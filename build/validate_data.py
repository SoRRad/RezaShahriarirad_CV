"""
validate_data.py - validate CSV source files before generating CV outputs.
Run standalone: python build/validate_data.py
"""
import csv
import pathlib
import re
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import ALL_VALID_CAT_KEYS  # noqa: E402

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / "data"

REQUIRED_COLS = {
    "publications": ["n", "year", "type", "title", "authors", "journal"],
    "presentations": ["date", "type", "title", "venue", "location"],
    "profile": ["field", "value"],
    "experience": ["period", "role", "org"],
    "education": ["period", "degree", "org"],
    "awards": ["year", "title", "org"],
    "patents": ["date", "title", "issuer", "number"],
    "editorial": ["role", "journal", "period"],
    "references": ["name", "role", "inst"],
    "leadership": ["period", "title", "org", "desc"],
    "hobbies": ["name", "icon", "desc"],
    "journals": ["name"],
    "skills_computing": ["name", "level"],
    "skills_interpersonal": ["name"],
    "open_source": ["name", "language", "desc", "url"],
    "affiliations": ["org_key", "name", "role", "institution", "period"],
    "projects": [
        "project_name",
        "category",
        "collaborators",
        "irb_number",
        "short_description",
        "role",
        "status",
        "display_order",
        "public_visible",
    ],
}

REQUIRED_PROFILE_FIELDS = {
    "name",
    "title",
    "institution",
    "city_state",
    "bio_paragraph_1",
    "bio_paragraph_2",
    "email_professional",
    "scholar_url",
    "pubmed_url",
    "scopus_url",
    "researchgate_url",
    "wos_url",
    "linkedin_url",
    "orcid_url",
    "github_url",
    "h_index_cached",
    "citations_cached",
    "peer_reviews",
    "journals_reviewed",
    "manuscripts_reviewed",
    "metrics_last_updated",
}

VALID_PUB_TYPES = {"original", "review", "case", "letter"}
VALID_PRESENTATION_TYPES = {"poster", "oral"}
VALID_YES_NO = {"yes", "no", ""}
VALID_MONTHS = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", ""}
KEY_TEXT_FIELDS = {
    "publications": ["title", "authors", "journal"],
    "presentations": ["title", "venue", "location"],
    "profile": ["field", "value"],
    "affiliations": ["name", "role", "institution"],
    "projects": ["project_name", "short_description", "role", "status"],
}
HIDDEN_CHARS = {
    "\ufeff": "BOM",
    "\u200b": "zero-width space",
    "\u200c": "zero-width non-joiner",
    "\u200d": "zero-width joiner",
    "\u2060": "word joiner",
    "\u00a0": "non-breaking space",
}


def _read_csv_with_lines(path):
    data_lines = []
    line_numbers = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for lineno, line in enumerate(handle, start=1):
            if line.startswith("#"):
                continue
            data_lines.append(line)
            line_numbers.append(lineno)

    if not data_lines:
        return [], [], []

    reader = csv.DictReader(data_lines)
    rows = []
    row_lines = []
    for offset, row in enumerate(reader, start=1):
        rows.append(row)
        row_lines.append(line_numbers[offset] if offset < len(line_numbers) else offset + 1)
    return reader.fieldnames or [], rows, row_lines


def _split_semicolon(value):
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def _has_control_char(value):
    return any(ord(ch) < 32 and ch not in "\r\n" for ch in str(value))


def _text_issues(value):
    value = str(value or "")
    issues = []
    if value != value.strip():
        issues.append("leading/trailing whitespace")
    if "\t" in value:
        issues.append("tab character")
    if _has_control_char(value):
        issues.append("control character")
    for char, label in HIDDEN_CHARS.items():
        if char in value:
            issues.append(label)
    return issues


def _valid_year(value, min_year=1900, max_year=2035):
    value = str(value or "").strip()
    if not value:
        return True, None
    if not re.fullmatch(r"\d{4}", value):
        return False, "is not a four-digit year"
    year = int(value)
    if year < min_year or year > max_year:
        return False, f"is outside {min_year}-{max_year}"
    return True, None


def _validate_columns(stem, columns, errors):
    seen = Counter(columns)
    for col in columns:
        label = str(col or "")
        issues = _text_issues(label)
        if not label:
            errors.append(f"{stem}.csv: header contains an empty column name")
        if issues:
            errors.append(
                f"{stem}.csv: header '{label}' contains "
                + ", ".join(sorted(set(issues)))
            )
    for col, count in seen.items():
        if col and count > 1:
            errors.append(f"{stem}.csv: duplicate column '{col}'")

    required = REQUIRED_COLS.get(stem, [])
    missing = [col for col in required if col not in columns]
    for col in missing:
        errors.append(f"{stem}.csv: missing required column '{col}'")
    return not missing


