"""
build_html.py — regenerate index.html from /data/ CSVs + build/static_assets/.
Reads cv_style.css and cv_script.js verbatim; all dynamic content comes from CSVs.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import load_all_data, get_profile, format_authors_html, parse_semicolon, TAXONOMY

ROOT    = pathlib.Path(__file__).parent.parent
ASSETS  = pathlib.Path(__file__).parent / "static_assets"
OUT     = ROOT / "index.html"


# ── helpers ────────────────────────────────────────────────────────────────

def _e(s):
    """HTML-escape."""
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"','&quot;')

def _q(s):
    """JSON-safe single-quoted JS string (escape backslash and single-quote)."""
    return str(s).replace("\\","\\\\").replace("'","\\'")


# ── section generators ─────────────────────────────────────────────────────

def _head(css: str, profile: dict) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reza Shahriarirad, M.D. — Academic CV</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400&display=swap" rel="stylesheet">
<style>
{css}
</style>
</head>
<body>"""


def _nav() -> str:
    return """
<!-- NAV -->
<nav>
  <div class="nav-logo">Reza Shahriarirad, M.D.</div>
  <ul class="nav-links">
    <li><a href="#about">About</a></li>
    <li><a href="#experience">Experience</a></li>
    <li><a href="#leadership">Leadership</a></li>
    <li><a href="#publications">Publications</a></li>
    <li><a href="#awards">Awards</a></li>
    <li><a href="#patents">Patents</a></li>
    <li><a href="#reviewer">Editorial</a></li>
    <li><a href="#presentations">Presentations</a></li>
    <li><a href="#opensource">Open Source</a></li>
    <li><a href="#hobbies">Interests</a></li>
    <li><a href="#references">References</a></li>
  </ul>
  <button class="hamburger" onclick="toggleMenu()"><span></span><span></span><span></span></button>
</nav>
<div class="mobile-menu" id="mobile-menu">
  <a href="#about" onclick="closeMenu()">About</a>
  <a href="#experience" onclick="closeMenu()">Experience</a>
  <a href="#leadership" onclick="closeMenu()">Leadership</a>
  <a href="#publications" onclick="closeMenu()">Publications</a>
  <a href="#awards" onclick="closeMenu()">Awards</a>
  <a href="#patents" onclick="closeMenu()">Patents</a>
  <a href="#reviewer" onclick="closeMenu()">Editorial</a>
  <a href="#presentations" onclick="closeMenu()">Presentations</a>
  <a href="#opensource" onclick="closeMenu()">Open Source</a>
  <a href="#hobbies" onclick="closeMenu()">Interests</a>
  <a href="#references" onclick="closeMenu()">References</a>
</div>"""


def _hero(profile: dict, pub_count: int, photo_b64: str) -> str:
    cites   = profile.get("citations_cached", "3248")
    hindex  = profile.get("h_index_cached",   "24")
    reviews = profile.get("peer_reviews",      "149")
    # format citations with comma
    try:
        cites_fmt = f"{int(cites):,}"
    except Exception:
        cites_fmt = cites
    return f"""
<!-- HERO -->
<div class="hero">
  <div class="hero-bg"></div>
  <div class="hero-grid"></div>
  <div class="hero-content">
    <div class="hero-left">
      <div class="hero-eyebrow">Physician · Researcher</div>
      <h1>Reza<br><span class="hero-title-accent">Shahriarirad,</span><br>M.D.</h1>
      <div class="hero-credentials">
        <strong>Research Fellow, Surgery Innovation Center</strong><br>
        Mayo Clinic · Rochester, Minnesota<br>
        ORCID: {_e(profile.get('orcid',''))}
      </div>
      <div class="hero-cta">
        <a href="#publications" class="btn-primary">View Publications</a>
        <a href="#" class="btn-outline cf-email" data-u="R.shahriari1995" data-d="gmail.com">Get in Touch</a>
        <a href="#" onclick="downloadCV();return false;" class="btn-pdf" title="Download updated CV as Word document">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
          Download CV
        </a>
      </div>
    </div>
    <div class="hero-right" style="display:flex;flex-direction:column;align-items:center">
      <div class="hero-photo-wrap">
        <img id="cv-headshot" class="hero-photo" src="data:image/jpeg;base64,{photo_b64}" alt="Dr. Reza Shahriarirad">
      </div>
      <div class="hero-stats" style="width:100%">
        <div class="stat-box">
          <div class="stat-num" id="hero-pubs">{pub_count}</div>
          <div class="stat-label">Publications</div>
        </div>
        <div class="stat-box">
          <div class="stat-num" id="hero-cites">{cites_fmt}<span class="live-dot" title="Updating…"></span></div>
          <div class="stat-label">Citations</div>
        </div>
        <div class="stat-box">
          <div class="stat-num" id="hero-hindex">{hindex}</div>
          <div class="stat-label">H-index</div>
        </div>
        <div class="stat-box">
          <div class="stat-num" id="hero-reviews">{reviews}</div>
          <div class="stat-label">Peer Reviews</div>
        </div>
      </div>
      <p style="font-size:.65rem;color:var(--silver);text-align:right;margin-top:.5rem;letter-spacing:.04em">Citations &amp; indices pulled live from Google Scholar <span class="live-dot"></span></p>
    </div>
  </div>
</div>"""


