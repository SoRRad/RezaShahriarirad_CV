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
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import ALL_VALID_CAT_KEYS  # noqa: E402


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


def _strip_tags(markup):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", markup))).strip()


def _nav_labels(text):
    chunks = []
    for pattern in (
        r'<ul class=["\']nav-links["\'][^>]*>(.*?)</ul>',
        r'<div class=["\']mobile-menu["\'][^>]*>(.*?)</div>',
    ):
        chunks.extend(re.findall(pattern, text, flags=re.S))
    labels = []
    for chunk in chunks:
        labels.extend(_strip_tags(match) for match in re.findall(r"<a\b[^>]*>(.*?)</a>", chunk, flags=re.S))
    return [label for label in labels if label]


def _research_tags(text):
    grid_match = re.search(r'<div class=["\']research-grid["\'][^>]*>(.*?)</div>', text, flags=re.S)
    if not grid_match:
        return []
    return [
        (html.unescape(cat), _strip_tags(label))
        for cat, label in re.findall(
            r'data-cat=["\']([^"\']+)["\'][^>]*>(.*?)</span>',
            grid_match.group(1),
            flags=re.S,
        )
    ]


def _near_text(text, marker, before=900, after=650):
    idx = text.find(marker)
    if idx < 0:
        return ""
    return text[max(0, idx - before): idx + after]


def _has_logo_or_placeholder(text, marker, expected_initials):
    window = _near_text(text, marker)
    if not window:
        return False
    expected = html.escape(expected_initials, quote=True)
    has_img = bool(re.search(r'class=["\'][^"\']*(?:timeline-logo|lab-card-logo)(?:\s|["\'])', window))
    has_placeholder = (
        "logo-placeholder" in window
        and (expected in window or expected_initials in html.unescape(window))
    )
    return has_img or has_placeholder


