import subprocess
from pathlib import Path

def convert_vector_assets(task_id: str, extract_dir: Path):
    from tasks.celery_app import publish_log

    for ext in ("*.eps", "*.pdf"):
        for fpath in extract_dir.rglob(ext):
            if fpath.stat().st_size == 0:
                continue
            out_png = fpath.with_suffix(".png")
            out_svg = fpath.with_suffix(".svg")
            try:
                subprocess.run(
                    ["magick", str(fpath), "-density", "150", str(out_png)],
                    capture_output=True, timeout=30, check=True,
                )
                publish_log(task_id, "Info", f"Converted {fpath.name} -> {out_png.name}")
            except Exception as e:
                publish_log(task_id, "Warning", f"Failed to convert {fpath.name} to PNG: {e}")
            try:
                subprocess.run(
                    ["magick", str(fpath), str(out_svg)],
                    capture_output=True, timeout=30, check=True,
                )
            except Exception:
                pass