def _about(profile: dict) -> str:
    bio1 = profile.get("bio_paragraph_1", "")
    bio2 = profile.get("bio_paragraph_2", "")
    irb_count = profile.get("irb_count", "30")
    irb_desc  = profile.get("irb_description", "")
    # research tags
    tags_html = """          <div class="research-tag">Plastic &amp; Reconstructive Surgery</div>
          <div class="research-tag">Bariatric &amp; Abdominal Wall Reconstruction</div>
          <div class="research-tag">Thoracic Surgery</div>
          <div class="research-tag">Cardiac Surgery</div>
          <div class="research-tag">Oral &amp; Maxillofacial Surgery</div>
          <div class="research-tag">Gastrointestinal Surgery</div>
          <div class="research-tag">Trauma Surgery</div>
          <div class="research-tag">Surgical AI &amp; Innovation</div>"""
    email_p = profile.get("email_personal", "")
    # Split email for cloudflare obfuscation
    eu, ed = (email_p.split("@") + [""])[:2]
    email2_p = profile.get("email_professional", "")
    eu2, ed2 = (email2_p.split("@") + [""])[:2]
    loc = f"{profile.get('city_state','Rochester, MN')}, USA"
    langs = profile.get("languages", "English (Fluent) · Farsi (Native)")
    res_int = profile.get("research_interests","Surgery · Minimally Invasive Surgery · Artificial Intelligence")
    return f"""
<!-- ABOUT -->
<div id="about">
<div class="section-wrap">
  <div class="section-label">Profile</div>
  <h2>About</h2>
  <div class="about-grid">
    <div class="about-text">
      <p>{bio1}</p>
      <p>{bio2}</p>
      <div style="margin:1.8rem 0 0">
        <div class="section-label" style="margin-bottom:.8rem">Ongoing Research at Mayo Clinic</div>
        <p>Since joining the Surgery Innovation Center, Dr. Shahriarirad has been involved in over <strong>{irb_count} IRB-approved research projects</strong> spanning a broad range of surgical specialties. His work encompasses clinical trial design, translational device evaluation, surgical innovation, and multidisciplinary collaboration — including leading internal competitive proposal submissions and engaging with industry partners.</p>
        <div class="research-grid">
{tags_html}
        </div>
      </div>
      <div class="about-links">
        <a href="{_e(profile.get('scholar_url',''))}" target="_blank" class="profile-link">Google Scholar</a>
        <a href="{_e(profile.get('pubmed_url',''))}" target="_blank" class="profile-link">PubMed</a>
        <a href="{_e(profile.get('scopus_url',''))}" target="_blank" class="profile-link">Scopus</a>
        <a href="{_e(profile.get('researchgate_url',''))}" target="_blank" class="profile-link">ResearchGate</a>
        <a href="{_e(profile.get('wos_url',''))}" target="_blank" class="profile-link">Web of Science</a>
        <a href="{_e(profile.get('linkedin_url',''))}" target="_blank" class="profile-link">LinkedIn</a>
        <a href="{_e(profile.get('orcid_url',''))}" target="_blank" class="profile-link">ORCID</a>
        <a href="{_e(profile.get('github_url',''))}" target="_blank" class="profile-link">GitHub</a>
      </div>
    </div>
    <div>
      <div class="contact-block">
        <h3>Contact</h3>
        <div class="contact-item contact-item-multi"><span>Email</span><div class="contact-multi"><a href="#" class="cf-email" data-u="{_e(eu)}" data-d="{_e(ed)}">[loading]</a><a href="#" class="cf-email" data-u="{_e(eu2)}" data-d="{_e(ed2)}">[loading]</a></div></div>
        <div class="contact-item"><span>Phone</span><span>{_e(profile.get('phone',''))}</span></div>
        <div class="contact-item"><span>Location</span><span>{_e(loc)}</span></div>
        <div class="contact-item"><span>Research Interests</span><span>{_e(res_int)}</span></div>
        <div class="contact-item"><span>Languages</span><span>{_e(langs)}</span></div>
      </div>
    </div>
  </div>
</div>
</div>"""


