"""Generate Shahriarirad_Reza_CV.pdf from the generated DOCX when possible."""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import author_tag_counts, get_profile, load_all_data  # noqa: E402

ROOT = pathlib.Path(__file__).parent.parent
DOCX = ROOT / "Shahriarirad_Reza_CV.docx"
OUT = ROOT / "Shahriarirad_Reza_CV.pdf"


def _find_libreoffice():
    candidates = [
        os.environ.get("LIBREOFFICE_PATH"),
        os.environ.get("SOFFICE_PATH"),
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for candidate in candidates:
        if candidate and pathlib.Path(candidate).exists():
            return str(candidate)
    return None


def _convert_with_libreoffice(soffice):
    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(ROOT),
        str(DOCX),
    ]
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            "LibreOffice PDF conversion failed.\n"
            + (result.stdout or "")
            + (result.stderr or "")
        )
    if not OUT.exists() or OUT.stat().st_size == 0:
        raise RuntimeError("LibreOffice finished without creating Shahriarirad_Reza_CV.pdf")
    print(f"  Generated {OUT.relative_to(ROOT)} from {DOCX.name} ({OUT.stat().st_size:,} bytes)")


def _e(value):
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _fallback_pdf():
    """Fallback for local machines without LibreOffice; CI installs LibreOffice."""
    try:
        from weasyprint import HTML
    except Exception as exc:
        raise RuntimeError(
            "LibreOffice was not found and WeasyPrint fallback is unavailable. "
            "Install LibreOffice or run the GitHub Actions build."
        ) from exc

    data = load_all_data()
    profile = get_profile(data)
    pubs = data["publications"].to_dict("records")
    counts = author_tag_counts(pubs)
    emails = [
        profile.get("email_professional", ""),
        profile.get("email_personal", ""),
    ]
    email_line = " | ".join(_e(email) for email in emails if email)
    style = """
    @page { size: A4; margin: 18mm; }
    body { font-family: Arial, sans-serif; font-size: 9.5pt; color: #1a2740; line-height: 1.45; }
    h1 { color: #1F3864; margin-bottom: 2mm; }
    h2 { color: #1F3864; border-bottom: 1px solid #1F3864; font-size: 12pt; margin-top: 7mm; }
    table { width: 100%; border-collapse: collapse; margin: 2mm 0 4mm; }
    td, th { border: 1px solid #c8d4e0; padding: 3pt 4pt; vertical-align: top; }
    th { background: #D9EAF7; color: #1F3864; text-align: left; }
    .muted { color: #5d6878; }
    """
    rows = "".join(
        f"<tr><td>{_e(r.get('n'))}</td><td>{_e(r.get('year'))}</td><td>{_e(r.get('title'))}</td><td>{_e(r.get('journal'))}</td></tr>"
        for r in pubs
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
    <h1>Reza Shahriarirad, M.D.</h1>
    <div class="muted">{_e(profile.get('title'))} | {_e(profile.get('institution'))}</div>
    <div>{email_line}</div>
    <div>ORCID: {_e(profile.get('orcid_url') or profile.get('orcid'))}</div>
    <h2>Publication Metrics</h2>
    <table><tr><th>Total publications</th><th>First author</th><th>Co-first</th><th>Last/senior</th><th>Corresponding</th><th>H-index</th><th>Citations</th></tr>
    <tr><td>{len(pubs)}</td><td>{counts['first']}</td><td>{counts['co-first']}</td><td>{counts['last']}</td><td>{counts['corresponding']}</td><td>{_e(profile.get('h_index_cached'))}</td><td>{_e(profile.get('citations_cached'))}</td></tr></table>
    <h2>Appendix A: Publications</h2>
    <table><tr><th>#</th><th>Year</th><th>Title</th><th>Journal</th></tr>{rows}</table>
    </body></html>"""
    HTML(string=html, base_url=str(ROOT)).write_pdf(str(OUT))
    print(
        f"  Generated {OUT.relative_to(ROOT)} with WeasyPrint fallback "
        f"({OUT.stat().st_size:,} bytes). Install LibreOffice for DOCX-to-PDF conversion."
    )


def main():
    if not DOCX.exists():
        from build_word import main as build_word_main

        build_word_main()
    soffice = _find_libreoffice()
    if soffice:
        _convert_with_libreoffice(soffice)
    else:
        print("[build_pdf] WARNING: LibreOffice not found; using local WeasyPrint fallback.")
        _fallback_pdf()


if __name__ == "__main__":
    main()
