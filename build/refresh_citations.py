"""Refresh per-paper citation counts in data/citations.csv from Google Scholar.

Runs in the weekly scheduled build only (it costs two or three SerpApi searches
per run), and only when the SERPAPI_KEY secret is set. It reads the articles on
the Google Scholar profile, matches them to data/publications.csv by title, and
writes one row per matched paper. Any failure leaves the existing file alone:
the site simply shows the counts it already has, or none.

Run:  SERPAPI_KEY=... python build/refresh_citations.py
"""
from __future__ import annotations

import csv
import io
import json
import os
import pathlib
import re
import sys
import unicodedata
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import refresh_metrics as rm  # noqa: E402

ROOT = pathlib.Path(__file__).parent.parent
PUBS_PATH = ROOT / "data" / "publications.csv"
OUT_PATH = ROOT / "data" / "citations.csv"
HEADER = (
    "# COLUMN GUIDE: Written by build/refresh_citations.py from Google Scholar; do not edit by hand. "
    "n=publication number in publications.csv, citations=times cited.\n"
)
PAGE_SIZE = 100
MAX_PAGES = 4


def normalize_title(title) -> str:
    """Lowercase, strip accents and punctuation so small formatting differences still match."""
    text = unicodedata.normalize("NFKD", str(title or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def parse_articles(payload) -> list:
    """Return [(title, citations)] from one SerpApi google_scholar_author response."""
    out = []
    for article in (payload or {}).get("articles", []) or []:
        title = str(article.get("title", "")).strip()
        cited = (article.get("cited_by") or {}).get("value")
        try:
            cited = int(cited)
        except (TypeError, ValueError):
            cited = 0
        if title:
            out.append((title, cited))
    return out


def match_citations(pub_rows, articles) -> dict:
    """Map publication number -> citations for articles whose title matches a publication."""
    by_title = {}
    for title, cited in articles:
        key = normalize_title(title)
        if key:
            by_title[key] = max(cited, by_title.get(key, 0))
    out = {}
    for row in pub_rows:
        key = normalize_title(row.get("title", ""))
        n = str(row.get("n", "")).strip()
        if n and key in by_title:
            out[n] = by_title[key]
    return out


def fetch_articles(author_id, api_key) -> list:
    articles = []
    for page in range(MAX_PAGES):
        params = urllib.parse.urlencode({
            "engine": "google_scholar_author", "author_id": author_id, "hl": "en",
            "num": PAGE_SIZE, "start": page * PAGE_SIZE, "api_key": api_key,
        })
        payload = json.loads(rm._get(f"https://serpapi.com/search.json?{params}"))
        if payload.get("error"):
            raise RuntimeError(f"SerpApi error: {payload['error']}")
        batch = parse_articles(payload)
        articles.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
    return articles


def _pub_rows():
    with PUBS_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def write_citations(matched: dict) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["n", "citations"])
    for n in sorted(matched, key=lambda value: int(value) if value.isdigit() else 0):
        writer.writerow([n, matched[n]])
    OUT_PATH.write_text(HEADER + buffer.getvalue(), encoding="utf-8")


def main():
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        print("refresh_citations: SERPAPI_KEY not set; skipping per-paper citation refresh.")
        return 0
    try:
        _, rows = rm.load_profile()
        profile = {r["field"]: r["value"] for r in rows}
        author_id = rm.author_id_from_url(profile.get("scholar_url", ""))
        if not author_id:
            print("refresh_citations: could not read the Scholar author id; skipping.")
            return 0
        articles = fetch_articles(author_id, api_key)
        pubs = _pub_rows()
        matched = match_citations(pubs, articles)
    except Exception as exc:  # noqa: BLE001 -- must never break the build
        print(f"::warning::refresh_citations: per-paper citation refresh failed: {exc}")
        return 0
    # A thin result means Scholar returned something unexpected; keep the old file.
    if len(matched) < max(10, len(pubs) // 4):
        print(f"::warning::refresh_citations: matched only {len(matched)} of {len(pubs)} papers; keeping existing counts.")
        return 0
    write_citations(matched)
    print(f"refresh_citations: wrote counts for {len(matched)} of {len(pubs)} papers ({len(articles)} Scholar articles read).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