def _experience(exp_df, edu_df, skills_comp_df, skills_inter_df) -> str:
    def timeline_item(row):
        logo = f'<div class="timeline-logo-placeholder" style="background:{_e(row.get("logo_color","#4a607e"))};color:#fff;font-size:.5rem;font-weight:700">{_e(row.get("logo_initials",""))}</div>'
        desc_html = f'\n          <div class="timeline-desc">{_e(row["desc"])}</div>' if row.get("desc","").strip() else ""
        return f"""        <div class="timeline-item">
          <div class="timeline-period">{_e(row["period"])}</div>
          <div class="timeline-header">
            {logo}
            <div>
              <div class="timeline-role">{_e(row["role"])}</div>
              <div class="timeline-org">{_e(row["org"])}</div>
            </div>
          </div>{desc_html}
        </div>"""

    def edu_item(row):
        logo = f'<div class="timeline-logo-placeholder" style="background:{_e(row.get("logo_color","#4a607e"))};color:#fff;font-size:.5rem;font-weight:700">{_e(row.get("logo_initials",""))}</div>'
        return f"""        <div class="timeline-item">
          <div class="timeline-period">{_e(row["period"])}</div>
          <div class="timeline-header">
            {logo}
            <div>
              <div class="timeline-role">{_e(row["degree"])}</div>
              <div class="timeline-org">{_e(row["org"])}</div>
            </div>
          </div>
        </div>"""

    exp_items  = "\n".join(timeline_item(r) for _, r in exp_df.iterrows())
    edu_items  = "\n".join(edu_item(r) for _, r in edu_df.iterrows())

    def _skill_name(r):
        url = str(r.get("url","")).strip()
        name = _e(r["name"])
        if url:
            return f'<a href="{_e(url)}" target="_blank">{name}</a>'
        return name

    comp_rows = "\n".join(
        f'          <div class="skill-item"><span>{_skill_name(r)}</span><span class="skill-level">{_e(r["level"])}</span></div>'
        for _, r in skills_comp_df.iterrows()
    )
    inter_rows = "\n".join(
        f'          <div class="skill-item">{_e(r["name"])}</div>'
        for _, r in skills_inter_df.iterrows()
    )

    return f"""
<!-- EXPERIENCE -->
<div class="section-alt" id="experience">
<div class="section-wrap">
  <div class="section-label">Career</div>
  <h2>Experience &amp; Education</h2>
  <div class="timeline-grid">
    <div>
      <div class="timeline-col"><h3>Professional Experience</h3></div>
      <div class="timeline">
{exp_items}
      </div>
    </div>
    <div>
      <div class="timeline-col"><h3>Education</h3></div>
      <div class="timeline">
{edu_items}
      </div>
      <div class="timeline-col" style="margin-top:2.5rem"><h3>Skills</h3></div>
      <div class="skills-grid" style="grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:.5rem">
        <div class="skill-group">
          <h3>Computing</h3>
{comp_rows}
        </div>
        <div class="skill-group">
          <h3>Interpersonal</h3>
{inter_rows}
        </div>
      </div>
    </div>
  </div>
</div>
</div>"""


