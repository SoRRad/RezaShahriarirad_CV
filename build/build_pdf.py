"""Convert the generated DOCX CV to PDF with LibreOffice headless."""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).parent.parent
DOCX = ROOT / "Shahriarirad_Reza_CV.docx"
OUT = ROOT / "Shahriarirad_Reza_CV.pdf"
META = ROOT / "cv_pdf_build.json"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _find_libreoffice():
    program_files = pathlib.Path(r"C:\Program Files\LibreOffice\program")
    program_files_x86 = pathlib.Path(r"C:\Program Files (x86)\LibreOffice\program")
    candidates = [
        os.environ.get("LIBREOFFICE_PATH"),
        os.environ.get("SOFFICE_PATH"),
        shutil.which("soffice.com"),
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        str(program_files / "soffice.com"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        str(program_files_x86 / "soffice.com"),
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
    with tempfile.TemporaryDirectory(prefix="cv-pdf-", ignore_cleanup_errors=True) as out_dir:
        out_path = pathlib.Path(out_dir)
        cmd = [
            soffice,
            "--headless",
            "--nologo",
            "--nodefault",
            "--nofirststartwizard",
            "--nolockcheck",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_path),
            str(DOCX),
        ]
        try:
            result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False, timeout=120)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("LibreOffice PDF conversion timed out after 120 seconds.") from exc
        converted = out_path / OUT.name
        if result.returncode != 0:
            raise RuntimeError(
                "LibreOffice PDF conversion failed.\n"
                + (result.stdout or "")
                + (result.stderr or "")
            )
        if not converted.exists() or converted.stat().st_size == 0:
            raise RuntimeError(
                "LibreOffice finished without creating a fresh Shahriarirad_Reza_CV.pdf.\n"
                + (result.stdout or "")
                + (result.stderr or "")
            )
        shutil.copy2(converted, OUT)
    if not OUT.exists() or OUT.stat().st_size == 0:
        raise RuntimeError("LibreOffice finished without creating Shahriarirad_Reza_CV.pdf")
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


def _docx_text_elements(element):
    return "".join(t.text or "" for t in element.findall(".//w:t", NS))


def _docx_to_html():
    import html

    with zipfile.ZipFile(DOCX) as docx:
        xml = docx.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find("w:body", NS)
    parts = []
    for child in list(body):
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = _docx_text_elements(child).strip()
            if not text:
                parts.append("<p class='spacer'></p>")
                continue
            style = "para"
            upper = text.upper()
            if text == upper and len(text) < 80:
                style = "section"
            elif text.startswith("Appendix "):
                style = "section appendix"
            parts.append(f"<p class='{style}'>{html.escape(text)}</p>")
        elif tag == "tbl":
            rows = []
            for tr in child.findall("w:tr", NS):
                cells = []
                for tc in tr.findall("w:tc", NS):
                    cells.append(html.escape(_docx_text_elements(tc).strip()))
                if any(cells):
                    rows.append(cells)
            if rows:
                html_rows = []
                for idx, row in enumerate(rows):
                    cell_tag = "th" if idx == 0 and len(rows) > 1 else "td"
                    html_rows.append("<tr>" + "".join(f"<{cell_tag}>{cell}</{cell_tag}>" for cell in row) + "</tr>")
                parts.append("<table>" + "".join(html_rows) + "</table>")
    return """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
@page { size: Letter; margin: 0.62in 0.65in; }
body { font-family: Arial, sans-serif; color: #222a35; font-size: 9.2pt; line-height: 1.32; }
p { margin: 0 0 4pt; }
.para { margin-bottom: 4pt; }
.spacer { height: 2pt; margin: 0; }
.section { color: #1f3864; font-weight: 700; font-size: 10.5pt; margin: 9pt 0 4pt; padding-bottom: 2pt; border-bottom: 1.2pt solid #b8953a; letter-spacing: .02em; }
.appendix { page-break-before: always; }
table { width: 100%; border-collapse: collapse; margin: 2pt 0 7pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { background: #d9eaf7; color: #1f3864; font-weight: 700; }
td, th { border: .45pt solid #c8d4e0; padding: 3pt 4pt; vertical-align: top; font-size: 8.4pt; }
</style>
</head>
<body>
""" + "\n".join(parts) + "\n</body>\n</html>\n"


def _convert_with_weasyprint_fallback(error):
    try:
        from weasyprint import HTML
    except Exception as exc:
        raise RuntimeError(
            "LibreOffice PDF conversion failed and WeasyPrint fallback is unavailable.\n"
            + str(error)
        ) from exc

    html_text = _docx_to_html()
    HTML(string=html_text, base_url=str(ROOT)).write_pdf(str(OUT))
    if not OUT.exists() or OUT.stat().st_size == 0:
        raise RuntimeError("WeasyPrint DOCX fallback did not create Shahriarirad_Reza_CV.pdf")
    META.write_text(
        json.dumps(
            {
                "generated": True,
                "converted_from_docx": True,
                "method": "weasyprint-docx-extracted-to-pdf-fallback",
                "preferred_method": "libreoffice-docx-to-pdf",
                "source": DOCX.name,
                "output": OUT.name,
                "libreoffice_error": str(error),
                "docx_bytes": DOCX.stat().st_size,
                "pdf_bytes": OUT.stat().st_size,
                "timestamp": int(time.time()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"  Generated {OUT.relative_to(ROOT)} from {DOCX.name} "
        f"with WeasyPrint fallback after LibreOffice failed ({OUT.stat().st_size:,} bytes)"
    )


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
    try:
        _convert_with_libreoffice(soffice)
    except Exception as exc:
        _convert_with_weasyprint_fallback(exc)


if __name__ == "__main__":
    main()