def _validate_text_fields(stem, row, lineno, errors):
    fields = set(row.keys()) | set(KEY_TEXT_FIELDS.get(stem, []))
    for field in fields:
        if field is None or field not in row:
            continue
        issues = _text_issues(row.get(field, ""))
        if issues:
            errors.append(
                f"{stem}.csv: row {lineno} field '{field}' contains "
                + ", ".join(sorted(set(issues)))
            )


def _validate_url(stem, row, lineno, field, errors):
    url = str(row.get(field, "")).strip()
    if url and not (url.startswith("http://") or url.startswith("https://")):
        errors.append(f"{stem}.csv: row {lineno} field '{field}' must start with http:// or https://")


def _warn_file_encoding(path, warnings):
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        warnings.append(f"{path.name}: UTF-8 BOM detected and tolerated; build reads UTF-8-SIG")


def _validate_publications(rows, lines, errors):
    numbers = []
    for row, lineno in zip(rows, lines):
        n_raw = str(row.get("n", "")).strip()
        if not n_raw:
            errors.append(f"publications.csv: row {lineno} missing publication number")
        elif not n_raw.isdigit():
            errors.append(f"publications.csv: row {lineno} publication number '{n_raw}' is not numeric")
        else:
            numbers.append(int(n_raw))

        for field in ("title", "authors", "journal"):
            if not str(row.get(field, "")).strip():
                errors.append(f"publications.csv: row {lineno} missing required field '{field}'")

        ok, msg = _valid_year(row.get("year", ""))
        if not ok:
            errors.append(f"publications.csv: row {lineno} year '{row.get('year', '')}' {msg}")

        if "month" in row:
            month = str(row.get("month", "")).strip()
            if month not in VALID_MONTHS:
                errors.append(f"publications.csv: row {lineno} month '{month}' is not a valid three-letter month")

        type_s = str(row.get("type", "")).strip().lower()
        if type_s and type_s not in VALID_PUB_TYPES:
            errors.append(f"publications.csv: row {lineno} type '{type_s}' is not one of {sorted(VALID_PUB_TYPES)}")

        for field in ("cat", "highlight_topics"):
            for cat in _split_semicolon(row.get(field, "")):
                if cat not in ALL_VALID_CAT_KEYS:
                    errors.append(f"publications.csv: row {lineno} unknown {field} key '{cat}'")

        featured = str(row.get("featured", "")).strip().lower()
        if featured not in VALID_YES_NO:
            errors.append("publications.csv: row " f"{lineno} featured must be yes, no, or empty")

        _validate_url("publications", row, lineno, "url", errors)

    counts = Counter(numbers)
    for number in sorted(n for n, count in counts.items() if count > 1):
        errors.append(f"publications.csv: duplicate publication number {number}")


def _validate_presentations(rows, lines, errors):
    for row, lineno in zip(rows, lines):
        for field in ("title", "venue", "location"):
            if not str(row.get(field, "")).strip():
                errors.append(f"presentations.csv: row {lineno} missing required field '{field}'")

        ok, msg = _valid_year(row.get("year", ""))
        if not ok:
            errors.append(f"presentations.csv: row {lineno} year '{row.get('year', '')}' {msg}")

        month = str(row.get("month", "")).strip()
        if month not in VALID_MONTHS:
            errors.append(f"presentations.csv: row {lineno} month '{month}' is not a valid three-letter month")

        date_text = str(row.get("date", "")).strip()
        year_text = str(row.get("year", "")).strip()
        if year_text and date_text and year_text not in date_text:
            errors.append(f"presentations.csv: row {lineno} date '{date_text}' does not include year '{year_text}'")

        type_s = str(row.get("type", "")).strip().lower()
        if type_s and type_s not in VALID_PRESENTATION_TYPES:
            errors.append(
                f"presentations.csv: row {lineno} type '{type_s}' is not one of {sorted(VALID_PRESENTATION_TYPES)}"
            )

        for cat in _split_semicolon(row.get("cat", "")):
            if cat not in ALL_VALID_CAT_KEYS:
                errors.append(f"presentations.csv: row {lineno} unknown cat key '{cat}'")

        featured = str(row.get("featured", "")).strip().lower()
        if featured not in VALID_YES_NO:
            errors.append(f"presentations.csv: row {lineno} featured must be yes, no, or empty")


def _validate_profile(rows, lines, errors):
    profile = {}
    field_lines = {}
    for row, lineno in zip(rows, lines):
        field = str(row.get("field", "")).strip()
        value = str(row.get("value", "")).strip()
        if not field:
            errors.append(f"profile.csv: row {lineno} missing field name")
            continue
        profile[field] = value
        field_lines[field] = lineno

    for field in sorted(REQUIRED_PROFILE_FIELDS):
        if field not in profile:
            errors.append(f"profile.csv: missing required profile field '{field}'")
        elif not profile[field]:
            errors.append(f"profile.csv: row {field_lines[field]} field '{field}' cannot be empty")

    for field in ("scholar_url", "pubmed_url", "scopus_url", "researchgate_url", "wos_url", "linkedin_url", "orcid_url", "github_url"):
        if field in profile:
            fake_row = {field: profile[field]}
            _validate_url("profile", fake_row, field_lines.get(field, 0), field, errors)