def _leadership(leadership_df) -> str:
    cards = []
    for _, r in leadership_df.iterrows():
        cards.append(f"""  <div class="leadership-card">
    <div class="leadership-period">{_e(r["period"])}</div>
    <div class="leadership-title">{_e(r["title"])}</div>
    <div class="leadership-org">{_e(r["org"])}</div>
    <div class="leadership-desc">{_e(r["desc"])}</div>
  </div>""")
    return f"""
<!-- LEADERSHIP -->
<div id="leadership">
<div class="section-wrap">
  <div class="section-label">Leadership &amp; Service</div>
  <h2>Leadership &amp; Community Service</h2>
{''.join(cards)}
</div>
</div>"""


def _publications_section() -> str:
    """Static filter sidebar + JS-rendered list (data injected via JS array)."""
    return """
<!-- PUBLICATIONS -->
<div class="section-alt" id="publications">
<div class="section-wrap">
  <div class="section-label">Research Output</div>
  <h2>Publications</h2>

  <div class="pub-controls">
    <!-- Left: filter sidebar -->
    <div class="pub-filter-sidebar">
      <div class="pub-filter-group">
        <span class="pub-filter-group-label">Article Type</span>
        <button class="filter-btn active" onclick="filterPubs('all',this,'type')">All Types</button>
        <button class="filter-btn" onclick="filterPubs('original',this,'type')">Original Articles</button>
        <button class="filter-btn" onclick="filterPubs('review',this,'type')">Reviews &amp; Meta-analyses</button>
        <button class="filter-btn" onclick="filterPubs('case',this,'type')">Case Reports</button>
        <button class="filter-btn" onclick="filterPubs('letter',this,'type')">Letters / Editorials</button>
      </div>
      <div class="pub-filter-group">
        <span class="pub-filter-group-label">Authorship</span>
        <button class="filter-btn" onclick="filterPubs('first',this,'type')">1st Author</button>
        <button class="filter-btn" onclick="filterPubs('co-first',this,'type')">2nd / Co-first</button>
        <button class="filter-btn" onclick="filterPubs('corresponding',this,'type')">Corresponding</button>
        <button class="filter-btn" onclick="filterPubs('last',this,'type')">Last / Senior</button>
      </div>
      <div class="pub-filter-group">
        <span class="pub-filter-group-label">Topic</span>
        <button class="filter-btn active" onclick="filterPubs('all',this,'cat')" id="cat-all-btn">All Topics</button>
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" onclick="filterPubsMain(this)" data-group="surgery">
            <span>Surgery</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="grp-surgery" style="display:none">
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('plastic',this,'cat')" data-main="surgery">Plastic, Reconstructive &amp; Burns</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('thoracic',this,'cat')" data-main="surgery">Thoracic Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('vascular',this,'cat')" data-main="surgery">Vascular Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('gi',this,'cat')" data-main="surgery">GI &amp; Colorectal Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('endocrine',this,'cat')" data-main="surgery">Endocrine Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('ortho',this,'cat')" data-main="surgery">Orthopaedic Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('urosurg',this,'cat')" data-main="surgery">Urological Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('transplant',this,'cat')" data-main="surgery">Transplant Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('oncology',this,'cat')" data-main="surgery">Surgical Oncology</button>
          </div>
        </div>
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" onclick="filterPubsMain(this)" data-group="medicine">
            <span>Internal Medicine</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="grp-medicine" style="display:none">
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('infectious',this,'cat')" data-main="medicine">Infectious Disease</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('pulm',this,'cat')" data-main="medicine">Pulmonology</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('neuro',this,'cat')" data-main="medicine">Neurology</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('derm',this,'cat')" data-main="medicine">Dermatology</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('urology',this,'cat')" data-main="medicine">Urology</button>
          </div>
        </div>
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" onclick="filterPubsMain(this)" data-group="ai">
            <span>Artificial Intelligence</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="grp-ai" style="display:none">
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('ai',this,'cat')" data-main="ai">AI &amp; Machine Learning</button>
          </div>
        </div>
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" onclick="filterPubsMain(this)" data-group="pubhealth">
            <span>Public Health</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="grp-pubhealth" style="display:none">
            <button class="filter-btn filter-sub-btn" onclick="filterPubs('pubhealth',this,'cat')" data-main="pubhealth">Public Health &amp; Epidemiology</button>
          </div>
        </div>
      </div>
    </div>
    <!-- Right: search + list -->
    <div class="pub-list-wrap">
      <div style="display:flex;align-items:center;gap:.7rem;margin-bottom:1rem;flex-wrap:wrap">
        <input type="search" id="pub-search" placeholder="Search title, author, journal…"
          style="flex:1;min-width:180px;padding:.45rem .8rem;border:1px solid var(--mist);border-radius:3px;font-size:.82rem;font-family:'DM Sans',sans-serif;outline:none;background:var(--white);color:var(--text)"
          oninput="currentSearch=this.value;showingAll=false;renderPubs()">
        <div id="pub-count" style="font-size:.72rem;color:var(--text-muted);white-space:nowrap">—</div>
      </div>
  <div class="pub-list" id="pub-list"></div>
  </div><!-- /pub-list-wrap -->
  </div><!-- /pub-controls -->
  <p class="pub-note" style="font-size:.74rem;color:var(--text-muted);margin-bottom:1.5rem">* denotes corresponding author. My name is highlighted in bold.</p>
  <div style="text-align:center;padding:2rem 0 0" id="pub-more">
    <button class="btn-outline" onclick="showAllPubs()" style="border-color:var(--navy);color:var(--navy)">Show all publications</button>
  </div>
</div>
</div>"""


