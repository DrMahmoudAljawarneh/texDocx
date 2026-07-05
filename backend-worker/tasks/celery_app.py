import os, json, time, traceback, subprocess, zipfile, shutil
from pathlib import Path
from celery import Celery
import redis as sync_redis

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
LATEXML_HOST = os.environ.get("LATEXML_HOST", "latexml")
LATEXML_PORTS = os.environ.get("LATEXML_PORTS", "3334").split(",")
SHARED_DIR = Path(os.environ.get("SHARED_DIR", "/shared"))

app = Celery("texdocx", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0", backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_soft_time_limit=600,
    task_time_limit=660,
)

_redis_pool = None

def _get_redis():
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = sync_redis.ConnectionPool(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, max_connections=10
        )
    return sync_redis.Redis(connection_pool=_redis_pool)

def publish_log(task_id, severity, message, line_number=None):
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "severity": severity,
        "message": message,
    }
    if line_number:
        entry["line_number"] = line_number
    try:
        r = _get_redis()
        r.publish(f"log:{task_id}", json.dumps(entry))
        r.append(f"log:{task_id}", json.dumps(entry) + "\n")
        r.expire(f"log:{task_id}", 3600)
    except Exception:
        pass

def update_status(task_id, status, progress=None):
    try:
        r = _get_redis()
        mapping = {"status": status, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        if progress is not None:
            mapping["progress_percent"] = str(progress)
        r.hset(f"job:{task_id}", mapping=mapping)
    except Exception:
        pass

@app.task(bind=True, name="convert")
def convert(self, payload):
    task_id = payload["task_id"]
    fmt = payload["format"]
    macros = payload.get("macros", "")
    citation_style = payload.get("citation_style", "ieee")
    algorithm_render = payload.get("algorithm_render", "text")
    template_path_str = payload.get("template_path")
    job_dir = Path(payload["job_dir"])
    zip_path = Path(payload["zip_path"])

    publish_log(task_id, "Info", f"Starting conversion for task {task_id}")
    update_status(task_id, "PROCESSING", 0)

    try:
        extract_dir = job_dir / "source"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            zf.extractall(str(extract_dir))
        publish_log(task_id, "Info", f"Extracted source to {extract_dir}")

        tex_files = list(extract_dir.rglob("*.tex"))
        if not tex_files:
            raise ValueError("No .tex files found in archive")
        main_tex = tex_files[0]
        publish_log(task_id, "Info", f"Found main TeX file: {main_tex.name}")

        if algorithm_render == "image":
            try:
                import re
                tex_content = main_tex.read_text(encoding="utf-8", errors="replace")
                algo_count = 0
                for m in re.finditer(r'\\begin\{(algorithm|algorithm\*)\}(.*?)\\end\{(algorithm|algorithm\*)\}', tex_content, re.DOTALL):
                    snippet = m.group(0)
                    (job_dir / f"algo_{algo_count}.tex").write_text(snippet, encoding="utf-8")
                    algo_count += 1
                publish_log(task_id, "Info", f"Extracted {algo_count} algorithm environments for image rendering")
            except Exception as e:
                publish_log(task_id, "Warning", f"Failed to extract algorithm snippets: {e}")

        update_status(task_id, "PROCESSING", 10)
        from tasks.images import convert_vector_assets
        convert_vector_assets(task_id, extract_dir)
        publish_log(task_id, "Info", "Vector assets converted")

        update_status(task_id, "PROCESSING", 30)
        from tasks.compiler import compile_latex
        raw_xml = compile_latex(task_id, main_tex, macros)
        publish_log(task_id, "Info", "LaTeX compiled to XML")

        update_status(task_id, "PROCESSING", 50)
        bib_files = list(extract_dir.rglob("*.bib"))
        from tasks.bibliography import parse_bibliography
        xml_with_bib = parse_bibliography(task_id, raw_xml, bib_files)
        publish_log(task_id, "Info", "Bibliography parsed")

        update_status(task_id, "PROCESSING", 65)
        from tasks.math import pre_render_math
        final_xml = pre_render_math(task_id, xml_with_bib, job_dir)
        publish_log(task_id, "Info", "MathML pre-rendered")

        xml_path = job_dir / "output.xml"
        xml_path.write_text(final_xml, encoding="utf-8")
        publish_log(task_id, "Info", f"XML output written to {xml_path}")

        if fmt in ("docx", "all"):
            update_status(task_id, "PROCESSING", 80)
            from tasks.docxgen import generate_docx
            docx_path = job_dir / "output.docx"
            template_path = Path(template_path_str) if template_path_str else None
            generate_docx(task_id, final_xml, docx_path, citation_style, algorithm_render, asset_dir=extract_dir, template_path=template_path)
            publish_log(task_id, "Info", "DOCX generated")
        else:
            publish_log(task_id, "Info", "Skipping DOCX generation (xml-only mode)")

        update_status(task_id, "SUCCESS", 100)
        publish_log(task_id, "Info", "Conversion complete")
        publish_log(task_id, "Complete", "Job finished successfully",
                    line_number=None)

        r = _get_redis()
        r.publish(f"log:{task_id}", json.dumps({"event": "complete", "status": "SUCCESS"}))

    except Exception as e:
        tb = traceback.format_exc()
        publish_log(task_id, "Fatal", f"Conversion failed: {e}")
        publish_log(task_id, "Fatal", tb)
        update_status(task_id, "FAILURE", 0)

        r = _get_redis()
        r.publish(f"log:{task_id}", json.dumps({"event": "complete", "status": "FAILURE"}))

        dlq_payload = json.dumps({
            "original_payload": payload,
            "error": str(e),
            "traceback": tb,
            "failed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        r = _get_redis()
        r.set(f"dlq:{task_id}", dlq_payload)
        r.expire(f"dlq:{task_id}", 86400)
        r.lpush("dlq:failed_jobs", task_id)

        raise
    finally:
        if zip_path.exists():
            try:
                zip_path.unlink()
            except Exception:
                pass
        extract_dir = job_dir / "source"
        if extract_dir.exists():
            shutil.rmtree(str(extract_dir), ignore_errors=True)
