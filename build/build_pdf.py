"""Convert the generated DOCX CV to PDF with LibreOffice headless."""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent.parent
DOCX = ROOT / "Shahriarirad_Reza_CV.docx"
OUT = ROOT / "Shahriarirad_Reza_CV.pdf"
META = ROOT / "cv_pdf_build.json"


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
    if not DOCX.exists() or DOCX.stat().st_size == 0:
        raise RuntimeError(
            "DOCX input is missing or empty. Run python build/build_word.py before PDF conversion."
        )
    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(ROOT),
        str(DOCX),
    ]
    before_mtime = OUT.stat().st_mtime if OUT.exists() else None
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            "LibreOffice PDF conversion failed.\n"
            + (result.stdout or "")
            + (result.stderr or "")
        )
    if not OUT.exists() or OUT.stat().st_size == 0:
        raise RuntimeError("LibreOffice finished without creating Shahriarirad_Reza_CV.pdf")
    if before_mtime is not None and OUT.stat().st_mtime == before_mtime:
        raise RuntimeError("LibreOffice did not update Shahriarirad_Reza_CV.pdf")
    META.write_text(
        json.dumps(
            {
                "generated": True,
                "method": "libreoffice-docx-to-pdf",
                "source": DOCX.name,
                "output": OUT.name,
                "converter": soffice,
                "docx_bytes": DOCX.stat().st_size,
                "pdf_bytes": OUT.stat().st_size,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"  Generated {OUT.relative_to(ROOT)} from {DOCX.name} ({OUT.stat().st_size:,} bytes)")


def main():
    if not DOCX.exists():
        from build_word import main as build_word_main

        build_word_main()
    soffice = _find_libreoffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice/soffice was not found. Install LibreOffice or set LIBREOFFICE_PATH "
            "so Shahriarirad_Reza_CV.pdf can be converted directly from Shahriarirad_Reza_CV.docx."
        )
    _convert_with_libreoffice(soffice)


if __name__ == "__main__":
    main()