def _validate_projects(rows, lines, errors):
    seen_orders = []
    for row, lineno in zip(rows, lines):
        for field in ("project_name", "short_description", "display_order", "public_visible"):
            if not str(row.get(field, "")).strip():
                errors.append(f"projects.csv: row {lineno} missing required field '{field}'")
        visible = str(row.get("public_visible", "")).strip().lower()
        if visible not in {"yes", "no"}:
            errors.append(f"projects.csv: row {lineno} public_visible must be yes or no")
        order = str(row.get("display_order", "")).strip()
        if order and not order.isdigit():
            errors.append(f"projects.csv: row {lineno} display_order must be numeric")
        elif order:
            seen_orders.append(int(order))

    counts = Counter(seen_orders)
    for order in sorted(o for o, count in counts.items() if count > 1):
        errors.append(f"projects.csv: duplicate display_order {order}")


def _validate_affiliations(rows, lines, errors):
    for row, lineno in zip(rows, lines):
        for field in ("org_key", "name"):
            if not str(row.get(field, "")).strip():
                errors.append(f"affiliations.csv: row {lineno} missing required field '{field}'")
        for field in ("show_in_experience", "hide_meta"):
            value = str(row.get(field, "")).strip().lower()
            if value not in VALID_YES_NO:
                errors.append(f"affiliations.csv: row {lineno} {field} must be yes, no, or empty")
        _validate_url("affiliations", row, lineno, "url", errors)


def _validate_open_source(rows, lines, errors):
    for row, lineno in zip(rows, lines):
        _validate_url("open_source", row, lineno, "url", errors)
        _validate_url("open_source", row, lineno, "demo", errors)
        _validate_url("open_source", row, lineno, "paper", errors)


LOGO_DIRS = [
    ROOT / "assets" / "logos",
    ROOT / "assets",
    ROOT / "images",
    ROOT / "img",
    ROOT / "public",
    ROOT / "static",
    ROOT / "build" / "static_assets" / "logos",
    ROOT / "build" / "static_assets",
]


def _check_logo_file_refs(rows, lines, stem, warnings):
    """Warn (not error) if logo_file value points to a non-existent asset."""
    for row, lineno in zip(rows, lines):
        logo_file = str(row.get("logo_file", "")).strip()
        if not logo_file:
            continue
        found = any((d / logo_file).exists() for d in LOGO_DIRS if d.exists())
        if not found:
            warnings.append(f"{stem}.csv: row {lineno} logo_file '{logo_file}' not found in any logo directory (will fall back to initials)")


def validate_all():
    errors = []
    warnings = []
    summaries = []

    for path in sorted(DATA.glob("*.csv")):
        stem = path.stem
        _warn_file_encoding(path, warnings)
        columns, rows, lines = _read_csv_with_lines(path)
        if not _validate_columns(stem, columns, errors):
            continue

        for row, lineno in zip(rows, lines):
            if None in row and row[None]:
                errors.append(
                    f"{stem}.csv: row {lineno} has extra column data; quote fields that contain commas"
                )
            if all(str(value or "").strip() == "" for value in row.values()):
                errors.append(f"{stem}.csv: row {lineno} is completely empty")
            _validate_text_fields(stem, row, lineno, errors)

        if stem == "publications":
            _validate_publications(rows, lines, errors)
        elif stem == "presentations":
            _validate_presentations(rows, lines, errors)
        elif stem == "profile":
            _validate_profile(rows, lines, errors)
        elif stem == "projects":
            _validate_projects(rows, lines, errors)
        elif stem == "affiliations":
            _validate_affiliations(rows, lines, errors)
        elif stem == "open_source":
            _validate_open_source(rows, lines, errors)

        if stem in ("experience", "education", "affiliations"):
            _check_logo_file_refs(rows, lines, stem, warnings)

        summaries.append((stem, len(rows)))

    if warnings:
        print(f"\n[VALIDATE] {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  ! {w}")

    if errors:
        print(f"\n[VALIDATE] FAILED: {len(errors)} error(s) found:\n")
        for error in errors:
            print(f"  x {error}")
        print()
        return len(errors)

    for stem, count in summaries:
        print(f"  ok {stem}.csv -- {count} rows")
    pub_count = next((count for stem, count in summaries if stem == "publications"), 0)
    print(f"\n[VALIDATE] PASSED: All checks passed. {pub_count} publications in data.")
    return 0


if __name__ == "__main__":
    sys.exit(1 if validate_all() else 0)
