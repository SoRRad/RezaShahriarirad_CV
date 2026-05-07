"""Shared utilities for all CV build scripts."""
import csv, re, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / "data"

TAXONOMY = {
    "surgery": {
        "label": "Surgery",
        "subs": {
            "plastic":   "Plastic, Reconstructive & Burns",
            "thoracic":  "Thoracic Surgery",
            "vascular":  "Vascular Surgery",
            "gi":        "GI & Colorectal Surgery",
            "endocrine": "Endocrine Surgery",
            "ortho":     "Orthopaedic Surgery",
            "urosurg":   "Urological Surgery",
            "transplant":"Transplant Surgery",
            "oncology":  "Surgical Oncology",
        },
    },
    "medicine": {
        "label": "Internal Medicine",
        "subs": {
            "infectious": "Infectious Disease",
            "pulm":       "Pulmonology",
            "neuro":      "Neurology",
            "derm":       "Dermatology",
            "urology":    "Urology",
        },
    },
    "ai": {
        "label": "Artificial Intelligence",
        "subs": {"ai": "AI & Machine Learning"},
    },
    "pubhealth": {
        "label": "Public Health",
        "subs": {"pubhealth": "Public Health & Epidemiology"},
    },
}

CAT_LABELS = {
    sub: label
    for grp in TAXONOMY.values()
    for sub, label in grp["subs"].items()
}


def load_all_data() -> dict:
    """Load every CSV from /data/ into a dict of DataFrames keyed by file stem."""
    result = {}
    for csv_path in DATA.glob("*.csv"):
        result[csv_path.stem] = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    return result


def get_profile(data: dict) -> dict:
    """Return profile.csv as a flat dict field→value."""
    df = data["profile"]
    return dict(zip(df["field"], df["value"]))


def format_authors_html(authors: str) -> str:
    """Wrap 'Shahriarirad R' (with optional *) in <strong> tags for HTML."""
    return re.sub(r"(Shahriarirad R\*?)", r"<strong>\1</strong>", authors)


def parse_semicolon(value) -> list:
    """Split a semicolon-separated string into a list; [] for empty/NaN."""
    if not value or (isinstance(value, float)):
        return []
    s = str(value).strip()
    return [x.strip() for x in s.split(";") if x.strip()] if s else []


def html_escape(text: str) -> str:
    """Escape HTML special characters in text."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
