import os, json, uuid, asyncio, time
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from celery import Celery

router = APIRouter()

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
SHARED_DIR = Path(os.environ.get("SHARED_DIR", "/shared"))
MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".tex", ".zip"}

celery_app = Celery("texdocx", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

def _validate_file(filename: str, content_length: int):
    if content_length > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Allowed: .tex, .zip")

@router.post("/submit")
async def submit_job(
    request: Request,
    file: UploadFile = File(...),
    format: str = Form("all"),
    macros: str = Form(None),
):
    if format not in ("all", "xml", "docx"):
        raise HTTPException(status_code=400, detail="Invalid format. Must be 'all', 'xml', or 'docx'")

    content = await file.read()
    _validate_file(file.filename or "input.zip", len(content))

    task_id = str(uuid.uuid4())
    job_dir = SHARED_DIR / task_id
    job_dir.mkdir(parents=True, exist_ok=True)
    zip_path = job_dir / "input.zip"
    zip_path.write_bytes(content)

    await request.app.state.redis.hset(f"job:{task_id}", mapping={
        "status": "PENDING",
        "progress_percent": "0",
        "format": format,
        "filename": file.filename or "",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    await request.app.state.redis.expire(f"job:{task_id}", 3600)

    payload = {
        "task_id": task_id,
        "format": format,
        "macros": macros or "",
        "zip_path": str(zip_path),
        "job_dir": str(job_dir),
    }
    await asyncio.to_thread(celery_app.send_task, "convert", kwargs={"payload": payload})

    return JSONResponse(
        status_code=202,
        content={
            "task_id": task_id,
            "status": "PENDING",
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    )

@router.get("/{task_id}/status")
async def get_status(request: Request, task_id: str):
    data = await request.app.state.redis.hgetall(f"job:{task_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "task_id": task_id,
        "status": data.get("status", "UNKNOWN"),
        "progress_percent": int(data.get("progress_percent", 0)),
        "updated_at": data.get("updated_at", ""),
    }

@router.head("/{task_id}/logs")
@router.get("/{task_id}/logs")
async def get_logs(request: Request, task_id: str):
    raw = await request.app.state.redis.get(f"log:{task_id}")
    log_file = SHARED_DIR / task_id / "output.log"
    if log_file.exists():
        text = log_file.read_text()
    else:
        text = raw or ""
    return {"task_id": task_id, "logs": text}

@router.get("/{task_id}/logs/stream")
async def stream_logs(request: Request, task_id: str):
    async def event_generator():
        pubsub = request.app.state.redis.pubsub()
        await pubsub.subscribe(f"log:{task_id}")

        yield "event: connected\ndata: {}\n\n"

        timeout = 300
        start = asyncio.get_event_loop().time()
        try:
            while True:
                elapsed = asyncio.get_event_loop().time() - start
                if elapsed > timeout:
                    break
                try:
                    msg = await asyncio.wait_for(pubsub.get_message(timeout=None), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                if msg and msg["type"] == "message":
                    data = msg["data"]
                    try:
                        parsed = json.loads(data)
                        if parsed.get("event") == "complete":
                            status = parsed.get("status", "SUCCESS")
                            yield f"event: complete\ndata: {json.dumps({'task_id': task_id, 'status': status})}\n\n"
                            break
                        else:
                            yield f"event: log\ndata: {data}\n\n"
                    except Exception:
                        yield f"event: log\ndata: {data}\n\n"
        finally:
            await pubsub.unsubscribe(f"log:{task_id}")
            await pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.head("/{task_id}/output/{fmt}")
@router.get("/{task_id}/output/{fmt}")
async def get_output(task_id: str, fmt: str):
    if fmt not in ("xml", "docx"):
        raise HTTPException(status_code=400, detail="Format must be 'xml' or 'docx'")
    ext = fmt
    fpath = SHARED_DIR / task_id / f"output.{ext}"
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="Output not found")
    media = "application/xml" if ext == "xml" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(str(fpath), media_type=media, filename=f"output.{ext}")
