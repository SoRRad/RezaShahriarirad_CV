"""Generate the one-page compact resume PDF (Shahriarirad_Reza_Resume.pdf).

The layout follows the Google Docs "Serif" resume template: Merriweather for
the name and entries, Open Sans for labels and metadata, small blue uppercase
section headings, and a right-hand sidebar. Content comes from data/resume.csv
plus the shared CSVs (metrics, patents, honors, editorial, languages).

The PDF is rendered directly from HTML with WeasyPrint so it builds the same way
locally and in CI. It is a text PDF with ligatures disabled and, where the
installed WeasyPrint supports it, PDF/UA tagging, so resume parsers and AI
screeners read it cleanly.
"""
from __future__ import annotations

import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import ROOT, author_tag_counts, get_profile, load_all_data  # noqa: E402

OUT = ROOT / "Shahriarirad_Reza_Resume.pdf"
FONTS = pathlib.Path(__file__).parent / "static_assets" / "fonts"

FONT_FACES = [
    ("Merriweather", 400, "normal", "Merriweather-Regular.ttf"),
    ("Merriweather", 700, "normal", "Merriweather-Bold.ttf"),
    ("Merriweather", 400, "italic", "Merriweather-Italic.ttf"),
    ("Open Sans", 400, "normal", "OpenSans-Regular.ttf"),
    ("Open Sans", 600, "normal", "OpenSans-SemiBold.ttf"),
    ("Open Sans", 700, "normal", "OpenSans-Bold.ttf"),
]

CSS = """
@page { size: Letter; margin: 0.5in 0.6in 0.42in; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html { font-variant-ligatures: none; font-feature-settings: "liga" 0, "clig" 0; }
body { font-family: "Merriweather", Georgia, serif; font-size: 8.3pt; line-height: 1.38; color: #3c3c3c; }
a { color: inherit; text-decoration: none; }

.head { display: grid; grid-template-columns: 1fr 2.05in; column-gap: 0.32in; align-items: start; margin-bottom: 0.17in; }
h1 { font-size: 25pt; font-weight: 700; color: #000; line-height: 1.12; letter-spacing: -0.01em; }
.tagline { font-family: "Open Sans", Arial, sans-serif; font-size: 8.6pt; color: #555; margin-top: 0.17in; }
.contact { font-family: "Open Sans", Arial, sans-serif; font-size: 7.5pt; line-height: 1.55; color: #333; padding-top: 0.04in; }

.body { display: grid; grid-template-columns: 1fr 2.05in; column-gap: 0.32in; }

h2 { font-family: "Open Sans", Arial, sans-serif; font-size: 7.6pt; font-weight: 700; letter-spacing: 0.06em;
     text-transform: uppercase; color: #2079c7; margin: 0.13in 0 0.05in; }
main > h2:first-child, aside > h2:first-child { margin-top: 0; }

.entry { margin-bottom: 0.06in; break-inside: avoid; }
.entry h3 { font-size: 9pt; font-weight: 700; color: #000; line-height: 1.3; }
.entry h3 .role { font-weight: 400; font-style: italic; }
.meta { font-family: "Open Sans", Arial, sans-serif; font-size: 7.1pt; color: #6b6b6b; margin-top: 0.01in; }

ul { list-style: none; margin-top: 0.025in; }
/* Hanging-indent bullets with an inline marker. Avoid position:relative/absolute here:
   positioned boxes are painted in a later layer, which moves their text to the end
   of the PDF content stream and scrambles the reading order parsers see. */
li { padding-left: 0.12in; text-indent: -0.12in; margin-bottom: 0.015in; }
li::before { content: "•"; display: inline-block; width: 0.12in; text-indent: 0; color: #2079c7; }

.proj b { color: #000; }
.pub { margin-bottom: 0.05in; }
.pub b { color: #000; font-weight: 700; }
.pub i { font-style: italic; }
.note { font-family: "Open Sans", Arial, sans-serif; font-size: 7.3pt; color: #555; margin-top: 0.03in; }

aside { font-size: 7.9pt; }
aside ul { margin-top: 0; }
.stat { margin-bottom: 0.03in; }
.stat b { font-family: "Merriweather", Georgia, serif; font-weight: 700; color: #000; font-size: 9.6pt; }
.side-item { margin-bottom: 0.04in; }
.side-item b { color: #000; font-weight: 700; }
.side-item .meta { margin-top: 0; }
"""


def _e(value) -> str:
    return html.escape(str(value or "").strip(), quote=True)


def _font_css() -> str:
    rules = []
    for family, weight, style, filename in FONT_FACES:
        path = FONTS / filename
        if path.exists():
            rules.append(
                f'@font-face {{ font-family: "{family}"; font-weight: {weight}; font-style: {style}; '
                f'src: url("{path.resolve().as_uri()}"); }}'
            )
    return "\n".join(rules)


def _rows(df):
    return [] if df is None else df.to_dict("records")