def _awards(awards_df) -> str:
    cards = []
    for _, r in awards_df.iterrows():
        url = r.get("url","").strip()
        title_html = (
            f'<a href="{_e(url)}" target="_blank" style="color:inherit;text-decoration:none">{_e(r["title"])} ↗</a>'
            if url else _e(r["title"])
        )
        cards.append(f"""    <div class="award-card">
      <div class="award-year">{_e(r["year"])}</div>
      <div class="award-title">{title_html}</div>
      <div class="award-org">{_e(r["org"])}</div>
    </div>""")
    return f"""
<!-- AWARDS -->
<div id="awards">
<div class="section-wrap">
  <div class="section-label">Recognition</div>
  <h2>Awards &amp; Honours</h2>
  <div class="awards-grid">
{''.join(cards)}
  </div>
</div>
</div>"""


def _patents(patents_df) -> str:
    items = []
    for _, r in patents_df.iterrows():
        items.append(f"""    <div class="patent-item">
      <div class="patent-date">{_e(r["date"])}</div>
      <div>
        <div class="patent-title">{_e(r["title"])}</div>
        <div class="patent-id">Issuer: {_e(r["issuer"])} &nbsp;·&nbsp; Registration No. {_e(r["number"])}</div>
      </div>
    </div>""")
    return f"""
<!-- PATENTS -->
<div class="section-alt" id="patents">
<div class="section-wrap">
  <div class="section-label">Innovation</div>
  <h2>Patents &amp; Innovations</h2>
  <div class="patent-list">
{''.join(items)}
  </div>
</div>
</div>"""


def _editorial(editorial_df, profile: dict) -> str:
    editor_items = []
    for _, r in editorial_df.iterrows():
        url = r.get("url","").strip()
        journal_html = (
            f'<a href="{_e(url)}" target="_blank">{_e(r["journal"])} ↗</a>'
            if url else _e(r["journal"])
        )
        editor_items.append(f"""      <div class="editor-item">
        <span class="editor-role">{_e(r["role"])}</span>
        <span class="editor-journal">{journal_html}</span>
        <span class="editor-period">{_e(r["period"])}</span>
      </div>""")
    peer_reviews  = profile.get("peer_reviews",       "149")
    manuscripts   = profile.get("manuscripts_reviewed","129")
    journals_cnt  = profile.get("journals_reviewed",   "67")
    return f"""
<!-- EDITORIAL / REVIEWER -->
<div id="reviewer">
<div class="section-wrap">
  <div class="section-label">Editorial Activity</div>
  <h2>Editor &amp; Reviewer Experience</h2>

  <div style="margin-bottom:2.5rem">
    <h3 style="font-family:'Cormorant Garamond',serif;font-size:1.2rem;font-weight:400;color:var(--text-mid);margin-bottom:1rem;padding-bottom:.5rem;border-bottom:1px solid var(--mist)">Editorial Roles</h3>
    <div class="editor-list">
{''.join(editor_items)}
    </div>
  </div>

  <div style="margin-bottom:2rem">
    <h3 style="font-family:'Cormorant Garamond',serif;font-size:1.2rem;font-weight:400;color:var(--text-mid);margin-bottom:1rem;padding-bottom:.5rem;border-bottom:1px solid var(--mist)">Reviewer Role</h3>
    <div class="reviewer-stats">
    <div><div class="reviewer-stat-num">{_e(peer_reviews)}</div><div class="reviewer-stat-label">Peer Reviews</div></div>
    <div><div class="reviewer-stat-num">{_e(manuscripts)}</div><div class="reviewer-stat-label">Manuscripts</div></div>
    <div><div class="reviewer-stat-num">{_e(journals_cnt)}</div><div class="reviewer-stat-label">Journals</div></div>
  </div>
  </div>

  <h3 style="font-family:'Cormorant Garamond',serif;font-size:1.2rem;font-weight:400;color:var(--text-mid);margin-bottom:1.2rem">Journals Reviewed</h3>
  <div class="journal-grid" id="journal-grid"></div>
</div>
</div>"""


