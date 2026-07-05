import os, time, asyncio, shutil
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

import redis.asyncio as aioredis

from gateway.routes import jobs, admin

start_time = time.time()
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
SHARED_DIR = Path(os.environ.get("SHARED_DIR", "/shared"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = aioredis.ConnectionPool(
        host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, max_connections=20
    )
    app.state.redis = aioredis.Redis(connection_pool=pool)

    stale_threshold = 7200
    cleanup_interval = 600

    async def cleanup_loop():
        while True:
            await asyncio.sleep(cleanup_interval)
            try:
                now = time.time()
                for entry in os.scandir(str(SHARED_DIR)):
                    if entry.is_dir():
                        mtime = entry.stat().st_mtime
                        if now - mtime > stale_threshold:
                            has_job_key = await app.state.redis.exists(f"job:{entry.name}")
                            if not has_job_key:
                                shutil.rmtree(entry.path, ignore_errors=True)
            except Exception:
                pass

    task = asyncio.create_task(cleanup_loop())

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await pool.aclose()

app = FastAPI(title="texDocx", lifespan=lifespan)

app.mount("/ui", StaticFiles(directory=os.environ.get("FRONTEND_DIR", "/app/frontend"), html=True), name="ui")

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/health")
async def health():
    issues = []
    latexml_host = os.environ.get("LATEXML_HOST", "latexml")
    shared_dir = os.environ.get("SHARED_DIR", "/shared")
    try:
        await app.state.redis.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {e}"
        issues.append("redis")
    latexml_ports = os.environ.get("LATEXML_PORTS", "3334").split(",")
    latexml_status = "reachable"
    for port in latexml_ports[:1]:
        try:
            import socket
            s = socket.create_connection((latexml_host, int(port)), timeout=2)
            s.close()
        except Exception as e:
            latexml_status = f"unreachable on {port}: {e}"
            issues.append("latexml")
            break
    shared_path = Path(shared_dir)
    writable = os.access(str(shared_path), os.W_OK) if shared_path.exists() else False
    tmpfs_status = "writable" if writable else "missing or not writable"
    if not writable:
        issues.append("tmpfs")
    status_code = 200 if not issues else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if not issues else "degraded",
            "redis": redis_status,
            "latexmls": latexml_status,
            "tmpfs": tmpfs_status,
            "uptime_seconds": int(time.time() - start_time),
        },
    )

@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    frontend_dir = os.environ.get("FRONTEND_DIR", "/app/frontend")
    return FileResponse(os.path.join(frontend_dir, "index.html"))
