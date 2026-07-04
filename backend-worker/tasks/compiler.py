import os, random, json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

LATEXML_HOST = os.environ.get("LATEXML_HOST", "latexml")
LATEXML_PORTS = os.environ.get("LATEXML_PORTS", "3334").split(",")

def _pick_daemon_url():
    port = random.choice(LATEXML_PORTS)
    return f"http://{LATEXML_HOST}:{port}/"

def compile_latex(task_id, tex_path: Path, macros: str) -> str:
    from tasks.celery_app import publish_log

    publish_log(task_id, "Info", f"Compiling {tex_path.name} via latexmls daemon")
    tex_content = tex_path.read_text(encoding="utf-8")

    if macros:
        tex_content = macros + "\n" + tex_content
        publish_log(task_id, "Info", "Injected custom macros")

    url = _pick_daemon_url()
    data = urlencode({"source": tex_content}).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urlopen(req, timeout=120) as resp:
            raw_xml = resp.read().decode("utf-8")
    except Exception as e:
        publish_log(task_id, "Error", f"latexmls request failed: {e}")
        raise RuntimeError(f"LaTeXML compilation failed: {e}")

    publish_log(task_id, "Info", f"Compilation produced {len(raw_xml)} chars of XML")
    return raw_xml