def _presentations(pres_df) -> str:
    items = []
    for _, r in pres_df.iterrows():
        cats = parse_semicolon(r.get("cat",""))
        # deduplicate cats preserving order
        seen = set(); cats_u = [c for c in cats if not (c in seen or seen.add(c))]
        data_cats = ",".join(cats_u)
        type_cls  = r.get("type","poster").lower()
        type_lbl  = type_cls.capitalize()
        items.append(f"""    <div class="pres-item" data-type="{_e(type_cls)}" data-location="{_e(r.get('location',''))}" data-cats="{_e(data_cats)}">
      <div class="pres-date-col">
        <span class="pres-year-txt">{_e(r.get('date',''))}</span>
        <span class="pres-type {type_cls}">{type_lbl}</span>
      </div>
      <div>
        <div class="pres-title">{_e(r.get('title',''))}</div>
        <div class="pres-venue">{_e(r.get('venue',''))}</div>
        <div class="pres-location">{_e(r.get('location',''))}</div>
      </div>
    </div>""")
    return f"""
<!-- PRESENTATIONS -->
<div class="section-alt" id="presentations">
<div class="section-wrap">
  <div class="section-label">Academic Engagements</div>
  <h2>Presentations</h2>
  <div class="pres-controls">
    <!-- Left: filter sidebar -->
    <div class="pres-filter-sidebar">
      <div class="pres-filter-group">
        <span class="pub-filter-group-label">Reset</span>
        <button class="filter-btn active" id="pres-reset" onclick="resetPresFilters(this)">All Presentations</button>
      </div>
      <div class="pres-filter-group">
        <span class="pub-filter-group-label">Type</span>
        <button class="filter-btn" onclick="filterPres('type','poster',this)">Poster</button>
        <button class="filter-btn" onclick="filterPres('type','oral',this)">Oral</button>
      </div>
      <div class="pres-filter-group">
        <span class="pub-filter-group-label">Location</span>
        <button class="filter-btn" onclick="filterPres('location','Iran',this)">Iran</button>
        <button class="filter-btn" onclick="filterPres('location','Netherlands',this)">Netherlands</button>
        <button class="filter-btn" onclick="filterPres('location','Turkey',this)">Turkey</button>
        <button class="filter-btn" onclick="filterPres('location','United States',this)">United States</button>
      </div>
      <div class="pres-filter-group">
        <span class="pub-filter-group-label">Topic</span>
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" onclick="filterPresMain(this)" data-group="surgery">
            <span>Surgery</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="pgrp-surgery" style="display:none">
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','plastic',this)" data-main="surgery">Plastic, Reconstructive &amp; Burns</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','thoracic',this)" data-main="surgery">Thoracic Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','vascular',this)" data-main="surgery">Vascular Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','gi',this)" data-main="surgery">GI &amp; Colorectal Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','endocrine',this)" data-main="surgery">Endocrine Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','ortho',this)" data-main="surgery">Orthopaedic Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','urosurg',this)" data-main="surgery">Urological Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','transplant',this)" data-main="surgery">Transplant Surgery</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','oncology',this)" data-main="surgery">Surgical Oncology</button>
          </div>
        </div>
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" onclick="filterPresMain(this)" data-group="medicine">
            <span>Internal Medicine</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="pgrp-medicine" style="display:none">
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','infectious',this)" data-main="medicine">Infectious Disease</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','pulm',this)" data-main="medicine">Pulmonology</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','neuro',this)" data-main="medicine">Neurology</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','derm',this)" data-main="medicine">Dermatology</button>
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','urology',this)" data-main="medicine">Urology</button>
          </div>
        </div>
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" onclick="filterPresMain(this)" data-group="ai">
            <span>Artificial Intelligence</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="pgrp-ai" style="display:none">
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','ai',this)" data-main="ai">AI &amp; Machine Learning</button>
          </div>
        </div>
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" onclick="filterPresMain(this)" data-group="pubhealth">
            <span>Public Health</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="pgrp-pubhealth" style="display:none">
            <button class="filter-btn filter-sub-btn" onclick="filterPres('cat','pubhealth',this)" data-main="pubhealth">Public Health &amp; Epidemiology</button>
          </div>
        </div>
      </div>
    </div>
    <!-- Right: search + list -->
    <div class="pres-list-wrap">
      <div style="display:flex;align-items:center;gap:.7rem;margin-bottom:1rem;flex-wrap:wrap">
        <input type="search" id="pres-search" placeholder="Search title or conference…"
          style="flex:1;min-width:180px;padding:.45rem .8rem;border:1px solid var(--mist);border-radius:3px;font-size:.82rem;font-family:'DM Sans',sans-serif;outline:none;background:var(--white);color:var(--text)"
          oninput="filterPresSearch(this.value)">
        <div id="pres-count" style="font-size:.72rem;color:var(--text-muted);white-space:nowrap">{len(pres_df)} presentations</div>
      </div>
      <div class="pres-list" id="pres-list">
{''.join(items)}
      </div>
    </div>
  </div></div>
</div>
</div>"""


