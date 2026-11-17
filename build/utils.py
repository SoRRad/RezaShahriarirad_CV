"""Shared utilities for all CV build scripts."""
import csv, hashlib, io, os, re, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / "data"

TAXONOMY = {
    "ai": {
        "label": "Artificial Intelligence",
        "subs": {
            "computer_vision": "Computer Vision",
            "machine_learning": "Machine Learning",
        },
    },
    "health_sciences": {
        "label": "Health Sciences",
        "subs": {
            "education":      "Medical Education",
            "epidemiology":   "Epidemiology",
            "health_systems": "Health Systems & Policy",
            "pubhealth":      "Public Health",
        },
    },
    "internal_medicine": {
        "label": "Internal Medicine",
        "subs": {
            "derm":       "Dermatology",
            "infectious": "Infectious Disease",
            "neuro":      "Neurology",
            "psych":      "Psychiatry",
            "pulm":       "Pulmonology",
            "urology":    "Urology",
        },
    },
    "surgery": {
        "label": "Surgery",
        "subs": {
            "bariatric":  "Bariatric & Metabolic Surgery",
            "endocrine":  "Endocrine Surgery",
            "gi":         "GI & Colorectal Surgery",
            "oncology":   "Surgical Oncology",
            "ortho":      "Orthopaedic Surgery",
            "plastic":    "Plastic, Reconstructive & Burns",
            "thoracic":   "Thoracic Surgery",
            "transplant": "Transplant Surgery",
            "urosurg":    "Urological Surgery",
            "vascular":   "Vascular Surgery",
        },
    },
}

CAT_LABELS = {
    sub: label
    for grp in TAXONOMY.values()
    for sub, label in grp["subs"].items()
}

# Flat set of all valid sub-keys
ALL_VALID_CAT_KEYS = set(CAT_LABELS.keys())
TOP_LEVEL_CAT_KEYS = set(TAXONOMY.keys())
VALID_AUTHOR_TAGS = {"first", "co-first", "last", "corresponding"}


def load_all_data() -> dict:
    """Load every CSV from /data/ into a dict of DataFrames keyed by file stem."""
    result = {}
    for csv_path in DATA.glob("*.csv"):
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            data_lines = [line for line in handle if not line.startswith("#")]
        result[csv_path.stem] = pd.read_csv(
            io.StringIO("".join(data_lines)),
            dtype=str,
            keep_default_na=False,
        )
        result[csv_path.stem].columns = [str(c).strip().lstrip("\ufeff") for c in result[csv_path.stem].columns]
    return result


_PLACEHOLDER_RE = re.compile(r"\{([a-z][a-z0-9_]*)\}")


def fill_placeholders(text, facts: dict) -> str:
    """Replace {field} tokens in profile prose with that field's value.

    Lets sentences such as "I have authored {pub_count} peer-reviewed
    publications" stay correct as the counts change. Unknown tokens are left
    as written so a typo is visible on the page instead of silently vanishing.
    """
    def repl(match):
        value = str(facts.get(match.group(1), "")).strip()
        return value if value else match.group(0)
    return _PLACEHOLDER_RE.sub(repl, str(text or ""))


def get_profile(data: dict) -> dict:
    """Return profile.csv as a flat dict field→value, with {field} tokens filled."""
    df = data["profile"]
    raw = dict(zip(df["field"], df["value"]))
    return {field: fill_placeholders(value, raw) for field, value in raw.items()}


_MONTH_ORDER = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def newest_first(rows) -> list:
    """Sort publication/presentation records newest first by year, then month.

    The sort is stable, so entries that share a month keep their CSV order.
    The website list and the Word/PDF CV both use it, so they always agree.
    """
    def key(row):
        try:
            year = int(str(row.get("year", "")).strip()[:4])
        except ValueError:
            year = 0
        month = _MONTH_ORDER.get(str(row.get("month", "")).strip()[:3].lower(), 0)
        return (-year, -month)
    return sorted(list(rows), key=key)


def format_authors_html(authors: str) -> str:
    """Wrap 'Shahriarirad R' (with optional *) in <strong> tags for HTML."""
    return re.sub(r"(Shahriarirad R\*?)", r"<strong>\1</strong>", authors)


TRACKING_PARAM_PREFIXES = ("utm_",)
TRACKING_PARAM_NAMES = {
    "gclid", "fbclid", "_gl", "mc_cid", "mc_eid", "igshid", "ref_src",
    "ref", "gclsrc", "dclid", "yclid", "msclkid", "spm", "dgcid", "controls_id",
}


def has_tracking_params(url) -> bool:
    """True if the URL query string carries a known tracking parameter."""
    from urllib.parse import urlsplit, parse_qsl

    query = urlsplit(str(url or "")).query
    for key, _ in parse_qsl(query, keep_blank_values=True):
        low = key.lower()
        if low in TRACKING_PARAM_NAMES or low.startswith(TRACKING_PARAM_PREFIXES):
            return True
    return False


def clean_url(url) -> str:
    """Strip tracking parameters (utm_*, gclid, _gl, ...) from a URL.

    Preserves meaningful query parameters and never rewrites the host/path, so a
    working link stays working. Returns the input unchanged when it is empty or
    not http(s).
    """
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    raw = str(url or "").strip()
    if not raw or not raw.lower().startswith(("http://", "https://")):
        return raw
    parts = urlsplit(raw)
    if not parts.query:
        return raw
    kept = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not (key.lower() in TRACKING_PARAM_NAMES or key.lower().startswith(TRACKING_PARAM_PREFIXES))
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), parts.fragment))


def parse_semicolon(value) -> list:
    """Split a semicolon-separated string into a list; [] for empty/NaN."""
    if not value or (isinstance(value, float)):
        return []
    s = str(value).strip()
    return [x.strip() for x in s.split(";") if x.strip()] if s else []


def author_tag_counts(rows) -> dict:
    """Count explicit authorship tags across publication rows."""
    counts = {tag: 0 for tag in VALID_AUTHOR_TAGS}
    for row in rows:
        raw_tags = row.get("tags", "")
        if isinstance(raw_tags, (list, tuple, set)):
            tag_values = raw_tags
        else:
            tag_values = parse_semicolon(raw_tags)
        tags = {str(tag).strip().lower() for tag in tag_values}
        for tag in counts:
            if tag in tags:
                counts[tag] += 1
    return counts


def write_stable_pdf(document, out, source_html: str) -> None:
    """Write a WeasyPrint document so the same input always gives the same bytes.

    Two things otherwise change on every run: the random file identifier, and
    the "modified" stamp fontTools puts in each embedded font subset. Pinning
    both means the workflow only commits a PDF when its content really changed.
    Neither value is shown to readers; the PDFs carry no creation date.
    """
    os.environ.setdefault("SOURCE_DATE_EPOCH", "1767225600")  # font subset stamp only
    identifier = hashlib.sha256(source_html.encode("utf-8")).hexdigest()[:32].encode("ascii")
    try:
        document.write_pdf(out, pdf_variant="pdf/ua-1", pdf_identifier=identifier)
    except Exception as exc:  # older WeasyPrint or a tagging failure: still ship a text PDF
        print(f"  PDF/UA tagging unavailable ({exc}); writing an untagged PDF instead.")
        document.write_pdf(out, pdf_identifier=identifier)


def html_escape(text: str) -> str:
    """Escape HTML special characters in text."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