def _int(value, default=0) -> int:
    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _resume_sections(data) -> dict:
    sections: dict[str, list[tuple[str, str]]] = {}
    for row in _rows(data.get("resume")):
        section = str(row.get("section", "")).strip().lower()
        if section:
            sections.setdefault(section, []).append(
                (str(row.get("item", "")).strip(), str(row.get("detail", "")).strip())
            )
    return sections


def _contact(profile) -> str:
    lines = []
    for field in ("email_professional", "email_personal"):
        email = profile.get(field, "").strip()
        if email and profile.get(f"{field}_public_visible", "yes").strip().lower() != "no":
            lines.append(f'<a href="mailto:{_e(email)}">{_e(email)}</a>')
    city = profile.get("city_state", "").strip()
    if city:
        lines.append(_e(city))
    for field in ("linkedin_url", "canonical_url"):
        url = profile.get(field, "").strip()
        if url:
            label = url.split("://", 1)[-1].rstrip("/").removeprefix("www.")
            lines.append(f'<a href="{_e(url)}">{_e(label)}</a>')
    return "<br>".join(lines)


def _entry(title, role, meta, bullets) -> str:
    role_html = f' — <span class="role">{_e(role)}</span>' if role else ""
    items = "".join(f"<li>{_e(b)}</li>" for b in bullets if b)
    bullets_html = f"<ul>{items}</ul>" if items else ""
    return (
        f'<div class="entry"><h3>{_e(title)}{role_html}</h3>'
        f'<div class="meta">{_e(meta)}</div>{bullets_html}</div>'
    )


def _education(data, sections) -> str:
    wanted = [item for item, _ in sections.get("education", [])]
    by_degree = {str(r.get("degree", "")).strip(): r for r in _rows(data.get("education"))}
    parts = []
    for degree in wanted:
        row = by_degree.get(degree)
        if not row:
            continue
        org = str(row.get("org", "")).split("·")[0].strip()
        parts.append(_entry(org, degree, row.get("period", ""), []))
    return "".join(parts)


def _experience(data, sections) -> str:
    order: list[str] = []
    bullets: dict[str, list[str]] = {}
    for role, detail in sections.get("experience", []):
        if role not in bullets:
            order.append(role)
            bullets[role] = []
        if detail:
            bullets[role].append(detail)
    by_role = {str(r.get("role", "")).strip(): r for r in _rows(data.get("experience"))}
    parts = []
    for role in order:
        row = by_role.get(role)
        if not row:
            continue
        org = str(row.get("org", "")).replace(" · ", ", ").strip()
        meta = " · ".join(x for x in (str(row.get("period", "")).strip(), str(row.get("city", "")).strip()) if x)
        parts.append(_entry(org, role, meta, bullets[role]))
    return "".join(parts)


def _projects(sections) -> str:
    items = "".join(
        f'<li class="proj"><b>{_e(name)}</b> — {_e(desc)}</li>' if desc else f'<li class="proj"><b>{_e(name)}</b></li>'
        for name, desc in sections.get("project", [])
    )
    return f"<ul>{items}</ul>" if items else ""


def _author_role(tags: str) -> str:
    tag_set = {t.strip() for t in tags.split(";") if t.strip()}
    if "first" in tag_set:
        return "First author"
    if "co-first" in tag_set:
        return "Co-first author"
    if "last" in tag_set:
        return "Senior author"
    if "corresponding" in tag_set:
        return "Corresponding author"
    return ""


def _publications(data, sections, profile) -> str:
    by_n = {str(r.get("n", "")).strip(): r for r in _rows(data.get("publications"))}
    parts = []
    for n, _ in sections.get("publication", []):
        row = by_n.get(n)
        if not row:
            continue
        year = str(row.get("year", "")).strip()
        role = _author_role(str(row.get("tags", "")))
        tail = " · ".join(x for x in (f"<i>{_e(row.get('journal'))}</i>", _e(year), _e(role)) if x)
        parts.append(f'<div class="pub"><b>{_e(row.get("title"))}</b><div class="meta">{tail}</div></div>')
    pub_count = _int(profile.get("pub_count"), len(by_n))
    scholar = profile.get("scholar_url", "").strip()
    link = f' Full list: <a href="{_e(scholar)}">Google Scholar</a>.' if scholar else ""
    parts.append(f'<div class="note">{pub_count} peer-reviewed publications in total.{link}</div>')
    return "".join(parts)