def _open_source(profile: dict) -> str:
    return f"""
<!-- OPEN SOURCE MODELS -->
<div id="opensource">
<div class="section-wrap">
  <div class="section-label">Open Science</div>
  <h2>Open Source Models &amp; Tools</h2>
  <p style="font-size:.9rem;color:var(--text-muted);margin-bottom:1.8rem;line-height:1.85;max-width:680px">Open-source computational tools, machine learning models, and research software developed as part of ongoing surgical AI and clinical research. All repositories are publicly available on GitHub.</p>
  <div class="repos-grid" id="repos-grid"></div>
</div>
</div>"""


def _hobbies(hobbies_df) -> str:
    cards = []
    for _, r in hobbies_df.iterrows():
        name_esc = _e(r["name"]).replace("&amp;", "&amp;")
        cards.append(f"""    <div class="hobby-card">
      <div class="hobby-icon">{r["icon"]}</div>
      <div><div class="hobby-name">{name_esc}</div><div class="hobby-desc">{_e(r["desc"])}</div></div>
    </div>""")
    return f"""
<!-- HOBBIES -->
<div class="section-alt" id="hobbies">
<div class="section-wrap">
  <div class="section-label">Personal</div>
  <h2>Extracurricular &amp; Interests</h2>
  <div class="hobbies-grid">
{''.join(cards)}
  </div>
</div>
</div>"""


def _references_section() -> str:
    return """
<!-- REFERENCES -->
<div id="references">
<div class="section-wrap">
  <div class="section-label">Professional Network</div>
  <h2>References</h2>
  <div class="refs-grid" id="refs-grid"></div>
</div>
</div>"""


def _footer(profile: dict) -> str:
    return f"""
<!-- FOOTER -->
<footer>
  <div class="footer-name">{_e(profile.get('name','Reza Shahriarirad, M.D.'))}</div>
  <div class="footer-note">{_e(profile.get('title','Research Fellow'))} · {_e(profile.get('institution','Surgery Innovation Center · Mayo Clinic'))} · {_e(profile.get('city_state','Rochester, MN'))}</div>
  <div class="footer-divider"></div>
  <div class="footer-links">
    <a href="{_e(profile.get('scholar_url',''))}" target="_blank">Google Scholar</a>
    <a href="{_e(profile.get('pubmed_url',''))}" target="_blank">PubMed</a>
    <a href="{_e(profile.get('orcid_url',''))}" target="_blank">ORCID</a>
    <a href="{_e(profile.get('researchgate_url',''))}" target="_blank">ResearchGate</a>
    <a href="{_e(profile.get('scopus_url',''))}" target="_blank">Scopus</a>
    <a href="{_e(profile.get('linkedin_url',''))}" target="_blank">LinkedIn</a>
  </div>
</footer>"""


