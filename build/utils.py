"""Shared utilities for all CV build scripts."""
import csv, re, pathlib
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


def load_all_data() -> dict:
    """Load every CSV from /data/ into a dict of DataFrames keyed by file stem."""
    result = {}
    for csv_path in DATA.glob("*.csv"):
        result[csv_path.stem] = pd.read_csv(
            csv_path, dtype=str, keep_default_na=False, comment="#"
        )
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
