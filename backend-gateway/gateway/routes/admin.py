import os, json, asyncio

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from celery import Celery

router = APIRouter()

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

celery_app = Celery("texdocx", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

@router.get("/dlq")
async def list_dlq(request: Request, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    total = await request.app.state.redis.llen("dlq:failed_jobs")
    start = (page - 1) * per_page
    end = start + per_page - 1
    task_ids = await request.app.state.redis.lrange("dlq:failed_jobs", start, end)
    items = []
    for tid in task_ids:
        raw = await request.app.state.redis.get(f"dlq:{tid}")
        items.append({"task_id": tid, "payload": json.loads(raw) if raw else None})
    return {"total": total, "page": page, "per_page": per_page, "items": items}

@router.post("/dlq/{task_id}/retry")
async def retry_dlq(request: Request, task_id: str):
    raw = await request.app.state.redis.get(f"dlq:{task_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    payload = json.loads(raw)

    await asyncio.to_thread(
        celery_app.send_task, "convert", kwargs={"payload": payload["original_payload"]}
    )

    await request.app.state.redis.lrem("dlq:failed_jobs", 1, task_id)
    await request.app.state.redis.delete(f"dlq:{task_id}")
    return JSONResponse(content={"status": "retried", "task_id": task_id})
