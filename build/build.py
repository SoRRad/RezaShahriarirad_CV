"""
build.py - orchestrates all CV build steps.
Run from the repo root: python build/build.py
  --preview    After build, open index.html in the default browser.
"""
import argparse
import csv
import importlib
import json
import pathlib
import sys

BUILD_DIR = pathlib.Path(__file__).parent
ROOT = BUILD_DIR.parent
DATA_DIR = ROOT / "data"
sys.path.insert(0, str(BUILD_DIR))

STEPS = [
    ("build_html", "Generating index.html"),
    ("build_word", "Generating Shahriarirad_Reza_CV.docx"),
    ("build_pdf", "Generating Shahriarirad_Reza_CV.pdf"),
]


def _csv_rows(stem):
    path = DATA_DIR / f"{stem}.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        data_lines = [line for line in handle if not line.startswith("#")]
    return list(csv.DictReader(data_lines))


def _split_semicolon(value):
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def _write_json(path, payload):
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"  Generated {path.relative_to(ROOT)}")


def generate_legacy_json():
    """Generate legacy JSON artifacts from CSV sources."""
    pubs = []
    for row in _csv_rows("publications"):
        out = dict(row)
        for key in ("tags", "cat", "keywords", "highlight_topics"):
            out[key] = _split_semicolon(out.get(key, ""))
        try:
            out["n"] = int(out.get("n", ""))
        except ValueError:
            pass
        pubs.append(out)

    presentations = []
    for row in _csv_rows("presentations"):
        out = dict(row)
        for key in ("cat", "keywords"):
            out[key] = _split_semicolon(out.get(key, ""))
        presentations.append(out)

    journals = _csv_rows("journals")
    profile = {row["field"]: row["value"] for row in _csv_rows("profile")}
    live_stats = {
        "generated": True,
        "source": "data/profile.csv",
        "citations": profile.get("citations_cached", ""),
        "hindex": profile.get("h_index_cached", ""),
        "peerReviews": profile.get("peer_reviews", ""),
        "journals": profile.get("journals_reviewed", ""),
        "manuscripts": profile.get("manuscripts_reviewed", ""),
        "pubCount": str(len(pubs)),
        "firstAuth": profile.get("first_auth", ""),
        "secondAuth": profile.get("co_first_auth", ""),
        "lastAuth": profile.get("last_auth", ""),
        "corrAuth": profile.get("corr_auth", ""),
        "date": profile.get("metrics_last_updated", ""),
    }

    _write_json(ROOT / "cv_pubs.json", pubs)
    _write_json(ROOT / "cv_presentations.json", presentations)
    _write_json(ROOT / "cv_journals.json", journals)
    _write_json(ROOT / "cv_live_stats.json", live_stats)


def main():
    parser = argparse.ArgumentParser(description="Build the CV website.")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open index.html in the default browser after build.",
    )
    args = parser.parse_args()

    print("[BUILD] Running validation ...")
    try:
        from validate_data import validate_all

        n_errors = validate_all()
        if n_errors > 0:
            print(
                f"[BUILD] ABORTED: fix {n_errors} validation error(s) before building.",
                file=sys.stderr,
            )
            sys.exit(1)
        print("[BUILD] Validation passed.\n")
    except Exception:
        import traceback

        print("[BUILD] FAILED: validation step crashed:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

    print("[BUILD] Generating legacy JSON artifacts ...")
    try:
        generate_legacy_json()
    except Exception:
        import traceback

        print("[BUILD] FAILED: legacy JSON generation crashed:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

    failed = []
    for module_name, label in STEPS:
        print(f"[BUILD] {label} ...")
        try:
            mod = importlib.import_module(module_name)
            mod.main()
            print(f"[BUILD] DONE: {label}")
        except Exception as exc:
            import traceback

            print(f"[BUILD] FAILED: {label}", file=sys.stderr)
            traceback.print_exc()
            failed.append((label, exc))

    if failed:
        print(f"\n[BUILD] {len(failed)} step(s) failed:", file=sys.stderr)
        for label, exc in failed:
            print(f"  - {label}: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\n[BUILD] All steps completed successfully.")

    if args.preview:
        import webbrowser

        index = (ROOT / "index.html").resolve()
        webbrowser.open(index.as_uri())
        print("Preview opened in browser.")


if __name__ == "__main__":
    main()
