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
from utils import ALL_VALID_CAT_KEYS, TOP_LEVEL_CAT_KEYS, VALID_AUTHOR_TAGS  # noqa: E402

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
    "skills_research": ["name"],
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
    "cv_summary",
    "work_mayo_clinic_1",
    "work_mayo_clinic_2",
    "work_mayo_clinic_3",
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
DISALLOWED_KEYWORD_ALIASES = {
    "dm": "Diabetes",
    "robotic": "Robotic surgery",
    "robitic": "Robotic surgery",
    "mis": "Minimally invasive surgery",
}
KEYWORD_NORMALIZATION_ALIASES = {
    **DISALLOWED_KEYWORD_ALIASES,
    "robotics": "Robotic surgery",
    "robotic surgery": "Robotic surgery",
    "covid": "COVID-19",
    "covid-19": "COVID-19",
    "gi surgery": "Gastrointestinal surgery",
    "gastrointestinal surgery": "Gastrointestinal surgery",
    "orthopedics": "Orthopaedic surgery",
    "orthopaedic surgery": "Orthopaedic surgery",
    "bariatric": "Bariatric surgery",
    "bariatric surgery": "Bariatric surgery",
}
EXPECTED_PUBLICATION_HEADER = [
    "n",
    "year",
    "type",
    "tags",
    "cat",
    "title",
    "authors",
    "journal",
    "url",
    "keywords",
    "highlight_topics",
    "featured",
]
KEY_TEXT_FIELDS = {
    "publications": ["title", "authors", "journal"],
    "presentations": ["title", "venue", "location"],
    "profile": ["field", "value"],
    "affiliations": ["name", "role", "institution"],
    "projects": ["project_name", "short_description", "role", "status"],
    "skills_research": ["name"],
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


def _raw_csv_shape_checks(path, stem, errors):
    data_lines = []
    line_numbers = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for lineno, line in enumerate(handle, start=1):
            if line.startswith("#"):
                if stem == "publications" and line.rstrip("\r\n").rstrip().endswith(","):
                    errors.append(
                        f"{stem}.csv: line {lineno} comment/header guide ends with a trailing comma"
                    )
                continue
            if line.strip():
                data_lines.append(line)
                line_numbers.append(lineno)

    if not data_lines:
        return

    header_line = data_lines[0].rstrip("\r\n")
    if header_line.rstrip().endswith(","):
        errors.append(f"{stem}.csv: header row ends with a trailing comma")

    rows = list(csv.reader(data_lines))
    if not rows:
        return

    header = [col.strip().lstrip("\ufeff") for col in rows[0]]
    expected_count = len(header)
    if stem == "publications" and header != EXPECTED_PUBLICATION_HEADER:
        errors.append(
            "publications.csv: header must be exactly "
            + ",".join(EXPECTED_PUBLICATION_HEADER)
        )
        expected_count = len(EXPECTED_PUBLICATION_HEADER)

    for offset, row in enumerate(rows[1:], start=1):
        lineno = line_numbers[offset] if offset < len(line_numbers) else offset + 1
        if len(row) != expected_count:
            errors.append(
                f"{stem}.csv: row {lineno} has {len(row)} columns; expected {expected_count}. "
                "Quote fields that contain commas and remove stray trailing commas."
            )


def _split_semicolon(value):
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def _raw_semicolon_parts(value):
    return [item.strip() for item in str(value or "").split(";")]


def _validate_semicolon_field(stem, row, lineno, field, errors, valid_values=None):
    raw = str(row.get(field, "") or "")
    if not raw:
        return []
    parts = _raw_semicolon_parts(raw)
    values = [part for part in parts if part]
    if raw.strip().endswith(";"):
        errors.append(f"{stem}.csv: row {lineno} field '{field}' has a trailing semicolon")
    if any(part == "" for part in parts[1:-1]):
        errors.append(f"{stem}.csv: row {lineno} field '{field}' has an empty semicolon item")
    if "," in raw and field in {"tags", "cat", "highlight_topics", "keywords"}:
        errors.append(f"{stem}.csv: row {lineno} field '{field}' should use semicolons, not commas")
    if valid_values is not None:
        for value in values:
            if value in TOP_LEVEL_CAT_KEYS and field in {"cat", "highlight_topics"}:
                errors.append(
                    f"{stem}.csv: row {lineno} field '{field}' uses top-level category '{value}'; "
                    "use a subcategory key instead"
                )
            elif value not in valid_values:
                errors.append(f"{stem}.csv: row {lineno} unknown {field} key '{value}'")
    return values


def _validate_keyword_field(stem, row, lineno, errors):
    values = _validate_semicolon_field(stem, row, lineno, "keywords", errors)
    normalized_seen = {}
    for value in values:
        key = value.casefold()
        if key in DISALLOWED_KEYWORD_ALIASES:
            errors.append(
                f"{stem}.csv: row {lineno} keyword '{value}' should be "
                f"'{DISALLOWED_KEYWORD_ALIASES[key]}'"
            )
        normalized_key = KEYWORD_NORMALIZATION_ALIASES.get(key, value).casefold()
        if normalized_key in normalized_seen:
            errors.append(
                f"{stem}.csv: row {lineno} has duplicate/near-duplicate keywords "
                f"'{normalized_seen[normalized_key]}' and '{value}'"
            )
        normalized_seen[normalized_key] = value


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
        shifted_featured = str(row.get("", "") or "").strip().lower()
        featured = str(row.get("featured", "") or "").strip().lower()
        if shifted_featured:
            if shifted_featured in VALID_YES_NO and not featured:
                errors.append(
                    f"publications.csv: row {lineno} featured value appears shifted into an unnamed column"
                )
            else:
                errors.append(
                    f"publications.csv: row {lineno} has unexpected data in an unnamed column"
                )

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

        _validate_semicolon_field("publications", row, lineno, "tags", errors, VALID_AUTHOR_TAGS)
        _validate_semicolon_field("publications", row, lineno, "cat", errors, ALL_VALID_CAT_KEYS)
        _validate_keyword_field("publications", row, lineno, errors)
        _validate_semicolon_field("publications", row, lineno, "highlight_topics", errors, ALL_VALID_CAT_KEYS)

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

        _validate_semicolon_field("presentations", row, lineno, "cat", errors, ALL_VALID_CAT_KEYS)
        _validate_keyword_field("presentations", row, lineno, errors)

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


def _logo_or_placeholder(row):
    logo_file = str(row.get("logo_file", "")).strip()
    if logo_file and any((d / logo_file).exists() for d in LOGO_DIRS if d.exists()):
        return True
    return bool(str(row.get("logo_initials", "")).strip())


def _int_field(profile, field, errors):
    value = str(profile.get(field, "")).strip().replace(",", "")
    try:
        return int(value)
    except ValueError:
        errors.append(f"profile.csv: field '{field}' must be numeric")
        return None


def _require_row(rows, predicate, label, errors):
    row = next((row for row in rows if predicate(row)), None)
    if row is None:
        errors.append(label)
    return row


def _validate_requested_cv_content(rows_by_stem, errors):
    profile_rows = rows_by_stem.get("profile", [])
    profile = {row.get("field", ""): row.get("value", "") for row in profile_rows}
    pub_rows = rows_by_stem.get("publications", [])

    # Metric floors (no-downgrade), not exact pins. Google Scholar numbers only
    # grow; the Actions refresh and smoke test enforce the same floors, so a
    # successful metric refresh must never fail the build. Bump a floor here
    # only when a genuinely higher value has been verified and committed.
    for field, floor in (
        ("citations_cached", 3428),
        ("h_index_cached", 24),
        ("peer_reviews", 149),
        ("journals_reviewed", 67),
    ):
        value = _int_field(profile, field, errors)
        if value is not None and value < floor:
            errors.append(f"profile.csv: {field} must not be downgraded below {floor}")
    pub_count = _int_field(profile, "pub_count", errors) if "pub_count" in profile else None
    if pub_count is not None and pub_count != len(pub_rows):
        errors.append(f"profile.csv: pub_count is {pub_count}; expected {len(pub_rows)} from publications.csv")

    for field in ("email_professional", "email_personal"):
        if not str(profile.get(field, "")).strip():
            errors.append(f"profile.csv: missing public email field '{field}'")
    for field in ("email_professional_public_visible", "email_personal_public_visible"):
        if str(profile.get(field, "")).strip().lower() != "yes":
            errors.append(f"profile.csv: {field} must be yes so both emails appear")

    exp_rows = rows_by_stem.get("experience", [])
    astar_row = _require_row(
        exp_rows,
        lambda row: "a-star lab" in f"{row.get('role','')} {row.get('org','')}".casefold(),
        "experience.csv: missing Research Fellow - A-Star Lab row",
        errors,
    )
    if astar_row and not _logo_or_placeholder(astar_row):
        errors.append("experience.csv: A-Star Lab row needs either a logo_file or logo_initials placeholder")
    trainee_row = _require_row(
        exp_rows,
        lambda row: "research trainee" in str(row.get("role", "")).casefold()
        and "student research committee" in str(row.get("role", "")).casefold(),
        "experience.csv: missing Research Trainee - Student Research Committee row",
        errors,
    )
    if trainee_row:
        if not str(trainee_row.get("desc", "")).strip():
            errors.append("experience.csv: Research Trainee row needs a concise description")
        if not _logo_or_placeholder(trainee_row):
            errors.append("experience.csv: Research Trainee row needs either a logo_file or logo_initials placeholder")

    # Structural check rather than exact-title pins: titles are edited over time
    # (e.g. "Mayo Fellow Association" -> "Mayo Research Fellows' Association"), so
    # assert the leadership section stays populated rather than freezing wording.
    leadership_rows = rows_by_stem.get("leadership", [])
    if len(leadership_rows) < 5:
        errors.append(
            f"leadership.csv: expected at least 5 leadership/service items, found {len(leadership_rows)}"
        )

    tech_rows = rows_by_stem.get("skills_computing", [])
    tech_names = {str(row.get("name", "")).casefold(): row for row in tech_rows}
    for name in ("SPSS", "EndNote", "Microsoft Office", "Corel Video Studio", "Python"):
        if name.casefold() not in tech_names:
            errors.append(f"skills_computing.csv: missing skill '{name}'")
    python_row = tech_names.get("python")
    if python_row and str(python_row.get("level", "")).strip().casefold() not in {"beginner", "basic proficiency"}:
        errors.append("skills_computing.csv: Python level must remain Beginner or Basic proficiency")

    research_names = {str(row.get("name", "")).casefold() for row in rows_by_stem.get("skills_research", [])}
    for name in (
        "Study design",
        "RCT coordination",
        "Data management",
        "Statistical analysis",
        "Systematic review and meta-analysis",
        "Clinical research coordination",
        "IRB preparation",
    ):
        if name.casefold() not in research_names:
            errors.append(f"skills_research.csv: missing skill '{name}'")

    interpersonal_names = {str(row.get("name", "")).casefold() for row in rows_by_stem.get("skills_interpersonal", [])}
    for name in (
        "Scientific editing",
        "Presentation skills",
        "Mentoring",
        "Time management",
        "Multidisciplinary collaboration",
        "English and Farsi fluency",
    ):
        if name.casefold() not in interpersonal_names:
            errors.append(f"skills_interpersonal.csv: missing skill '{name}'")

    award_rows = rows_by_stem.get("awards", [])
    award_titles = {str(row.get("title", "")).casefold() for row in award_rows}
    for title in ("World's Top 2% Scientists", "National Outstanding Student Researcher"):
        if title.casefold() not in award_titles:
            errors.append(f"awards.csv: missing award '{title}'")

    patent_rows = rows_by_stem.get("patents", [])
    patent_titles = {str(row.get("title", "")).casefold() for row in patent_rows}
    for title in (
        "A Machine Learning-Based System for Detecting Leishmaniasis in Microscopic Images",
        "Utilization of Chest Tube in Pediatric Caustic Injuries: A New Method for Esophageal Stenting",
    ):
        if title.casefold() not in patent_titles:
            errors.append(f"patents.csv: missing patent '{title}'")


def validate_all():
    errors = []
    warnings = []
    summaries = []
    last_publication = None
    rows_by_stem = {}

    for path in sorted(DATA.glob("*.csv")):
        stem = path.stem
        _warn_file_encoding(path, warnings)
        _raw_csv_shape_checks(path, stem, errors)
        columns, rows, lines = _read_csv_with_lines(path)
        rows_by_stem[stem] = rows
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
            if rows:
                last_publication = rows[-1]
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

    _validate_requested_cv_content(rows_by_stem, errors)

    # URL hygiene warnings (non-fatal): the build strips tracking params via
    # utils.clean_url, so this surfaces them at the source for a manual cleanup.
    from utils import has_tracking_params

    for stem, url_fields in (("publications", ("url",)), ("presentations", ("url",)), ("open_source", ("url", "demo", "paper"))):
        for idx, row in enumerate(rows_by_stem.get(stem, []), start=1):
            for field in url_fields:
                value = str(row.get(field, "")).strip()
                if value and has_tracking_params(value):
                    warnings.append(f"{stem}.csv: row {idx} field '{field}' contains tracking parameters (build will strip them)")

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
    if last_publication:
        print(
            "[VALIDATE] Last publication row: "
            f"#{str(last_publication.get('n', '')).strip()} "
            f"{str(last_publication.get('title', '')).strip()}"
        )
    print(f"\n[VALIDATE] PASSED: All checks passed. {pub_count} publications in data.")
    return 0


if __name__ == "__main__":
    sys.exit(1 if validate_all() else 0)