def _impact(data, profile) -> str:
    counts = author_tag_counts(_rows(data.get("publications")))
    pubs = _int(profile.get("pub_count"))
    citations = _int(profile.get("citations_cached"))
    h_index = _int(profile.get("h_index_cached"))
    reviews = _int(profile.get("peer_reviews"))
    journals = _int(profile.get("journals_reviewed"))
    patents = len(_rows(data.get("patents")))
    first = counts.get("first", 0) + counts.get("co-first", 0)
    stats = [
        (f"{pubs}", f"peer-reviewed publications ({first} first/co-first, {counts.get('last', 0)} senior)"),
        (f"{citations:,}", f"citations · h-index {h_index}"),
        (f"{reviews}", f"peer reviews for {journals} journals"),
        (f"{patents}", "issued patents"),
    ]
    updated = profile.get("metrics_last_updated", "").strip()
    note = f'<div class="meta">Google Scholar, {_e(updated)}</div>' if updated else ""
    return "".join(f'<div class="stat"><b>{_e(num)}</b> {_e(label)}</div>' for num, label in stats) + note


def _skills(data, sections) -> str:
    names, seen = [], set()
    for row in _rows(data.get("skills_research")):
        names.append(str(row.get("name", "")).strip())
    names += [item for item, _ in sections.get("skill", [])]
    unique = []
    for name in names:
        if name and name.lower() not in seen:
            seen.add(name.lower())
            unique.append(name)
    return "<ul>" + "".join(f"<li>{_e(n)}</li>" for n in unique) + "</ul>"


def _tools(sections) -> str:
    tools = [item for item, _ in sections.get("tool", []) if item]
    return f"<div>{_e(' · '.join(tools))}</div>" if tools else ""


def _side_list(rows) -> str:
    return "".join(
        f'<div class="side-item"><b>{_e(title)}</b><div class="meta">{_e(meta)}</div></div>' for title, meta in rows
    )


def _patents(data) -> str:
    return _side_list(
        (r.get("title"), f"{str(r.get('date', '')).strip()} · Patent {str(r.get('issuer', '')).strip()} {str(r.get('number', '')).strip()}")
        for r in _rows(data.get("patents"))
    )


def _honors(data) -> str:
    return _side_list((r.get("title"), f"{str(r.get('org', '')).strip()} · {str(r.get('year', '')).strip()}") for r in _rows(data.get("awards")))


def _editorial(data, profile) -> str:
    rows = [(r.get("role"), f"{str(r.get('journal', '')).strip()} · {str(r.get('period', '')).strip()}") for r in _rows(data.get("editorial"))]
    return _side_list(rows)


def build_html(data) -> str:
    profile = get_profile(data)
    sections = _resume_sections(data)
    name = profile.get("name", "").strip()
    tagline = next((item for item, _ in sections.get("tagline", []) if item), profile.get("title", ""))
    languages = profile.get("languages", "").strip()
    keywords = "; ".join(
        [item for item, _ in sections.get("skill", [])] + [item for item, _ in sections.get("project", [])]
    )

    main = (
        f"<h2>Education</h2>{_education(data, sections)}"
        f"<h2>Professional Experience</h2>{_experience(data, sections)}"
        f"<h2>Surgical Innovation Projects · Mayo Clinic</h2>{_projects(sections)}"
        f"<h2>Selected Publications</h2>{_publications(data, sections, profile)}"
    )
    aside = (
        f"<h2>Research Impact</h2>{_impact(data, profile)}"
        f"<h2>Skills</h2>{_skills(data, sections)}"
        f"<h2>Tools</h2>{_tools(sections)}"
        f"<h2>Patents</h2>{_patents(data)}"
        f"<h2>Honors</h2>{_honors(data)}"
        f"<h2>Editorial</h2>{_editorial(data, profile)}"
    )
    if languages:
        aside += f"<h2>Languages</h2><div>{_e(languages)}</div>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_e(name)} — Resume</title>
<meta name="author" content="{_e(name)}">
<meta name="description" content="{_e(tagline)}">
<meta name="keywords" content="{_e(keywords)}">
<style>{_font_css()}{CSS}</style>
</head>
<body>
<header class="head">
  <div><h1>{_e(name)}</h1><div class="tagline">{_e(tagline)}</div></div>
  <div class="contact">{_contact(profile)}</div>
</header>
<div class="body">
  <main>{main}</main>
  <aside>{aside}</aside>
</div>
</body>
</html>"""


def render(data=None, out: pathlib.Path = OUT) -> int:
    """Write the resume PDF and return its page count."""
    from weasyprint import HTML

    document = HTML(string=build_html(data or load_all_data()), base_url=str(ROOT)).render()
    try:
        document.write_pdf(out, pdf_variant="pdf/ua-1")
    except Exception as exc:  # older WeasyPrint or a tagging failure: still ship a text PDF
        print(f"  PDF/UA tagging unavailable ({exc}); writing an untagged PDF instead.")
        document.write_pdf(out)
    return len(document.pages)


def main():
    pages = render()
    print(f"  Generated {OUT.name} ({OUT.stat().st_size:,} bytes, {pages} page{'s' if pages != 1 else ''})")
    if pages > 1:
        print(
            f"::warning::{OUT.name} runs to {pages} pages; trim data/resume.csv to keep the compact resume on one page."
        )


if __name__ == "__main__":
    main()
