from pathlib import Path
from lxml import etree

def pre_render_math(task_id: str, xml_content: str, job_dir: Path) -> str:
    from tasks.celery_app import publish_log
    from latex2mathml.converter import convert as latex2mathml_convert
    import ziamath as zm

    root = etree.fromstring(xml_content.encode("utf-8"))
    ns_latexml = "http://dlmf.nist.gov/LaTeXML"

    count = 0
    for math_elem in root.findall(f".//{{{ns_latexml}}}Math"):
        count += 1
        try:
            tex_str = math_elem.get("tex")
            if not tex_str:
                continue

            mathml_str = latex2mathml_convert(tex_str)
            mathml_elem = etree.fromstring(mathml_str.encode("utf-8"))

            eqn = zm.Math(mathml_str)
            svg_str = eqn.svg()
            svg_elem = etree.fromstring(svg_str.encode("utf-8"))

            parent = math_elem.getparent()
            if parent is not None:
                display = math_elem.get("mode") or math_elem.get("display") or "inline"
                alt = etree.Element("alternatives", display=display)
                idx = parent.index(math_elem)
                parent.insert(idx, alt)
                parent.remove(math_elem)
                alt.append(mathml_elem)
                alt.append(svg_elem)
        except Exception as e:
            publish_log(task_id, "Warning", f"MathML rendering failed for element {count}: {e}")

    publish_log(task_id, "Info", f"Processed {count} math elements")
    return etree.tostring(root, encoding="unicode", pretty_print=True)