# ── JS data generators ─────────────────────────────────────────────────────

def _pubs_js(pubs_df) -> str:
    entries = []
    for _, r in pubs_df.iterrows():
        tags = parse_semicolon(r.get("tags",""))
        cats = parse_semicolon(r.get("cat",""))
        tags_js = "[" + ",".join(f'"{_q(t)}"' for t in tags) + "]"
        cats_js = "[" + ",".join(f'"{_q(c)}"' for c in cats) + "]"
        n_val   = int(r.get("n",0)) if str(r.get("n","")).isdigit() else 0
        entries.append(
            f'{{n:{n_val},year:"{_q(r.get("year",""))}",type:"{_q(r.get("type",""))}",title:"{_q(r.get("title",""))}",authors:"{_q(r.get("authors",""))}",journal:"{_q(r.get("journal",""))}",url:"{_q(r.get("url",""))}",tags:{tags_js},cat:{cats_js}}}'
        )
    return "const pubs=[\n  " + ",\n  ".join(entries) + "\n];"


def _journals_js(journals_df) -> str:
    entries = []
    for _, r in journals_df.iterrows():
        url = r.get("url","").strip()
        if url:
            entries.append(f'{{name:"{_q(r["name"])}",url:"{_q(url)}"}}\n')
        else:
            entries.append(f'{{name:"{_q(r["name"])}"}}\n')
    return "const journals=[\n  " + "  ,".join(entries) + "];"


def _refs_js(refs_df) -> str:
    entries = []
    for _, r in refs_df.iterrows():
        links = []
        if r.get("link_label_1","").strip():
            links.append(f'{{label:"{_q(r["link_label_1"])}",url:"{_q(r.get("link_url_1",""))}"}}\n    ')
        if r.get("link_label_2","").strip():
            links.append(f'{{label:"{_q(r["link_label_2"])}",url:"{_q(r.get("link_url_2",""))}"}}\n    ')
        links_js = "[" + ",".join(l.strip() for l in links) + "]"
        entries.append(
            f'{{name:"{_q(r["name"])}",role:"{_q(r["role"])}",inst:"{_q(r["inst"])}",links:{links_js}}}'
        )
    return "const refs=[\n  " + ",\n  ".join(entries) + "\n];"


def _repos_js(repos_df) -> str:
    entries = []
    for _, r in repos_df.iterrows():
        entries.append(
            f'{{name:"{_q(r.get("name",""))}",language:"{_q(r.get("language",""))}",desc:"{_q(r.get("desc",""))}",url:"{_q(r.get("url",""))}",demo:"{_q(r.get("demo",""))}",paper:"{_q(r.get("paper",""))}",icon:"{_q(r.get("icon",""))}" }}'
        )
    if not entries:
        return "const openSourceRepos = [];"
    return "const openSourceRepos=[\n  " + ",\n  ".join(entries) + "\n];"


# ── main ───────────────────────────────────────────────────────────────────

def main():
    data    = load_all_data()
    profile = get_profile(data)

    css = (ASSETS / "cv_style.css").read_text(encoding="utf-8")
    js  = (ASSETS / "cv_script.js").read_text(encoding="utf-8")
    photo_b64 = (ASSETS / "headshot.b64").read_text(encoding="ascii").strip()

    pub_count = len(data["publications"])

    parts = [
        _head(css, profile),
        _nav(),
        _hero(profile, pub_count, photo_b64),
        _about(profile),
        _experience(data["experience"], data["education"],
                    data["skills_computing"], data["skills_interpersonal"]),
        _leadership(data["leadership"]),
        _publications_section(),
        _awards(data["awards"]),
        _patents(data["patents"]),
        _editorial(data["editorial"], profile),
        _presentations(data["presentations"]),
        _open_source(profile),
        _hobbies(data["hobbies"]),
        _references_section(),
        _footer(profile),
        # Cloudflare email decode script tag + script block
        '\n<script data-cfasync="false" src="/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js"></script><script>',
        _pubs_js(data["publications"]),
        _journals_js(data["journals"]),
        _refs_js(data["references"]),
        _repos_js(data["open_source"]),
        js,
        "</script>",
        "\n</body>\n</html>",
    ]

    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"  Generated {OUT.relative_to(ROOT)}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
