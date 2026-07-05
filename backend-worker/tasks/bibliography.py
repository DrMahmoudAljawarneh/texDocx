import json
from pathlib import Path
from lxml import etree

BIBTYPE_TO_CSL = {
    "article": "article-journal",
    "book": "book",
    "inproceedings": "paper-conference",
    "proceedings": "book",
    "incollection": "chapter",
    "phdthesis": "thesis",
    "mastersthesis": "thesis",
    "techreport": "report",
    "manual": "report",
    "misc": "article",
    "unpublished": "manuscript",
}

def _bib_to_csl_json(entry):
    csl = {"id": None, "type": "article"}
    csl["type"] = BIBTYPE_TO_CSL.get(str(entry.type).lower(), "article")

    for field, value in entry.fields.items():
        f = str(field).lower()
        v = str(value) if not isinstance(value, (list, tuple)) else " and ".join(str(x) for x in value)
        if f == "title":
            csl["title"] = v
        elif f == "journal":
            csl["container-title"] = v
        elif f == "booktitle":
            csl["container-title"] = v
        elif f == "volume":
            csl["volume"] = v
        elif f == "number":
            csl["issue"] = v
        elif f == "pages":
            csl["page"] = v
        elif f == "publisher":
            csl["publisher"] = v
        elif f == "address":
            csl["publisher-place"] = [v]
        elif f == "year":
            try:
                csl["issued"] = {"date-parts": [[int(v)]]}
            except ValueError:
                csl["issued"] = {"date-parts": [[v]]}
        elif f == "month":
            csl.setdefault("issued", {}).setdefault("date-parts", [[]]).append(v)
        elif f == "doi":
            csl["DOI"] = v
        elif f == "isbn":
            csl["ISBN"] = v
        elif f == "issn":
            csl["ISSN"] = v
        elif f == "url":
            csl["URL"] = v
        elif f == "note":
            csl["note"] = v
        elif f == "abstract":
            csl["abstract"] = v
        elif f == "edition":
            csl["edition"] = v

    for role, persons in entry.persons.items():
        r = str(role).lower()
        if r not in ("author", "editor"):
            continue
        csl_list = []
        for person in persons:
            p = {}
            try:
                first = person.first()
                if first:
                    p["given"] = " ".join(first) if isinstance(first, (list, tuple)) else str(first)
            except Exception:
                pass
            try:
                last = person.last()
                if last:
                    p["family"] = " ".join(last) if isinstance(last, (list, tuple)) else str(last)
            except Exception:
                pass
            if p:
                csl_list.append(p)
        if csl_list:
            csl[r] = csl_list

    return csl


def parse_bibliography(task_id: str, xml_content: str, bib_files: list) -> str:
    from tasks.celery_app import publish_log

    if not bib_files:
        publish_log(task_id, "Info", "No .bib files found, skipping bibliography parsing")
        return xml_content

    root = etree.fromstring(xml_content.encode("utf-8"))
    ns = {"jats": "http://www.ncbi.nlm.nih.gov/JATS1"}
    job_dir = None
    csl_entries = []

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

                    csl_entry = _bib_to_csl_json(entry)
                    csl_entry["id"] = key
                    csl_entries.append(csl_entry)

                    parsed += 1
                except Exception as e:
                    publish_log(task_id, "Warning", f"Skipped bib entry '{key}': {e}")

            publish_log(task_id, "Info", f"Parsed {parsed}/{len(bib_data.entries)} bibliography entries")
        except Exception as e:
            publish_log(task_id, "Warning", f"Failed to parse {bib_path.name}: {e}")

    if csl_entries and bib_files:
        job_dir = bib_files[0].parent.parent
        refs_path = job_dir / "references.json"
        try:
            refs_path.write_text(json.dumps(csl_entries, indent=2), encoding="utf-8")
            publish_log(task_id, "Info", f"CSL-JSON saved to {refs_path} ({len(csl_entries)} entries)")
        except Exception as e:
            publish_log(task_id, "Warning", f"Failed to save CSL-JSON: {e}")

    return etree.tostring(root, encoding="unicode", pretty_print=True)
