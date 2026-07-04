import os, json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter()

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

@router.get("/dlq")
async def list_dlq(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    import redis as sync_redis
    r = sync_redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    total = r.llen("dlq:failed_jobs")
    start = (page - 1) * per_page
    end = start + per_page - 1
    task_ids = r.lrange("dlq:failed_jobs", start, end)
    items = []
    for tid in task_ids:
        raw = r.get(f"dlq:{tid}")
        items.append({"task_id": tid, "payload": json.loads(raw) if raw else None})
    r.close()
    return {"total": total, "page": page, "per_page": per_page, "items": items}

@router.post("/dlq/{task_id}/retry")
async def retry_dlq(task_id: str):
    import redis as sync_redis
    import json
    r = sync_redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    raw = r.get(f"dlq:{task_id}")
    if not raw:
        r.close()
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    payload = json.loads(raw)
    r.lpush("celery", json.dumps(payload["original_payload"]))
    r.lrem("dlq:failed_jobs", 1, task_id)
    r.delete(f"dlq:{task_id}")
    r.close()
    return JSONResponse(content={"status": "retried", "task_id": task_id})
