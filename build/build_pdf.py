"""
build_pdf.py — generate Shahriarirad_Reza_CV.pdf using WeasyPrint.
Single-column A4 academic layout. No appendices.
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import load_all_data, get_profile, parse_semicolon

ROOT = pathlib.Path(__file__).parent.parent
OUT  = ROOT / "Shahriarirad_Reza_CV.pdf"


def _e(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"','&quot;')


def build_html(data, profile) -> str:
    pubs_df      = data["publications"]
    pres_df      = data["presentations"]
    edu_df       = data["education"]
    exp_df       = data["experience"]
    leadership_df= data["leadership"]
    awards_df    = data["awards"]
    patents_df   = data["patents"]
    editorial_df = data["editorial"]
    skills_comp  = data["skills_computing"]
    skills_inter = data["skills_interpersonal"]
    refs_df      = data["references"]
    hobbies_df   = data["hobbies"]

    # ── header photo ──────────────────────────────────────────────────────
    photo_b64 = (pathlib.Path(__file__).parent / "static_assets" / "headshot.b64").read_text(encoding="ascii").strip()

    # ── CSS ───────────────────────────────────────────────────────────────
    css = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap');
@page { size: A4; margin: 2cm; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Arial, sans-serif; font-size: 10pt; color: #1a2740; line-height: 1.55; }

/* header */
.cv-header { display: flex; align-items: flex-start; gap: 1.2cm; margin-bottom: 0.8cm; border-bottom: 2px solid #1F3864; padding-bottom: 0.5cm; }
.cv-photo { width: 2.5cm; height: 2.5cm; border-radius: 50%; object-fit: cover; object-position: center top; flex-shrink: 0; }
.cv-name { font-family: 'Cormorant Garamond', serif; font-size: 22pt; font-weight: 600; color: #1F3864; line-height: 1.1; }
.cv-title { font-size: 9pt; color: #6b84a0; margin-top: 0.15cm; }
.cv-contact-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.1cm 0.5cm; margin-top: 0.2cm; font-size: 8pt; color: #3d526b; }

/* section */
.section { margin-bottom: 0.6cm; page-break-inside: avoid; }
.section-title { font-family: 'Cormorant Garamond', serif; font-size: 12pt; font-weight: 600; color: #1F3864; border-bottom: 1px solid #1F3864; padding-bottom: 2pt; margin-bottom: 0.3cm; text-transform: uppercase; letter-spacing: .06em; }

/* entry */
.entry { margin-bottom: 0.35cm; }
.entry-header { display: flex; gap: 0.3cm; align-items: baseline; }
.entry-period { font-size: 8pt; color: #1F3864; font-weight: bold; white-space: nowrap; min-width: 2.2cm; }
.entry-title { font-weight: bold; font-size: 10pt; }
.entry-sub { font-size: 8.5pt; color: #6b84a0; margin-left: 2.5cm; margin-top: 1pt; }
.entry-desc { font-size: 8.5pt; color: #3d526b; margin-left: 2.5cm; margin-top: 2pt; line-height: 1.5; }

/* metrics table */
.metrics-table { width: 100%; border-collapse: collapse; margin-bottom: 0.4cm; }
.metrics-table th { background: #1F3864; color: #fff; font-size: 7.5pt; padding: 3pt 5pt; text-align: center; }
.metrics-table td { border: 1pt solid #c8d4e0; font-size: 10pt; font-weight: bold; color: #1F3864; padding: 4pt 5pt; text-align: center; }

/* reference card */
.ref-item { margin-bottom: 0.3cm; }
.ref-name { font-weight: bold; font-size: 9.5pt; }
.ref-role { font-size: 8pt; color: #3d526b; }
.ref-inst { font-size: 8pt; color: #6b84a0; font-style: italic; }

/* skills */
.skills-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.3cm; }
.skill-item { font-size: 9pt; border-bottom: 0.5pt solid #e8f0f7; padding: 2pt 0; display: flex; justify-content: space-between; }
.skill-level { color: #6b84a0; font-size: 8pt; }

/* two-col layout for awards */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 0.4cm; }
.award-card { border-left: 3pt solid #b8953a; padding-left: 0.3cm; }
.award-year { font-size: 8pt; color: #b8953a; font-weight: bold; }
.award-title { font-size: 9.5pt; font-weight: bold; }
.award-org { font-size: 8pt; color: #6b84a0; }

/* presentations */
.pres-item { display: flex; gap: 0.3cm; margin-bottom: 0.25cm; font-size: 9pt; }
.pres-date { min-width: 1.5cm; font-size: 8pt; color: #1F3864; font-weight: bold; }
.pres-type-tag { display: inline-block; font-size: 7pt; padding: 1pt 4pt; border-radius: 2pt; background: #e8f0f7; color: #4a607e; }
"""

    # ── metrics ───────────────────────────────────────────────────────────
    def metrics_html():
        first_auth = sum(1 for _, r in pubs_df.iterrows() if "first" in parse_semicolon(r.get("tags","")))
        co_first   = sum(1 for _, r in pubs_df.iterrows() if "co-first" in parse_semicolon(r.get("tags","")))
        last_auth  = sum(1 for _, r in pubs_df.iterrows() if "last" in parse_semicolon(r.get("tags","")))
        corr_auth  = sum(1 for _, r in pubs_df.iterrows() if "corresponding" in parse_semicolon(r.get("tags","")))
        cols = ["Total", "H-Index", "Citations", "1st Author", "Co-First", "Last Author", "Corresponding", "Peer Reviews"]
        vals = [len(pubs_df), profile.get("h_index_cached","24"), profile.get("citations_cached","3248"),
                first_auth, co_first, last_auth, corr_auth, profile.get("peer_reviews","149")]
        ths = "".join(f"<th>{_e(c)}</th>" for c in cols)
        tds = "".join(f"<td>{_e(v)}</td>" for v in vals)
        return f'<table class="metrics-table"><tr>{ths}</tr><tr>{tds}</tr></table>'

    # ── education HTML ────────────────────────────────────────────────────
    def edu_html():
        out = ""
        for _, r in edu_df.iterrows():
            out += f"""<div class="entry">
  <div class="entry-header"><span class="entry-period">{_e(r['period'])}</span><span class="entry-title">{_e(r['degree'])}</span></div>
  <div class="entry-sub">{_e(r['org'])}</div>
</div>"""
        return out

    # ── experience HTML ───────────────────────────────────────────────────
    def exp_html():
        out = ""
        for _, r in exp_df.iterrows():
            desc = f'<div class="entry-desc">{_e(r["desc"])}</div>' if r.get("desc","").strip() else ""
            out += f"""<div class="entry">
  <div class="entry-header"><span class="entry-period">{_e(r['period'])}</span><span class="entry-title">{_e(r['role'])}</span></div>
  <div class="entry-sub">{_e(r['org'])}</div>{desc}
</div>"""
        return out

    # ── leadership HTML ───────────────────────────────────────────────────
    def leadership_html():
        out = ""
        for _, r in leadership_df.iterrows():
            out += f"""<div class="entry">
  <div class="entry-header"><span class="entry-period">{_e(r['period'])}</span><span class="entry-title">{_e(r['title'])}</span></div>
  <div class="entry-sub">{_e(r['org'])}</div>
  <div class="entry-desc">{_e(r['desc'])}</div>
</div>"""
        return out

    # ── awards HTML ───────────────────────────────────────────────────────
    def awards_html():
        cards = ""
        for _, r in awards_df.iterrows():
            cards += f"""<div class="award-card">
  <div class="award-year">{_e(r['year'])}</div>
  <div class="award-title">{_e(r['title'])}</div>
  <div class="award-org">{_e(r['org'])}</div>
</div>"""
        return f'<div class="two-col">{cards}</div>'

    # ── patents HTML ──────────────────────────────────────────────────────
    def patents_html():
        out = ""
        for _, r in patents_df.iterrows():
            out += f"""<div class="entry">
  <div class="entry-header"><span class="entry-period">{_e(r['date'])}</span><span class="entry-title">{_e(r['title'])}</span></div>
  <div class="entry-sub">Issuer: {_e(r['issuer'])} · Reg. No. {_e(r['number'])}</div>
</div>"""
        return out

    # ── editorial HTML ────────────────────────────────────────────────────
    def editorial_html():
        out = ""
        for _, r in editorial_df.iterrows():
            out += f"""<div class="entry">
  <div class="entry-header"><span class="entry-period">{_e(r['period'])}</span><span class="entry-title">{_e(r['role'])}</span></div>
  <div class="entry-sub">{_e(r['journal'])}</div>
</div>"""
        out += f'<p style="font-size:9pt;margin-top:4pt">Reviewer: <strong>{_e(profile.get("peer_reviews","149"))}</strong> peer reviews · <strong>{_e(profile.get("manuscripts_reviewed","129"))}</strong> manuscripts · <strong>{_e(profile.get("journals_reviewed","67"))}</strong> journals</p>'
        return out

    # ── presentations HTML ────────────────────────────────────────────────
    def pres_html():
        out = ""
        for _, r in pres_df.iterrows():
            type_cls = r.get("type","poster").lower()
            out += f"""<div class="pres-item">
  <span class="pres-date">{_e(r.get('date',''))}</span>
  <div>
    <span class="pres-type-tag">{type_cls.capitalize()}</span>
    <strong style="font-size:9pt"> {_e(r.get('title',''))}</strong><br>
    <span style="font-size:8pt;color:#6b84a0">{_e(r.get('venue',''))} · {_e(r.get('location',''))}</span>
  </div>
</div>"""
        return out

    # ── skills HTML ───────────────────────────────────────────────────────
    def skills_html():
        comp_items = "".join(
            f'<div class="skill-item"><span>{_e(r["name"])}</span><span class="skill-level">{_e(r["level"])}</span></div>'
            for _, r in skills_comp.iterrows()
        )
        inter_items = "".join(
            f'<div class="skill-item">{_e(r["name"])}</div>'
            for _, r in skills_inter.iterrows()
        )
        return f'<div class="skills-grid"><div><strong>Computing</strong>{comp_items}</div><div><strong>Interpersonal</strong>{inter_items}</div></div>'

    # ── references HTML ───────────────────────────────────────────────────
    def refs_html():
        pairs = [list(refs_df.iterrows())[i:i+2] for i in range(0, len(refs_df), 2)]
        out = '<div class="two-col">'
        for pair in pairs:
            for _, r in pair:
                out += f"""<div class="ref-item">
  <div class="ref-name">{_e(r['name'])}</div>
  <div class="ref-role">{_e(r['role'])}</div>
  <div class="ref-inst">{_e(r['inst'])}</div>
</div>"""
        out += "</div>"
        return out

    # ── languages & hobbies ───────────────────────────────────────────────
    lang_str   = profile.get("languages","")
    hobbies_str= "  ·  ".join(r["name"] for _, r in hobbies_df.iterrows())

    # ── assemble full HTML ─────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>{css}</style>
