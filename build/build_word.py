"""
build_word.py — generate Shahriarirad_Reza_CV.docx using python-docx.
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import load_all_data, get_profile, parse_semicolon

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re

ROOT = pathlib.Path(__file__).parent.parent
OUT  = ROOT / "Shahriarirad_Reza_CV.docx"

NAVY   = RGBColor(0x1F, 0x38, 0x64)
GOLD   = RGBColor(0xB8, 0x95, 0x3A)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
DARK   = RGBColor(0x1A, 0x27, 0x40)
GRAY   = RGBColor(0x6B, 0x84, 0xA0)

FONT   = "Arial"


# ── helpers ────────────────────────────────────────────────────────────────

def _set_font(run, size=10, bold=False, italic=False, color=None):
    run.font.name  = FONT
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color


def _add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12 if level == 1 else 6)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text.upper() if level == 1 else text)
    _set_font(run, size=11 if level == 1 else 10, bold=True, color=NAVY)
    # Add bottom border
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1F3864")
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def _add_body(doc, text, size=10, italic=False, color=None, space_after=2):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    _set_font(run, size=size, italic=italic, color=color)
    return p


def _bold_shahriarirad(p, authors_str):
    """Add an authors paragraph with Shahriarirad R in bold."""
    p.paragraph_format.space_after = Pt(1)
    pattern = r"(Shahriarirad R\*?)"
    parts = re.split(pattern, str(authors_str))
    for part in parts:
        run = p.add_run(part)
        _set_font(run, size=9, bold=bool(re.match(pattern, part)))


def _cell_shade(cell, fill_hex):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  fill_hex)
    tcPr.append(shd)


def _set_col_width(table, col_idx, width_inches):
    for row in table.rows:
        row.cells[col_idx].width = Inches(width_inches)


# ── section builders ───────────────────────────────────────────────────────

def _section_contact(doc, profile):
    _add_heading(doc, "Contact Information")
    tbl = doc.add_table(rows=5, cols=2)
    tbl.style = "Table Grid"
    pairs = [
        ("Phone",    profile.get("phone","")),
        ("Email",    f'{profile.get("email_personal","")}  |  {profile.get("email_professional","")}'),
        ("Location", f'{profile.get("city_state","")}, USA'),
        ("ORCID",    profile.get("orcid","")),
        ("LinkedIn", profile.get("linkedin_url","")),
    ]
    for i, (k, v) in enumerate(pairs):
        r = tbl.rows[i]
        r.cells[0].text = k
        r.cells[1].text = v
        for j, cell in enumerate(r.cells):
            for para in cell.paragraphs:
                for run in para.runs:
                    _set_font(run, size=9, bold=(j == 0))
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    doc.add_paragraph()


def _section_education(doc, edu_df):
    _add_heading(doc, "Education")
    for _, r in edu_df.iterrows():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        period_run = p.add_run(f"{r['period']}  ")
        _set_font(period_run, size=9, bold=True, color=NAVY)
        deg_run = p.add_run(r["degree"])
        _set_font(deg_run, size=10, bold=True)
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(6)
        p2.paragraph_format.left_indent = Inches(0.2)
        run2 = p2.add_run(r["org"])
        _set_font(run2, size=9, color=GRAY)


def _section_experience(doc, exp_df):
    _add_heading(doc, "Professional Experience")
    for _, r in exp_df.iterrows():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        period_run = p.add_run(f"{r['period']}  ")
        _set_font(period_run, size=9, bold=True, color=NAVY)
        role_run = p.add_run(r["role"])
        _set_font(role_run, size=10, bold=True)
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(2)
        p2.paragraph_format.left_indent = Inches(0.2)
        org_run = p2.add_run(r["org"])
        _set_font(org_run, size=9, color=GRAY)
        if r.get("desc","").strip():
            p3 = doc.add_paragraph()
            p3.paragraph_format.space_after  = Pt(6)
            p3.paragraph_format.left_indent  = Inches(0.2)
            desc_run = p3.add_run(r["desc"])
            _set_font(desc_run, size=9, italic=True, color=GRAY)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)


def _section_leadership(doc, leadership_df):
    _add_heading(doc, "Leadership & Community Service")
    for _, r in leadership_df.iterrows():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        period_run = p.add_run(f"{r['period']}  ")
        _set_font(period_run, size=9, bold=True, color=NAVY)
        title_run = p.add_run(r["title"])
        _set_font(title_run, size=10, bold=True)
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(2)
        p2.paragraph_format.left_indent = Inches(0.2)
        org_run = p2.add_run(r["org"])
        _set_font(org_run, size=9, color=GRAY)
        if r.get("desc","").strip():
            p3 = doc.add_paragraph()
            p3.paragraph_format.space_after = Pt(6)
            p3.paragraph_format.left_indent = Inches(0.2)
            desc_run = p3.add_run(r["desc"])
            _set_font(desc_run, size=9)


def _section_pub_metrics(doc, profile, pubs_df):
    _add_heading(doc, "Publications & Impact Metrics")
    first_auth = sum(1 for _, r in pubs_df.iterrows() if "first" in parse_semicolon(r.get("tags","")))
    co_first   = sum(1 for _, r in pubs_df.iterrows() if "co-first" in parse_semicolon(r.get("tags","")))
    last_auth  = sum(1 for _, r in pubs_df.iterrows() if "last" in parse_semicolon(r.get("tags","")))
    corr_auth  = sum(1 for _, r in pubs_df.iterrows() if "corresponding" in parse_semicolon(r.get("tags","")))

    headers = ["Total Pubs", "H-Index", "Citations", "1st Author", "Co-First", "Last Author", "Corresponding", "Peer Reviews"]
    values  = [
        str(len(pubs_df)),
        profile.get("h_index_cached","24"),
        profile.get("citations_cached","3248"),
        str(first_auth),
        str(co_first),
        str(last_auth),
        str(corr_auth),
        profile.get("peer_reviews","149"),
    ]
    tbl = doc.add_table(rows=2, cols=len(headers))
    tbl.style = "Table Grid"
    for i, (h, v) in enumerate(zip(headers, values)):
        hcell = tbl.rows[0].cells[i]
        hcell.text = h
        _cell_shade(hcell, "1F3864")
        for para in hcell.paragraphs:
            for run in para.runs:
                _set_font(run, size=8, bold=True, color=WHITE)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        vcell = tbl.rows[1].cells[i]
        vcell.text = v
        for para in vcell.paragraphs:
            for run in para.runs:
                _set_font(run, size=10, bold=True, color=NAVY)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    doc.add_paragraph()


def _section_awards(doc, awards_df):
    _add_heading(doc, "Awards & Honours")
    for _, r in awards_df.iterrows():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        yr_run = p.add_run(f"{r['year']}  ")
        _set_font(yr_run, size=9, bold=True, color=NAVY)
        title_run = p.add_run(r["title"])
        _set_font(title_run, size=10, bold=True)
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(6)
        p2.paragraph_format.left_indent = Inches(0.2)
        org_run = p2.add_run(r["org"])
        _set_font(org_run, size=9, color=GRAY)


def _section_patents(doc, patents_df):
    _add_heading(doc, "Patents & Innovations")
    for _, r in patents_df.iterrows():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        date_run = p.add_run(f"{r['date']}  ")
        _set_font(date_run, size=9, bold=True, color=NAVY)
        title_run = p.add_run(r["title"])
        _set_font(title_run, size=10, bold=True)
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(6)
        p2.paragraph_format.left_indent = Inches(0.2)
        id_run = p2.add_run(f"Issuer: {r['issuer']}  ·  Registration No. {r['number']}")
        _set_font(id_run, size=9, color=GRAY)


def _section_editorial(doc, editorial_df, profile):
    _add_heading(doc, "Editorial & Reviewer Activity")
    _add_body(doc, "Editorial Roles", size=10, color=NAVY)
    for _, r in editorial_df.iterrows():
        url = r.get("url","").strip()
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.2)
        role_run = p.add_run(f"{r['role']} — ")
        _set_font(role_run, size=9, bold=True)
        journal_run = p.add_run(r["journal"])
        _set_font(journal_run, size=9, italic=True)
        per_run = p.add_run(f"  ({r['period']})")
        _set_font(per_run, size=9, color=GRAY)
    doc.add_paragraph()
    stats_p = doc.add_paragraph()
    stats_p.paragraph_format.space_after = Pt(4)
    pr_run = stats_p.add_run(f"Reviewer Stats:  {profile.get('peer_reviews','149')} peer reviews · {profile.get('manuscripts_reviewed','129')} manuscripts · {profile.get('journals_reviewed','67')} journals")
    _set_font(pr_run, size=9)


def _section_presentations(doc, pres_df):
    _add_heading(doc, "Presentations")
    for _, r in pres_df.iterrows():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        date_run = p.add_run(f"[{r.get('date','')}]  ")
        _set_font(date_run, size=9, bold=True, color=NAVY)
        type_run = p.add_run(f"[{r.get('type','').capitalize()}]  ")
        _set_font(type_run, size=9, color=GRAY)
        title_run = p.add_run(r.get("title",""))
        _set_font(title_run, size=9, bold=True)
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(5)
        p2.paragraph_format.left_indent = Inches(0.2)
        venue_run = p2.add_run(f'{r.get("venue","")}  |  {r.get("location","")}')
        _set_font(venue_run, size=8, italic=True, color=GRAY)


def _section_skills(doc, skills_comp_df, skills_inter_df):
    _add_heading(doc, "Skills")
    tbl = doc.add_table(rows=1, cols=2)
    tbl.style = "Table Grid"
    # Computing
    cell_c = tbl.rows[0].cells[0]
    cell_c.paragraphs[0].add_run("Computing").bold = True
    for _, r in skills_comp_df.iterrows():
        p = cell_c.add_paragraph()
        run = p.add_run(f"  {r['name']}")
        _set_font(run, size=9)
        if r.get("level","").strip():
            lvl = p.add_run(f"  ({r['level']})")
            _set_font(lvl, size=8, color=GRAY)
    # Interpersonal
    cell_i = tbl.rows[0].cells[1]
    cell_i.paragraphs[0].add_run("Interpersonal").bold = True
    for _, r in skills_inter_df.iterrows():
        p = cell_i.add_paragraph()
        run = p.add_run(f"  {r['name']}")
        _set_font(run, size=9)
    doc.add_paragraph()


def _section_languages_hobbies(doc, profile, hobbies_df):
    _add_heading(doc, "Languages & Interests")
    p = doc.add_paragraph()
    langs_run = p.add_run("Languages: ")
    _set_font(langs_run, size=9, bold=True)
    val_run = p.add_run(profile.get("languages","English (Fluent) · Farsi (Native)"))
    _set_font(val_run, size=9)
    p2 = doc.add_paragraph()
    hob_run = p2.add_run("Interests: ")
    _set_font(hob_run, size=9, bold=True)
    hobbies_str = "  ·  ".join(r["name"] for _, r in hobbies_df.iterrows())
    val2 = p2.add_run(hobbies_str)
    _set_font(val2, size=9)


def _section_references(doc, refs_df):
    _add_heading(doc, "Professional References")
    for _, r in refs_df.iterrows():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        name_run = p.add_run(r["name"])
        _set_font(name_run, size=10, bold=True)
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(1)
        p2.paragraph_format.left_indent = Inches(0.2)
        role_run = p2.add_run(r["role"])
        _set_font(role_run, size=9)
        p3 = doc.add_paragraph()
        p3.paragraph_format.space_after = Pt(6)
        p3.paragraph_format.left_indent = Inches(0.2)
        inst_run = p3.add_run(r["inst"])
        _set_font(inst_run, size=8, italic=True, color=GRAY)


# ── appendices ─────────────────────────────────────────────────────────────

def _appendix_pubs(doc, pubs_df):
    doc.add_page_break()
    h = doc.add_paragraph()
    hr = h.add_run("APPENDIX A — Complete Publication List")
    _set_font(hr, size=12, bold=True, color=NAVY)

    type_order = [("original","Original Articles"), ("review","Reviews & Meta-analyses"),
                  ("case","Case Reports"), ("letter","Letters / Editorials")]
    for type_key, type_label in type_order:
        subset = pubs_df[pubs_df["type"] == type_key]
        if subset.empty:
            continue
        h2 = doc.add_paragraph()
        h2r = h2.add_run(type_label)
        _set_font(h2r, size=10, bold=True, color=NAVY)
        h2.paragraph_format.space_before = Pt(8)

        for _, r in subset.iterrows():
            p = doc.add_paragraph()
            p.paragraph_format.space_after  = Pt(2)
            p.paragraph_format.left_indent  = Inches(0.3)
            p.paragraph_format.first_line_indent = Inches(-0.3)
            num_run = p.add_run(f"{r.get('n','')}. ")
            _set_font(num_run, size=9, bold=True, color=NAVY)
            _bold_shahriarirad(p, r.get("authors",""))
            title_run = p.add_run(f" {r.get('title','')}. ")
            _set_font(title_run, size=9)
            journal_run = p.add_run(r.get("journal",""))
            _set_font(journal_run, size=9, italic=True)
            year_run = p.add_run(f" ({r.get('year','')})")
            _set_font(year_run, size=9, color=GRAY)


def _appendix_journals(doc, journals_df):
    doc.add_page_break()
    h = doc.add_paragraph()
    hr = h.add_run("APPENDIX B — Journals Reviewed")
    _set_font(hr, size=12, bold=True, color=NAVY)

    tbl = doc.add_table(rows=0, cols=2)
    tbl.style = "Table Grid"
    names = list(journals_df["name"])
    half  = (len(names) + 1) // 2
    for i in range(half):
        row = tbl.add_row()
        left_name  = names[i]              if i < len(names)      else ""
        right_name = names[i + half]       if i + half < len(names) else ""
        row.cells[0].text = left_name
        row.cells[1].text = right_name
        for cell in row.cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    _set_font(run, size=8)


def _appendix_presentations(doc, pres_df):
    doc.add_page_break()
    h = doc.add_paragraph()
    hr = h.add_run("APPENDIX C — Presentations")
    _set_font(hr, size=12, bold=True, color=NAVY)

    for idx, (_, r) in enumerate(pres_df.iterrows(), start=1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after  = Pt(2)
        p.paragraph_format.left_indent  = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        num_run = p.add_run(f"{idx}. ")
        _set_font(num_run, size=9, bold=True, color=NAVY)
        title_run = p.add_run(f"{r.get('title','')}. ")
        _set_font(title_run, size=9, bold=True)
        venue_run = p.add_run(f"{r.get('venue','')}. {r.get('location','')}. {r.get('date','')}")
        _set_font(venue_run, size=9, italic=True, color=GRAY)
        type_run = p.add_run(f"  [{r.get('type','').capitalize()}]")
        _set_font(type_run, size=8, color=GRAY)


# ── main ───────────────────────────────────────────────────────────────────

def main():
    data    = load_all_data()
    profile = get_profile(data)

    doc = Document()

    # Page margins: 1 inch all sides
    for section in doc.sections:
        section.top_margin    = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin   = Inches(1)
        section.right_margin  = Inches(1)

    # Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_after = Pt(2)
    title_run = title_p.add_run(profile.get("name","Reza Shahriarirad, M.D."))
    _set_font(title_run, size=22, bold=True, color=NAVY)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(8)
    sub_run = sub_p.add_run(f'{profile.get("title","")}  ·  {profile.get("institution","")}  ·  {profile.get("city_state","")}')
    _set_font(sub_run, size=11, color=GRAY)

    _section_contact(doc,   profile)
    _section_education(doc, data["education"])
    _section_experience(doc, data["experience"])
    _section_leadership(doc, data["leadership"])
    _section_pub_metrics(doc, profile, data["publications"])
    _section_awards(doc,    data["awards"])
    _section_patents(doc,   data["patents"])
    _section_editorial(doc, data["editorial"], profile)
    _section_presentations(doc, data["presentations"])
    _section_skills(doc,    data["skills_computing"], data["skills_interpersonal"])
    _section_languages_hobbies(doc, profile, data["hobbies"])
    _section_references(doc, data["references"])

    # Appendices
    _appendix_pubs(doc,          data["publications"])
    _appendix_journals(doc,      data["journals"])
    _appendix_presentations(doc, data["presentations"])

    doc.save(OUT)
    print(f"  Generated {OUT.relative_to(ROOT)}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
