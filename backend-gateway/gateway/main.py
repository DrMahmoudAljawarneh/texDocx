import os, time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from gateway.routes import jobs, admin

start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = None
    yield

app = FastAPI(title="texDocx", lifespan=lifespan)

app.mount("/ui", StaticFiles(directory=os.environ.get("FRONTEND_DIR", "/app/frontend"), html=True), name="ui")

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/health")
async def health():
    import redis.asyncio as aioredis
    issues = []
    redis_host = os.environ.get("REDIS_HOST", "redis")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    latexml_host = os.environ.get("LATEXML_HOST", "latexml")
    shared_dir = os.environ.get("SHARED_DIR", "/shared")
    try:
        r = aioredis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
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