</head>
<body>

<div class="cv-header">
  <img class="cv-photo" src="data:image/jpeg;base64,{photo_b64}" alt="Dr. Shahriarirad">
  <div>
    <div class="cv-name">{_e(profile.get('name',''))}</div>
    <div class="cv-title">{_e(profile.get('title',''))} · {_e(profile.get('institution',''))} · {_e(profile.get('city_state',''))}</div>
    <div class="cv-contact-grid">
      <span>Phone: {_e(profile.get('phone',''))}</span>
      <span>ORCID: {_e(profile.get('orcid',''))}</span>
      <span>Email: {_e(profile.get('email_personal',''))}</span>
      <span>LinkedIn: {_e(profile.get('linkedin_url',''))}</span>
    </div>
  </div>
</div>

<div class="section"><div class="section-title">Education</div>{edu_html()}</div>
<div class="section"><div class="section-title">Professional Experience</div>{exp_html()}</div>
<div class="section"><div class="section-title">Leadership</div>{leadership_html()}</div>
<div class="section"><div class="section-title">Publications & Impact</div>{metrics_html()}</div>
<div class="section"><div class="section-title">Awards & Honours</div>{awards_html()}</div>
<div class="section"><div class="section-title">Patents</div>{patents_html()}</div>
<div class="section"><div class="section-title">Editorial & Reviewer Activity</div>{editorial_html()}</div>
<div class="section"><div class="section-title">Presentations</div>{pres_html()}</div>
<div class="section"><div class="section-title">Skills</div>{skills_html()}</div>
<div class="section"><div class="section-title">Languages & Interests</div>
  <p style="font-size:9pt"><strong>Languages:</strong> {_e(lang_str)}</p>
  <p style="font-size:9pt;margin-top:3pt"><strong>Interests:</strong> {_e(hobbies_str)}</p>
</div>
<div class="section"><div class="section-title">Professional References</div>{refs_html()}</div>

</body></html>"""


def main():
    from weasyprint import HTML, CSS
    data    = load_all_data()
    profile = get_profile(data)
    html_str = build_html(data, profile)
    HTML(string=html_str, base_url=str(ROOT)).write_pdf(str(OUT))
    print(f"  Generated {OUT.relative_to(ROOT)}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
