"""
smoke_test.py - post-build checks for the generated public CV site.
Run standalone: python build/smoke_test.py
"""
import csv
import html
import json
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / "data"
INDEX = ROOT / "index.html"


def _read_csv_rows(path):
    lines = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.startswith("#"):
                lines.append(line)
    return list(csv.DictReader(lines))


def _contains_title(text, title):
    if not title:
        return False
    variants = {
        title,
        html.escape(title, quote=True),
        title.replace("&", "&amp;"),
    }
    return any(variant in text for variant in variants)


def _section_exists(text, section_id):
    return re.search(rf'id=["\']{re.escape(section_id)}["\']', text) is not None


def _missing_nav_targets(text):
    ids = set(re.findall(r'id=["\']([^"\']+)["\']', text))
    anchors = set(re.findall(r'href=["\']#([^"\']+)["\']', text))
    ignored = {"", "top"}
    return sorted(anchor for anchor in anchors if anchor not in ids and anchor not in ignored)


def _json_contains_title(path, title):
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return title in json.dumps(payload, ensure_ascii=False)


def _json_length(path):
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return len(payload) if isinstance(payload, list) else None


def _docx_text(path):
    if not path.exists():
        return ""
    with zipfile.ZipFile(path) as docx:
        xml = docx.read("word/document.xml").decode("utf-8", errors="ignore")
    xml = re.sub(r"<[^>]+>", " ", xml)
    return html.unescape(re.sub(r"\s+", " ", xml))


def main():
    errors = []

    if not INDEX.exists():
        errors.append("index.html does not exist")
        text = ""
    else:
        text = INDEX.read_text(encoding="utf-8")

    pub_rows = _read_csv_rows(DATA / "publications.csv")
    if not pub_rows:
        errors.append("data/publications.csv has no publication rows")
        last_pub = {}
    else:
        last_pub = pub_rows[-1]

    last_n = str(last_pub.get("n", "")).strip()
    last_title = str(last_pub.get("title", "")).strip()
    print(f"[SMOKE] Publications rows: {len(pub_rows)}")
    print(f"[SMOKE] Last publication: #{last_n} {last_title}")

    if last_title and not _contains_title(text, last_title):
        errors.append(f"index.html does not contain newest publication title: {last_title}")

    for section_id in ("about", "experience", "publications", "presentations", "references"):
        if not _section_exists(text, section_id):
            errors.append(f"index.html missing section id '{section_id}'")

    for element_id in (
        "pub-list",
        "pub-count",
        "pub-search",
        "pub-more",
        "pub-type-btn",
        "pub-type-panel",
        "pub-auth-btn",
        "pub-auth-panel",
        "cat-all-btn",
        "pres-list",
        "pres-count",
        "pres-search",
        "pres-more",
        "pres-type-btn",
        "pres-type-panel",
        "pres-loc-btn",
        "pres-loc-panel",
        "pres-reset",
    ):
        if not _section_exists(text, element_id):
            errors.append(f"index.html missing generated element id '{element_id}'")

    if "Metrics last updated" in text:
        errors.append("Visible 'Metrics last updated' text is present in index.html")

    missing_nav = _missing_nav_targets(text)
    if missing_nav:
        errors.append("Broken nav anchors: " + ", ".join(missing_nav))

    if not _json_contains_title(ROOT / "cv_pubs.json", last_title):
        errors.append("cv_pubs.json does not contain newest publication title")
    pubs_json_count = _json_length(ROOT / "cv_pubs.json")
    if pubs_json_count != len(pub_rows):
        errors.append(f"cv_pubs.json has {pubs_json_count} publications; expected {len(pub_rows)}")

    if '"n": ' not in text and '"n":' not in text:
        errors.append("index.html does not appear to include the generated publications JavaScript array")
    if f'"n": {last_n}' not in text and f'"n":{last_n}' not in text:
        errors.append(f"index.html does not include newest publication number {last_n}")
    if "pub-tag-chip" not in text:
        errors.append("index.html is missing publication tag chip markup/class")
    if "pres-tag-chip" not in text:
        errors.append("index.html is missing presentation tag chip markup/class")
    if "window.cvDiagnostics" not in text or "window.testPubFilters" not in text or "window.testPresFilters" not in text:
        errors.append("browser diagnostics/test functions are missing")

    phone_rows = _read_csv_rows(DATA / "profile.csv")
    profile = {row.get("field", ""): row.get("value", "") for row in phone_rows}
    phone = str(profile.get("phone", "")).strip()
    if phone and phone in text:
        errors.append("Phone number is present in generated index.html")
    for email in ("Shahriarirad.reza@mayo.edu", "r.shahriari1995@gmail.com"):
        user, domain = email.split("@")
        if email not in text and (f'data-u="{html.escape(user)}"' not in text or f'data-d="{html.escape(domain)}"' not in text):
            errors.append(f"Generated index.html does not include public email {email}")

    tavs_logo_expected = (ROOT / "assets" / "logos" / "tavs.png").exists()
    if tavs_logo_expected:
        if "Thoracic and Vascular Surgery Research Center logo" not in text or "lab-card-logo" not in text:
            errors.append("TAVS logo asset exists but generated lab-card logo markup is missing")
        else:
            print("[SMOKE] TAVS logo markup found.")
    else:
        print("[SMOKE] TAVS logo asset not found; fallback initials are expected.")

    row_195 = next((row for row in pub_rows if str(row.get("n", "")).strip() == "195"), None)
    if row_195:
        row_195_title = str(row_195.get("title", "")).strip()
        if not _contains_title(text, row_195_title):
            errors.append("Publication row 195 is present in CSV but its title was not found in index.html")
        else:
            print("[SMOKE] Row 195 appears in index.html.")

    docx_path = ROOT / "Shahriarirad_Reza_CV.docx"
    pdf_path = ROOT / "Shahriarirad_Reza_CV.pdf"
    if not docx_path.exists() or docx_path.stat().st_size == 0:
        errors.append("Shahriarirad_Reza_CV.docx was not generated")
    else:
        doc_text = _docx_text(docx_path)
        if phone and phone in doc_text:
            errors.append("Phone number is present in generated DOCX")
        for email in ("Shahriarirad.reza@mayo.edu", "r.shahriari1995@gmail.com"):
            if email not in doc_text:
                errors.append(f"Generated DOCX does not include public email {email}")
        if str(len(pub_rows)) not in doc_text:
            errors.append("Generated DOCX does not include the current publication count")
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        errors.append("Shahriarirad_Reza_CV.pdf was not generated")
    if 'href="Shahriarirad_Reza_CV.pdf"' not in text:
        errors.append("Website PDF download link is missing")
    if 'href="Shahriarirad_Reza_CV.docx"' not in text:
        errors.append("Website Word download link is missing")

    if errors:
        print("\n[SMOKE] FAILED:")
        for error in errors:
            print(f"  x {error}")
        return 1

    print("[SMOKE] PASSED: generated site, JSON, DOCX/PDF outputs, filters, tag chips, and lab logo markup passed checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
