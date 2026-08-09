"""Refresh cached Google Scholar metrics in data/profile.csv.

Google Scholar has no public API and blocks automated HTML scraping from
datacenter / CI IP ranges (HTTP 403/429), which is why a plain scrape from
GitHub Actions almost never succeeds. This script therefore prefers a proper
Scholar data provider and falls back to a best-effort direct scrape:

  1. SerpApi Google Scholar Author API  (reliable)  -- used when the SERPAPI_KEY
     environment variable is set. SerpApi's free tier (100 searches/month) is far
     more than a weekly build needs. Get a key at https://serpapi.com/ and add it
     as a repository secret named SERPAPI_KEY.
  2. Direct scholar.google.com HTML scrape (best-effort fallback).

Rules:
  * Never downgrades a metric (Scholar counts only grow; a lower fetched value is
    treated as a transient error and ignored).
  * Non-fatal: on any failure it prints a notice and exits 0 so a scraping
    problem can never block the build or deploy.
  * On a successful, changed fetch it rewrites data/profile.csv
    (citations_cached, h_index_cached, metrics_last_updated) in place.

Run:  SERPAPI_KEY=... python build/refresh_metrics.py
"""
import csv
import datetime as dt
import io
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).parent.parent
PROFILE_PATH = ROOT / "data" / "profile.csv"


def _as_int(value):
    try:
        return int(str(value or "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def author_id_from_url(scholar_url):
    """Extract the Google Scholar author id (user= param) from the profile URL."""
    query = urllib.parse.urlparse(str(scholar_url or "")).query
    return urllib.parse.parse_qs(query).get("user", [""])[0]


def parse_serpapi(payload):
    """Pull {citations, h_index} from a SerpApi google_scholar_author response.

    SerpApi returns cited_by.table as e.g.
      [{"citations": {"all": 3496, "since_2021": ...}},
       {"h_index":   {"all": 24, ...}},
       {"i10_index": {"all": 60, ...}}]
    """
    out = {}
    table = (payload or {}).get("cited_by", {}).get("table", []) or []
    for entry in table:
        for key, metric in ("citations", "citations"), ("h_index", "h_index"):
            if key in entry:
                out[metric] = _as_int(entry[key].get("all"))
    return {k: v for k, v in out.items() if v is not None}


def parse_scholar_html(html):
    """Pull {citations, h_index} from raw scholar.google.com profile HTML."""
    blocks = re.findall(r'<td[^>]*class="gsc_rsb_std"[^>]*>(\d[\d,]*)</td>', html or "")
    out = {}
    if len(blocks) >= 3:
        out["citations"] = _as_int(blocks[0])   # Citations (All)
        out["h_index"] = _as_int(blocks[2])      # h-index (All)
    return {k: v for k, v in out.items() if v is not None}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def fetch_metrics(scholar_url, serpapi_key=None):
    """Return {citations, h_index} using SerpApi if a key is available, else HTML."""
    if serpapi_key:
        author_id = author_id_from_url(scholar_url)
        if not author_id:
            print("refresh_metrics: could not parse author id from scholar_url; skipping SerpApi.")
        else:
            params = urllib.parse.urlencode({
                "engine": "google_scholar_author",
                "author_id": author_id,
                "hl": "en",
                "api_key": serpapi_key,
            })
            payload = json.loads(_get(f"https://serpapi.com/search.json?{params}"))
            if payload.get("error"):
                raise RuntimeError(f"SerpApi error: {payload['error']}")
            metrics = parse_serpapi(payload)
            if metrics:
                print("refresh_metrics: fetched via SerpApi.")
                return metrics
            print("refresh_metrics: SerpApi returned no cited_by table; falling back to HTML.")
    return parse_scholar_html(_get(scholar_url))


def load_profile():
    comments, rows = [], []
    with PROFILE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            (comments if line.startswith("#") else rows).append(line.rstrip("\n") if line.startswith("#") else line)
    return comments, list(csv.DictReader(rows))


def write_profile(comments, rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["field", "value"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    out = ("\n".join(comments) + "\n" if comments else "") + buffer.getvalue()
    PROFILE_PATH.write_text(out, encoding="utf-8")


def apply_no_downgrade(profile_rows, profile, fetched):
    """Return {field: new_value} for metrics that fetched higher than cached."""
    updates = {}
    plan = [("citations", "citations_cached"), ("h_index", "h_index_cached")]
    for metric, field in plan:
        fetched_val = fetched.get(metric)
        if fetched_val is None:
            continue
        cached = _as_int(profile.get(field))
        if cached is None or fetched_val > cached:
            updates[field] = str(fetched_val)
        elif fetched_val < cached:
            print(f"refresh_metrics: ignoring {field} downgrade (fetched {fetched_val} < cached {cached}).")
    return updates


def main():
    comments, rows = load_profile()
    profile = {r["field"]: r["value"] for r in rows}
    serpapi_key = os.environ.get("SERPAPI_KEY", "").strip() or None
    if not serpapi_key:
        print("refresh_metrics: SERPAPI_KEY not set; attempting best-effort HTML scrape "
              "(Google usually blocks CI IPs). Add a free SerpApi key as the SERPAPI_KEY "
              "secret for reliable Google Scholar refresh.")
    try:
        fetched = fetch_metrics(profile.get("scholar_url", ""), serpapi_key)
    except Exception as exc:  # noqa: BLE001 -- must never break the build
        print(f"::warning::refresh_metrics: Google Scholar refresh failed: {exc}")
        return 0

    if not fetched:
        print("refresh_metrics: no metrics fetched; keeping existing values.")
        return 0

    updates = apply_no_downgrade(rows, profile, fetched)
    if not updates:
        print(f"refresh_metrics: no increase over cached values (fetched {fetched}); nothing to update.")
        return 0

    updates["metrics_last_updated"] = dt.date.today().strftime("%B %d, %Y").replace(" 0", " ")
    for row in rows:
        if row["field"] in updates:
            row["value"] = updates[row["field"]]
    write_profile(comments, rows)
    print("refresh_metrics: updated", json.dumps(updates))
    return 0


if __name__ == "__main__":
    sys.exit(main())
