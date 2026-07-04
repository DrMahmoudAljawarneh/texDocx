from pathlib import Path
from lxml import etree

def parse_bibliography(task_id: str, xml_content: str, bib_files: list) -> str:
    from tasks.celery_app import publish_log

    if not bib_files:
        publish_log(task_id, "Info", "No .bib files found, skipping bibliography parsing")
        return xml_content

    root = etree.fromstring(xml_content.encode("utf-8"))
    ns = {"jats": "http://www.ncbi.nlm.nih.gov/JATS1"}

    for bib_path in bib_files:
        publish_log(task_id, "Info", f"Processing bibliography: {bib_path.name}")
        try:
            from pybtex.database import parse_file
            bib_data = parse_file(str(bib_path))
            ref_list = etree.SubElement(root.find(".//jats:back", ns) or root, "ref-list")

            parsed = 0
            for key, entry in bib_data.entries.items():
                try:
                    ref = etree.SubElement(ref_list, "ref", id=f"ref-{key}")
                    ec = etree.SubElement(ref, "element-citation")
                    pub_type = str(entry.type) if entry.type else "other"
                    ec.set("publication-type", pub_type)

                    for field, value in entry.fields.items():
                        child = etree.SubElement(ec, str(field).lower())
                        if isinstance(value, (list, tuple)):
                            child.text = " and ".join(str(v) for v in value)
                        else:
                            child.text = str(value)

                    for role, persons in entry.persons.items():
                        for person in persons:
                            el = etree.SubElement(ec, str(role).lower())
                            name_el = etree.SubElement(el, "string-name")
                            try:
                                first = person.first()
                                if first:
                                    etree.SubElement(name_el, "given-names").text = str(" ".join(first) if not isinstance(first, str) else first)
                            except Exception:
                                pass
                            try:
                                last = person.last()
                                if last:
                                    etree.SubElement(name_el, "surname").text = str(" ".join(last) if not isinstance(last, str) else last)
                            except Exception:
                                pass

                    parsed += 1
                except Exception as e:
                    publish_log(task_id, "Warning", f"Skipped bib entry '{key}': {e}")

            publish_log(task_id, "Info", f"Parsed {parsed}/{len(bib_data.entries)} bibliography entries")
        except Exception as e:
            publish_log(task_id, "Warning", f"Failed to parse {bib_path.name}: {e}")

    return etree.tostring(root, encoding="unicode", pretty_print=True)