def _button_tags_without_type(text):
    offenders = []
    for match in re.finditer(r"<button\b([^>]*)>", text, flags=re.I):
        attrs = match.group(1)
        if 'type=' in attrs.lower():
            continue
        if re.search(r'class=["\'][^"\']*(?:filter-btn|custom-dropdown-btn|pub-tag-chip|pres-tag-chip|btn-outline)[^"\']*["\']', attrs, flags=re.I):
            offenders.append(match.group(0)[:140])
    return offenders


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

    nav_labels = _nav_labels(text)
    if "Open Source" not in nav_labels:
        errors.append("Navigation label 'Open Source' is missing")
    if "Code" in nav_labels:
        errors.append("Navigation still uses 'Code' as a label")
    if "Hobbies" not in nav_labels:
        errors.append("Navigation label 'Hobbies' is missing")
    if "Interests" in nav_labels:
        errors.append("Navigation still uses 'Interests' as a label")

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
    if "location.hash" in text:
        errors.append("Filtering script should not update location.hash")
    if "window.scrollTo({top: y" not in text:
        errors.append("Filter script is missing defensive scroll preservation")
    button_offenders = _button_tags_without_type(text)
    if button_offenders:
        errors.append("Filter/button controls missing type=\"button\": " + "; ".join(button_offenders[:3]))

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

    open_source_checks = [
        ("MOSI System", "MOSI System is missing from the Open Source section"),
        ("https://github.com/SoRRad/MOSI-System", "MOSI GitHub link is missing"),
        ("https://sorrad.github.io/MOSI-System/", "MOSI webpage/demo link is missing"),
        ("SIRIS", "SIRIS is missing from the Open Source section"),
        ("https://github.com/SoRRad/SIRIS", "SIRIS GitHub link is missing"),
        ("https://siris-1029209978489.us-central1.run.app/", "SIRIS webpage/demo link is missing"),
        ("GitHub Profile", "GitHub Profile card is missing"),
        ("https://github.com/SoRRad", "GitHub Profile URL is missing"),
        ("Open-source code, models, and academic software projects", "Compact GitHub profile statement is missing"),
    ]
    for needle, message in open_source_checks:
        if needle not in text:
            errors.append(message)
    if "Open-source computational tools, machine learning models, and research software" in text:
        errors.append("Old Open Source paragraph wording is still present")
    if 'const openSourceRepos=[]' in text or 'const openSourceRepos = []' in text:
        errors.append("Open Source section has no repository data")

    research_tags = _research_tags(text)
    tag_labels = [label for _, label in research_tags]
    if not research_tags:
        errors.append("Ongoing Research tags are missing")
    if "Trauma & Burns" in tag_labels:
        errors.append("Trauma & Burns still appears in Ongoing Research tags")
    if "Surgical AI & Innovation" not in tag_labels:
        errors.append("Surgical AI & Innovation is missing from Ongoing Research tags")
    if "Bariatric Surgery" in tag_labels and "Orthopaedic Surgery" in tag_labels:
        if tag_labels.index("Orthopaedic Surgery") != tag_labels.index("Bariatric Surgery") + 1:
            errors.append("Orthopaedic Surgery should appear immediately after Bariatric Surgery")
    else:
        errors.append("Bariatric Surgery and Orthopaedic Surgery tags must both appear")
    invalid_data_cats = sorted({cat for cat, _ in research_tags if cat not in ALL_VALID_CAT_KEYS})
    rendered_html = text.split("<script>", 1)[0]
    invalid_data_cats.extend(
        sorted(
            {
                html.unescape(cat)
                for cat in re.findall(r'data-cat=["\']([^"\']+)["\']', rendered_html)
                if html.unescape(cat) not in ALL_VALID_CAT_KEYS
            }
        )
    )
    invalid_data_cats = sorted(set(invalid_data_cats))
    if invalid_data_cats:
        errors.append("Broken data-cat attributes: " + ", ".join(invalid_data_cats))

    for marker, initials, label in [
        ("Khatam-al-Anbiya Hospital", "KA", "Khatam-al-Anbiya Hospital"),
        ("National Organization for Development of Exceptional Talents (SAMPAD)", "SAMPAD", "High School Diploma / SAMPAD"),
        ("MStar Lab", "MSTAR", "MStar Lab"),
    ]:
        if not _has_logo_or_placeholder(text, marker, initials):
            errors.append(f"{label} entry is missing a real logo or initials placeholder")
    if re.search(r'<img\b[^>]*\bsrc=["\']\s*["\']', text):
        errors.append("Generated index.html contains an empty image src")

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
    meta_path = ROOT / "cv_pdf_build.json"
    if not meta_path.exists():
        errors.append("PDF build metadata cv_pdf_build.json is missing")
    else:
        try:
            pdf_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("PDF build metadata is not valid JSON")
            pdf_meta = {}
        if not pdf_meta.get("converted_from_docx") and pdf_meta.get("method") != "libreoffice-docx-to-pdf":
            errors.append("PDF build metadata does not confirm DOCX-to-PDF conversion")
        if pdf_meta.get("method") != "libreoffice-docx-to-pdf" and pdf_meta.get("preferred_method") != "libreoffice-docx-to-pdf":
            errors.append("PDF build metadata does not retain LibreOffice as the preferred conversion method")
        if pdf_meta.get("source") != "Shahriarirad_Reza_CV.docx" or pdf_meta.get("output") != "Shahriarirad_Reza_CV.pdf":
            errors.append("PDF build metadata source/output do not match the generated DOCX/PDF files")
    if 'href="Shahriarirad_Reza_CV.pdf"' not in text:
        errors.append("Website PDF download link is missing")
    if 'href="Shahriarirad_Reza_CV.docx"' in text or "Shahriarirad_Reza_CV.docx" in re.sub(r"cv_pdf_build\.json.*", "", text):
        errors.append("Website Word download link should not be visible on the public page")

    if errors:
        print("\n[SMOKE] FAILED:")
        for error in errors:
            print(f"  x {error}")
        return 1

    print("[SMOKE] PASSED: public page links to PDF only; DOCX remains generated in the repo, and JSON/PDF outputs, filters, tag chips, and lab logo markup passed checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
