"""Generate the full CV PDF (Shahriarirad_Reza_CV.pdf) from the CSV data.

The PDF is typeset directly from HTML with WeasyPrint, the same way the compact
resume is, so it shares the resume's look (Merriweather / Open Sans), has
clickable links, running page numbers and a tagged text layer. The Word version
(build_word.py) is still generated for anyone who needs an editable file, but
the PDF no longer depends on it or on LibreOffice.

Run: python build/build_pdf.py
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import ROOT, author_tag_counts, clean_url, get_profile, load_all_data, newest_first, write_stable_pdf  # noqa: E402
from build_resume import _font_css  # noqa: E402  (bundled fonts, shared with the resume)

OUT = ROOT / "Shahriarirad_Reza_CV.pdf"
META = ROOT / "cv_pdf_build.json"
METHOD = "weasyprint-html-to-pdf"

PUB_GROUPS = [
    ("original", "Original Articles"),
    ("review", "Reviews and Meta-analyses"),
    ("case", "Case Reports"),
    ("letter", "Letters and Editorials"),
]

CSS = """
@page {
  size: Letter; margin: 0.7in 0.75in 0.75in;
  @bottom-left { content: "Reza Shahriarirad, M.D. · Curriculum Vitae"; font: 7.5pt "Open Sans", sans-serif; color: #6b7280; }
  @bottom-right { content: counter(page) " / " counter(pages); font: 7.5pt "Open Sans", sans-serif; color: #6b7280; }
}
@page :first { @bottom-left { content: ""; } }
* { box-sizing: border-box; }
html { font-family: "Open Sans", Arial, sans-serif; font-size: 9pt; line-height: 1.45; color: #1f2937;
       font-variant-ligatures: none; }
body { margin: 0; }
a { color: inherit; text-decoration: none; }
h1 { font-family: "Merriweather", Georgia, serif; font-size: 23pt; font-weight: 700; line-height: 1.1;
     margin: 0; color: #0f172a; letter-spacing: -0.01em; }
.title-line { font-size: 10.5pt; color: #374151; margin: 0.09in 0 0.07in; }
.contact { font-size: 8.3pt; color: #4b5563; line-height: 1.6; }
.contact a { color: #0e7490; }
.rule { border: 0; border-top: 1.5pt solid #0f172a; margin: 0.14in 0 0; }
h2 { font-family: "Open Sans", Arial, sans-serif; font-size: 8.6pt; font-weight: 700; letter-spacing: 0.09em;
     text-transform: uppercase; color: #0e7490; margin: 0.24in 0 0.08in; padding-bottom: 0.03in;
     border-bottom: 0.6pt solid #cbd5e1; break-after: avoid; }
h3 { font-family: "Merriweather", Georgia, serif; font-size: 9.6pt; font-weight: 700; color: #0f172a;
     margin: 0.16in 0 0.06in; break-after: avoid; }
p { margin: 0 0 0.07in; }
.metrics { display: flex; gap: 0.3in; margin: 0.02in 0 0; }
.metric b { display: block; font-family: "Merriweather", Georgia, serif; font-size: 15pt; line-height: 1.15; color: #0f172a; }
.metric span { font-size: 7.6pt; color: #6b7280; text-transform: uppercase; letter-spacing: 0.06em; }
.entry { display: flex; gap: 0.2in; margin-bottom: 0.09in; break-inside: avoid; }
.entry .when { flex: 0 0 1.05in; font-size: 8.3pt; color: #6b7280; padding-top: 0.01in; }
.entry .what { flex: 1; }
.entry .what b { font-weight: 700; color: #0f172a; }
.entry .org { color: #374151; }
.entry .desc { color: #4b5563; margin-top: 0.02in; font-size: 8.6pt; }
.kv { display: flex; gap: 0.2in; margin-bottom: 0.05in; break-inside: avoid; }
.kv .k { flex: 0 0 1.05in; font-size: 8.3pt; color: #6b7280; }
.kv .v { flex: 1; }
ol.pubs { list-style: none; margin: 0; padding: 0; }
ol.pubs li { display: flex; gap: 0.1in; margin-bottom: 0.055in; font-size: 8.5pt; line-height: 1.42; break-inside: avoid; }
ol.pubs .num { flex: 0 0 0.3in; text-align: right; color: #6b7280; font-variant-numeric: tabular-nums; }
ol.pubs .cit { flex: 1; }
ol.pubs .me { font-weight: 700; color: #0f172a; }
ol.pubs .jr { font-style: italic; }
ol.pubs .yr { color: #6b7280; }
ol.pubs .lnk { color: #0e7490; font-size: 7.8pt; word-break: break-all; }
.cols { column-count: 2; column-gap: 0.3in; font-size: 8.5pt; }
.cols div { break-inside: avoid; margin-bottom: 0.02in; }
.refs { display: flex; flex-wrap: wrap; gap: 0.12in 0.3in; }
.ref { flex: 0 0 calc(50% - 0.15in); font-size: 8.5pt; break-inside: avoid; }
.ref b { color: #0f172a; }
.ref .lnk { color: #0e7490; font-size: 7.8pt; }
.note { font-size: 7.8pt; color: #6b7280; }
.appendix { break-before: page; }
"""


def _e(value) -> str:
    return html.escape(str(value or "").strip(), quote=True)


def _rows(df):
    return [] if df is None else df.to_dict("records")


def _yes(value) -> bool:
    return str(value or "").strip().lower() in {"yes", "true", "1", "y"}


def _thousands(value) -> str:
    text = str(value or "").strip().replace(",", "")
    return f"{int(text):,}" if text.isdigit() else str(value or "").strip()


def _link(url, label=None) -> str:
    url = clean_url(str(url or "").strip())
    if not url.lower().startswith(("http://", "https://")):
        return ""
    shown = label or re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    return f'<a href="{_e(url)}">{_e(shown)}</a>'


def _entry(when, title, org="", desc="") -> str:
    org_html = f'<div class="org">{_e(org)}</div>' if str(org or "").strip() else ""
    desc_html = f'<div class="desc">{_e(desc)}</div>' if str(desc or "").strip() else ""
    return (
        f'<div class="entry"><div class="when">{_e(when)}</div>'
        f'<div class="what"><b>{_e(title)}</b>{org_html}{desc_html}</div></div>'
    )


def _header(profile) -> str:
    name = profile.get("name", "Reza Shahriarirad, M.D.")
    title = " · ".join(x for x in (profile.get("title", ""), profile.get("institution", ""), profile.get("city_state", "")) if x)
    emails = [
        profile.get(field, "").strip()
        for field in ("email_professional", "email_personal")
        if profile.get(field, "").strip() and _yes(profile.get(f"{field}_public_visible", "yes"))
    ]
    contact = [f'<a href="mailto:{_e(e)}">{_e(e)}</a>' for e in emails]
    links = [
        _link(profile.get(field, ""), label)
        for field, label in (
            ("canonical_url", None), ("orcid_url", "ORCID " + profile.get("orcid", "")),
            ("scholar_url", "Google Scholar"), ("pubmed_url", "PubMed"), ("scopus_url", "Scopus"),
            ("researchgate_url", "ResearchGate"), ("linkedin_url", "LinkedIn"), ("github_url", "GitHub"),
        )
    ]
    return (
        f"<h1>{_e(name)}</h1>"
        f'<div class="title-line">{_e(title)}</div>'
        f'<div class="contact">{" · ".join(contact)}<br>{" · ".join(x for x in links if x)}</div>'
        '<hr class="rule">'
    )


def _summary(profile) -> str:
    text = profile.get("cv_summary") or profile.get("bio_paragraph_1", "")
    return f"<h2>Research Summary</h2><p>{_e(text)}</p>" if text.strip() else ""


def _metrics(profile, pubs) -> str:
    counts = author_tag_counts(pubs)
    cells = [
        (len(pubs), "Publications"),
        (_thousands(profile.get("citations_cached", "")), "Citations"),
        (profile.get("h_index_cached", ""), "h-index"),
        (counts["first"] + counts["co-first"], "First / co-first author"),
        (counts["last"], "Senior author"),
        (counts["corresponding"], "Corresponding author"),
    ]
    body = "".join(f'<div class="metric"><b>{_e(v)}</b><span>{_e(k)}</span></div>' for v, k in cells if str(v).strip())
    updated = profile.get("metrics_last_updated", "").strip()
    note = f'<p class="note" style="margin-top:.06in">Citations and h-index from Google Scholar{", " + _e(updated) if updated else ""}.</p>'
    return f'<h2>Publication Metrics</h2><div class="metrics">{body}</div>{note}'


def _experience(data) -> str:
    items = "".join(
        _entry(r.get("period", ""), r.get("role", ""), " · ".join(x for x in (r.get("org", ""), r.get("city", "")) if str(x).strip()), r.get("desc", ""))
        for r in _rows(data.get("experience"))
    )
    return f"<h2>Professional Experience</h2>{items}" if items else ""


def _education(data) -> str:
    items = "".join(
        _entry(r.get("period", ""), r.get("degree", ""), " · ".join(x for x in (r.get("org", ""), r.get("city", "")) if str(x).strip()))
        for r in _rows(data.get("education"))
    )
    return f"<h2>Education</h2>{items}" if items else ""


def _mayo(profile) -> str:
    paras = [profile.get(f"work_mayo_clinic_{i}", "").strip() for i in (1, 2, 3)]
    body = "".join(f"<p>{_e(p)}</p>" for p in paras if p)
    return f"<h2>Work at Mayo Clinic</h2>{body}" if body else ""


def _awards(data) -> str:
    items = "".join(_entry(r.get("year", ""), r.get("title", ""), r.get("org", "")) for r in _rows(data.get("awards")))
    return f"<h2>Awards and Honors</h2>{items}" if items else ""


def _visible(rows):
    return [r for r in rows if str(r.get("public_visible", "")).strip().lower() not in ("no", "false", "0")
            and str(r.get("title", "")).strip()]


def _grants(data) -> str:
    items = "".join(
        _entry(r.get("period", ""), r.get("title", ""),
               " · ".join(str(r.get(k, "")).strip() for k in ("funder", "role", "amount", "status") if str(r.get(k, "")).strip()))
        for r in _visible(_rows(data.get("grants")))
    )
    return f"<h2>Grants and Funding</h2>{items}" if items else ""


def _invited_talks(data) -> str:
    items = "".join(
        _entry(r.get("date", ""), r.get("title", ""),
               " · ".join(str(r.get(k, "")).strip() for k in ("kind", "host", "location") if str(r.get(k, "")).strip()))
        for r in _visible(_rows(data.get("invited_talks")))
    )
    return f"<h2>Invited Talks</h2>{items}" if items else ""


def _patents(data) -> str:
    items = "".join(
        _entry(r.get("date", ""), r.get("title", ""), f'Patent {str(r.get("issuer", "")).strip()} {str(r.get("number", "")).strip()}'.strip())
        for r in _rows(data.get("patents"))
    )
    return f"<h2>Patents</h2>{items}" if items else ""


def _leadership(data) -> str:
    rows = _rows(data.get("leadership"))
    out = []
    for kind, label in (("teaching", "Teaching and Mentorship"), ("service", "Service and Community")):
        group = [r for r in rows if (str(r.get("kind", "")).strip().lower() == "teaching") == (kind == "teaching")]
        if group:
            out.append(f"<h3>{label}</h3>" + "".join(_entry(r.get("period", ""), r.get("title", ""), r.get("org", ""), r.get("desc", "")) for r in group))
    return "<h2>Leadership, Teaching and Service</h2>" + "".join(out) if out else ""


def _editorial(data, profile) -> str:
    items = "".join(_entry(r.get("period", ""), r.get("role", ""), r.get("journal", "")) for r in _rows(data.get("editorial")))
    review = (
        f'{_e(profile.get("peer_reviews", ""))} verified peer reviews of {_e(profile.get("manuscripts_reviewed", ""))} manuscripts '
        f'for {_e(profile.get("journals_reviewed", ""))} journals (listed in Appendix B).'
    )
    return f"<h2>Editorial and Peer Review</h2>{items}<p>{review}</p>"


def _skills(data, profile) -> str:
    def names(stem, with_level=False):
        out = []
        for r in _rows(data.get(stem)):
            name = str(r.get("name", "")).strip()
            level = str(r.get("level", "")).strip()
            if name:
                out.append(f"{name} ({level})" if with_level and level else name)
        return "; ".join(out)

    rows = [
        ("Research", names("skills_research")),
        ("Software", names("skills_computing", with_level=True)),
        ("Interpersonal", names("skills_interpersonal")),
        ("Languages", profile.get("languages", "")),
    ]
    body = "".join(f'<div class="kv"><div class="k">{_e(k)}</div><div class="v">{_e(v)}</div></div>' for k, v in rows if str(v).strip())
    return f"<h2>Skills and Languages</h2>{body}" if body else ""


def _references(data) -> str:
    cards = []
    for r in _rows(data.get("references")):
        links = " · ".join(
            x for x in (_link(r.get(f"link_url_{i}", ""), str(r.get(f"link_label_{i}", "")).strip() or None) for i in (1, 2)) if x
        )
        cards.append(
            f'<div class="ref"><b>{_e(r.get("name", ""))}</b><br>{_e(r.get("role", ""))}<br>'
            f'<span class="note">{_e(r.get("inst", ""))}</span>'
            + (f'<br><span class="lnk">{links}</span>' if links else "")
            + "</div>"
        )
    return f'<h2>References</h2><div class="refs">{"".join(cards)}</div>' if cards else ""


def _authors_html(authors) -> str:
    return re.sub(r"(Shahriarirad R\*?)", r'<span class="me">\1</span>', _e(authors))


def _publications(pubs) -> str:
    out = ['<section class="appendix"><h2>Appendix A · Publications</h2>',
           '<p class="note">Newest first within each group. * marks the corresponding author.</p>']
    for key, label in PUB_GROUPS:
        group = newest_first(r for r in pubs if str(r.get("type", "")).strip().lower() == key)
        if not group:
            continue
        out.append(f"<h3>{label} ({len(group)})</h3><ol class=\"pubs\">")
        for position, r in enumerate(group):
            url = clean_url(str(r.get("url", "")).strip())
            doi = url.split("doi.org/", 1)[1] if "doi.org/" in url else ""
            link = _link(url, f"doi:{doi}" if doi else None)
            out.append(
                f'<li><span class="num">{len(group) - position}.</span><span class="cit">{_authors_html(r.get("authors", ""))}. '
                f'{_e(r.get("title", ""))}. <span class="jr">{_e(r.get("journal", ""))}</span>. '
                f'<span class="yr">{_e(r.get("year", ""))}.</span>'
                + (f' <span class="lnk">{link}</span>' if link else "")
                + "</span></li>"
            )
        out.append("</ol>")
    out.append("</section>")
    return "".join(out)


def _journals(data) -> str:
    names = [str(r.get("name", "")).strip() for r in _rows(data.get("journals")) if str(r.get("name", "")).strip()]
    if not names:
        return ""
    body = "".join(f"<div>{_e(n)}</div>" for n in names)
    return f'<section class="appendix"><h2>Appendix B · Journals Reviewed ({len(names)})</h2><div class="cols">{body}</div></section>'


def _presentations(data) -> str:
    rows = newest_first(_rows(data.get("presentations")))
    if not rows:
        return ""
    items = []
    for position, r in enumerate(rows):
        when = " ".join(x for x in (str(r.get("month", "")).strip(), str(r.get("year", "")).strip()) if x)
        presenter = str(r.get("presenter", "")).strip()
        venue = "; ".join(x for x in (str(r.get("venue", "")).strip(), str(r.get("location", "")).strip()) if x)
        items.append(
            f'<li><span class="num">{len(rows) - position}.</span><span class="cit">{_e(r.get("title", ""))}. '
            f'<span class="jr">{_e(venue)}</span>. <span class="yr">{_e(when)} · {_e(str(r.get("type", "")).capitalize())}'
            + (f" · presented by {_e(presenter)}" if presenter else "")
            + ".</span></span></li>"
        )
    return (
        f'<section class="appendix"><h2>Appendix C · Presentations ({len(rows)})</h2>'
        f'<ol class="pubs">{"".join(items)}</ol></section>'
    )


def build_html(data) -> str:
    profile = get_profile(data)
    pubs = _rows(data.get("publications"))
    name = profile.get("name", "Reza Shahriarirad, M.D.")
    body = "".join([
        _header(profile), _summary(profile), _metrics(profile, pubs), _experience(data), _education(data),
        _mayo(profile), _awards(data), _grants(data), _invited_talks(data), _patents(data), _leadership(data), _editorial(data, profile),
        _skills(data, profile), _references(data), _publications(pubs), _journals(data), _presentations(data),
    ])
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{_e(name)} — Curriculum Vitae</title>"
        f'<meta name="author" content="{_e(name)}">'
        '<meta name="keywords" content="surgical innovation, surgical AI, computer vision, Mayo Clinic">'
        f"<style>{_font_css()}{CSS}</style></head><body>{body}</body></html>"
    )


def render(data=None, out: pathlib.Path = OUT) -> int:
    """Write the CV PDF and return its page count."""
    from weasyprint import HTML

    source = build_html(data or load_all_data())
    document = HTML(string=source, base_url=str(ROOT)).render()
    write_stable_pdf(document, out, source)
    return len(document.pages)


def main():
    pages = render()
    if not OUT.exists() or OUT.stat().st_size == 0:
        raise RuntimeError("WeasyPrint finished without creating Shahriarirad_Reza_CV.pdf")
    META.write_text(
        json.dumps({"generated": True, "method": METHOD, "source": "data/*.csv", "output": OUT.name, "pages": pages}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  Generated {OUT.name} ({OUT.stat().st_size:,} bytes, {pages} pages)")


if __name__ == "__main__":
    main()
