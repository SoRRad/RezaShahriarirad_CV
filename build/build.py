"""
build.py — orchestrates all CV build steps.
Run from the repo root: python build/build.py
"""
import sys
import pathlib

# Add build/ to path so sub-modules import utils correctly
BUILD_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(BUILD_DIR))

STEPS = [
    ("build_html", "Generating index.html"),
    ("build_word", "Generating Shahriarirad_Reza_CV.docx"),
    ("build_pdf",  "Generating Shahriarirad_Reza_CV.pdf"),
]


def main():
    import importlib
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
    else:
        print("\n[BUILD] All steps completed successfully.")


if __name__ == "__main__":
    main()
