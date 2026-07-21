"""
build_html.py — regenerate index.html from /data/ CSVs + build/static_assets/.
Reads cv_style.css and cv_script.js verbatim; all dynamic content comes from CSVs.
"""
import base64, json, mimetypes, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import load_all_data, get_profile, parse_semicolon, clean_url, TAXONOMY, CAT_LABELS

ROOT   = pathlib.Path(__file__).parent.parent
ASSETS = pathlib.Path(__file__).parent / "static_assets"
OUT    = ROOT / "index.html"


# ── helpers ────────────────────────────────────────────────────────────────

def _e(s):
    """HTML-escape."""
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"','&quot;')

def _q(s):
    """JSON-safe string (escape backslash and single-quote)."""
    return str(s).replace("\\","\\\\").replace('"','\\"')

def _yes(value):
    return str(value or "").strip().lower() == "yes"

def _public_email_records(profile):
    candidates = []
    if _yes(profile.get("email_professional_public_visible", "yes")):
        candidates.append(("Mayo Email", profile.get("email_professional", "")))
    if _yes(profile.get("email_personal_public_visible", "no")):
        candidates.append(("Personal Email", profile.get("email_personal", "")))

    seen = set()
    records = []
    for label, email in candidates:
        email = str(email or "").strip()
        key = email.lower()
        if email and key not in seen:
            seen.add(key)
            records.append((label, email))
    return records

def _public_emails(profile):
    return [email for _, email in _public_email_records(profile)]

def _primary_public_email(profile):
    emails = _public_emails(profile)
    return emails[0] if emails else ""

def _email_parts(email):
    return (str(email).split("@") + [""])[:2]

def _email_link(email, text="[loading]", extra_class="", keep_content=False):
    email_u, email_d = _email_parts(email)
    classes = " ".join(c for c in ["cf-email", extra_class] if c)
    keep = ' data-keep-content="true"' if keep_content else ""
    return f'<a href="#" class="{_e(classes)}" data-u="{_e(email_u)}" data-d="{_e(email_d)}"{keep}>{_e(text)}</a>'


# ── SVG icons ──────────────────────────────────────────────────────────────

ICONS = {
    "scholar": '<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 3 2.5 8 12 13l9.5-5L12 3z"/><path d="M5 11.2V16c0 1.9 3.1 3.5 7 3.5s7-1.6 7-3.5v-4.8l-7 3.7-7-3.7z"/></svg>',
    "pubmed":  '<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.6"/><text x="12" y="15.5" text-anchor="middle" font-size="6.7" font-weight="700" stroke="none" fill="currentColor">PM</text></svg>',
    "orcid":   '<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.7"/><text x="12" y="16" text-anchor="middle" font-size="8.8" font-weight="700" stroke="none" fill="currentColor">iD</text></svg>',
    "scopus":  '<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.7"/><text x="12" y="16" text-anchor="middle" font-size="10" font-weight="700" stroke="none" fill="currentColor">S</text></svg>',
    "wos":     '<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.7"/><text x="12" y="15.6" text-anchor="middle" font-size="7.2" font-weight="700" stroke="none" fill="currentColor">WoS</text></svg>',
    "researchgate": '<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="3" fill="none" stroke="currentColor" stroke-width="1.7"/><text x="12" y="15.8" text-anchor="middle" font-size="7.2" font-weight="700" stroke="none" fill="currentColor">RG</text></svg>',
    "linkedin":'<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
    "github":  '<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>',
    "email": '<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="m4.5 7 7.5 6 7.5-6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}

LOGO_DIRS = [
    ROOT / "assets" / "logos",
    ROOT / "assets",
    ROOT / "images",
    ROOT / "img",
    ROOT / "public",
    ROOT / "static",
    ASSETS / "logos",
    ASSETS,
]
LOGO_SUFFIXES = {".svg", ".png", ".jpg", ".jpeg", ".webp"}
SOCIAL_LOGO_NAMES = {
    "scholar": ["google-scholar", "google_scholar", "googlescholar", "scholar"],
    "pubmed": ["pubmed", "ncbi"],
    "orcid": ["orcid"],
    "scopus": ["scopus"],
    "wos": ["web-of-science", "webofscience", "web_of_science", "wos"],
    "researchgate": ["researchgate", "research-gate", "research_gate"],
    "linkedin": ["linkedin", "linked-in", "linked_in"],
    "github": ["github", "git-hub", "git_hub"],
    "email": ["email", "mail"],
}
_SOCIAL_LOGO_CACHE = {}

def _norm_name(value):
    return "".join(ch for ch in str(value).lower() if ch.isalnum())

def _iter_logo_files():
    for directory in LOGO_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in LOGO_SUFFIXES:
                yield path

def _find_social_logo(key):
    if key in _SOCIAL_LOGO_CACHE:
        return _SOCIAL_LOGO_CACHE[key]

    wanted = {_norm_name(name) for name in SOCIAL_LOGO_NAMES.get(key, [key])}
    files = list(_iter_logo_files())
    for path in files:
        if _norm_name(path.stem) in wanted:
            _SOCIAL_LOGO_CACHE[key] = path
            return path
    for path in files:
        stem = _norm_name(path.stem)
        if any(name and name in stem for name in wanted):
            _SOCIAL_LOGO_CACHE[key] = path
            return path

    _SOCIAL_LOGO_CACHE[key] = None
    return None

def _local_logo_markup(key):
    path = _find_social_logo(key)
    if not path:
        return ""
    mime = mimetypes.guess_type(str(path))[0] or "image/svg+xml"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    src = f"data:{mime};base64,{data}"
    return f'<img class="social-icon-img" src="{_e(src)}" alt="" aria-hidden="true" loading="lazy" decoding="async">'

def _icon_markup(key):
    return _local_logo_markup(key) or ICONS.get(key, "")

def _icon_btn(href, title, key, extra_class="", mail=False):
    if not href or href == "#":
        return ""
    icon = _icon_markup(key)
    cls = f"social-icon-btn {key} {extra_class}".strip()
    target = "" if mail else ' target="_blank"'
    rel = "" if mail else ' rel="noopener noreferrer"'
    return f'<a href="{_e(href)}"{target} class="{cls}" title="{_e(title)}" aria-label="{_e(title)}"{rel}>{icon}<span class="sr-only">{_e(title)}</span></a>'

def _email_icon_btn(email):
    if not email:
        return ""
    email_u, email_d = _email_parts(email)
    icon = _icon_markup("email")
    return f'<a href="#" class="social-icon-btn email cf-email" data-u="{_e(email_u)}" data-d="{_e(email_d)}" data-keep-content="true" title="Email" aria-label="Email">{icon}<span class="sr-only">Email</span></a>'


def _dedupe_labels(labels, limit=6):
    out = []
    seen = set()
    for label in labels:
        text = " ".join(str(label or "").strip().split())
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if limit and len(out) >= limit:
            break
    return out


def _tag_chips_html(labels, class_name, handler_name, limit=6):
    chips = []
    for label in _dedupe_labels(labels, limit=limit):
        chips.append(
            f'<button type="button" class="{_e(class_name)}" data-tag="{_e(label)}" '
            f'onclick="{handler_name}(event,this)">{_e(label)}</button>'
        )
    return "".join(chips)


# ── section generators ─────────────────────────────────────────────────────

def _head(css: str, profile: dict) -> str:
    canonical = profile.get("canonical_url", "https://sorrad.github.io/RezaShahriarirad_CV/")
    desc = profile.get(
        "meta_description",
        "Academic CV of Reza Shahriarirad, M.D., Research Fellow at Mayo Clinic Surgery Innovation Center, with work in surgical innovation, minimally invasive surgery, and artificial intelligence in surgery.",
    )
    title = "Reza Shahriarirad, M.D. - Academic CV"
    same_as = [
        profile.get("scholar_url", ""),
        profile.get("pubmed_url", ""),
        profile.get("orcid_url", ""),
        profile.get("scopus_url", ""),
        profile.get("wos_url", ""),
        profile.get("researchgate_url", ""),
        profile.get("linkedin_url", ""),
        profile.get("github_url", ""),
    ]
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Reza Shahriarirad",
        "honorificSuffix": "M.D.",
        "jobTitle": profile.get("title", "Research Fellow"),
        "affiliation": {
            "@type": "Organization",
            "name": profile.get("institution", "Surgery Innovation Center, Mayo Clinic"),
        },
        "url": canonical,
        "description": desc,
        "sameAs": [url for url in same_as if url],
    }
    public_email = _primary_public_email(profile)
    if public_email:
        person["email"] = public_email
    og_image = canonical.rstrip("/") + "/assets/headshot.jpg" if (ROOT / "assets" / "headshot.jpg").exists() else ""
    og_image_tags = (
        f'\n<meta property="og:image" content="{_e(og_image)}">'
        f'\n<meta name="twitter:image" content="{_e(og_image)}">'
    ) if og_image else ""
    favicon = (
        "data:image/svg+xml,"
        "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
        "%3Crect width='64' height='64' rx='10' fill='%230a1628'/%3E"
        "%3Ctext x='32' y='43' text-anchor='middle' font-family='Georgia,serif' font-size='30' fill='%23d4ae5a'%3ERS%3C/text%3E"
        "%3C/svg%3E"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_e(title)}</title>
<meta name="description" content="{_e(desc)}">
<meta name="author" content="Reza Shahriarirad, M.D.">
<meta name="theme-color" content="#0a1628">
<link rel="canonical" href="{_e(canonical)}">
<link rel="icon" href="{favicon}">
<meta property="og:title" content="{_e(title)}">
<meta property="og:description" content="{_e(desc)}">
<meta property="og:type" content="profile">
<meta property="og:url" content="{_e(canonical)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{_e(title)}">
<meta name="twitter:description" content="{_e(desc)}">{og_image_tags}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400&display=swap" rel="stylesheet">
<script type="application/ld+json">
{json.dumps(person, ensure_ascii=False, indent=2)}
</script>
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
    <li><a href="#hobbies">Hobbies</a></li>
    <li><a href="#references">References</a></li>
  </ul>
  <button class="hamburger" type="button" onclick="toggleMenu()" aria-label="Toggle navigation menu" aria-controls="mobile-menu" aria-expanded="false"><span></span><span></span><span></span></button>
</nav>
<div class="mobile-menu" id="mobile-menu" aria-label="Mobile navigation">
  <a href="#about" onclick="closeMenu()">About</a>
  <a href="#experience" onclick="closeMenu()">Experience</a>
  <a href="#leadership" onclick="closeMenu()">Leadership</a>
  <a href="#publications" onclick="closeMenu()">Publications</a>
  <a href="#awards" onclick="closeMenu()">Awards</a>
  <a href="#patents" onclick="closeMenu()">Patents</a>
  <a href="#reviewer" onclick="closeMenu()">Editorial</a>
  <a href="#presentations" onclick="closeMenu()">Presentations</a>
  <a href="#opensource" onclick="closeMenu()">Open Source</a>
  <a href="#hobbies" onclick="closeMenu()">Hobbies</a>
  <a href="#references" onclick="closeMenu()">References</a>
</div>"""


def _hero(profile: dict, pub_count: int, photo_b64: str) -> str:
    cites   = profile.get("citations_cached", "3248")
    hindex  = profile.get("h_index_cached",   "24")
    reviews = profile.get("peer_reviews",      "149")
    metrics_date = profile.get("metrics_last_updated", "")
    hero_institution = profile.get("institution", "Department of Surgery - Surgical Innovation · Mayo Clinic")
    hero_institution = hero_institution.replace(" · Mayo Clinic", "")
    public_email = _primary_public_email(profile)
    email_cta = _email_link(public_email, "Get in Touch", "btn-outline", keep_content=True) if public_email else ""
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
      <!-- EDIT: Hero eyebrow text (e.g. "Physician · Researcher") -->
      <div class="hero-eyebrow">Physician · Researcher</div>
      <!-- EDIT: Hero name display -->
      <h1>Reza<br><span class="hero-title-accent">Shahriarirad,</span><br>M.D.</h1>
      <!-- EDIT: Hero credentials line (title, institution, ORCID) -->
      <div class="hero-credentials">
        <strong>{_e(profile.get('title','Research Fellow'))}, {_e(hero_institution)}</strong><br>
        Mayo Clinic · Rochester, Minnesota<br>
        ORCID: {_e(profile.get('orcid',''))}
      </div>
      <div class="hero-cta">
        <a href="#publications" class="btn-primary">View Publications</a>
        {email_cta}
        <a href="Shahriarirad_Reza_CV.pdf"
           target="_blank" rel="noopener noreferrer" class="btn-pdf" aria-label="Download CV PDF">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" fill="currentColor"/></svg>
          Download CV (PDF)
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
          <div class="stat-num" id="hero-cites">{cites_fmt}</div>
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
      <!-- metrics-last-updated: {_e(metrics_date or '')} — hidden from public page; tracked in data/profile.csv -->
    </div>
  </div>
</div>"""


def _about(profile: dict) -> str:
    bio1 = profile.get("bio_paragraph_1", "")
    bio2 = profile.get("bio_paragraph_2", "")
    irb_count = profile.get("irb_count", "30")

    # Research tags mapped to taxonomy cat keys
    tags_data = [
        ("Plastic & Reconstructive Surgery",   "plastic"),
        ("Bariatric Surgery",                  "bariatric"),
        ("Orthopaedic Surgery",                "ortho"),
        ("Thoracic Surgery",                   "thoracic"),
        ("Vascular Surgery",                   "vascular"),
        ("GI & Colorectal Surgery",            "gi"),
        ("Surgical AI & Innovation",           "machine_learning"),
    ]
    tags_html = "\n".join(
        f'          <span class="research-tag" data-cat="{cat}">{label}</span>'
        for label, cat in tags_data
    )

    email_records = _public_email_records(profile)
    primary_email = email_records[0][1] if email_records else ""
    loc  = f"{profile.get('city_state','Rochester, MN')}, USA"
    langs    = profile.get("languages", "English (Fluent) · Farsi (Native)")
    res_int  = profile.get("research_interests","Surgery · Minimally Invasive Surgery · Artificial Intelligence")
    contact_rows = []
    for label, email in email_records:
        contact_rows.append(f'<div class="contact-item"><span>{_e(label)}</span>{_email_link(email)}</div>')
    if _yes(profile.get("phone_public_visible", "no")) and profile.get("phone"):
        contact_rows.append(f'<div class="contact-item"><span>Phone</span><span>{_e(profile.get("phone",""))}</span></div>')
    contact_rows.extend([
        f'<div class="contact-item"><span>Location</span><span>{_e(loc)}</span></div>',
        f'<div class="contact-item"><span>Research Interests</span><span>{_e(res_int)}</span></div>',
        f'<div class="contact-item"><span>Languages</span><span>{_e(langs)}</span></div>',
    ])
    contact_html = "\n        ".join(contact_rows)

    icons_html = "\n        ".join([
        _icon_btn(profile.get("scholar_url","#"),     "Google Scholar",  "scholar"),
        _icon_btn(profile.get("pubmed_url","#"),       "PubMed / NCBI",   "pubmed"),
        _icon_btn(profile.get("orcid_url","#"),        "ORCID",           "orcid"),
        _icon_btn(profile.get("scopus_url","#"),       "Scopus",          "scopus"),
        _icon_btn(profile.get("wos_url","#"),          "Web of Science",  "wos"),
        _icon_btn(profile.get("researchgate_url","#"), "ResearchGate",    "researchgate"),
        _icon_btn(profile.get("linkedin_url","#"),     "LinkedIn",        "linkedin"),
        _icon_btn(profile.get("github_url","#"),       "GitHub",          "github"),
        _email_icon_btn(primary_email),
    ])

    return f"""
<!-- ABOUT -->
<div id="about">
<div class="section-wrap">
  <div class="section-label">Profile</div>
  <h2>About</h2>
  <div class="about-grid">
    <div class="about-text">
      <!-- EDIT: About paragraph 1 -->
      <p>{bio1}</p>
      <!-- EDIT: About paragraph 2 -->
      <p>{bio2}</p>
      <div style="margin:1.8rem 0 0">
        <div class="section-label" style="margin-bottom:.8rem">Ongoing Research at Mayo Clinic</div>
        <!-- EDIT: Mayo Clinic / IRB research description paragraph -->
        <p>{_e(profile.get("irb_description", f"Since joining the Center for Surgery Innovation, I have been involved in more than {irb_count} IRB-approved research projects spanning a broad range of surgical specialties."))}</p>
        <!-- EDIT: Research specialty tags list -->
        <div class="research-grid">
{tags_html}
        </div>
      </div>
    </div>
    <div>
      <div class="contact-block">
        <h3>Contact</h3>
        {contact_html}
      </div>
      <div class="social-icons" style="margin-top:1rem;justify-content:flex-start">
        {icons_html}
      </div>
    </div>
  </div>
</div>
</div>"""


_LOGO_SIZE_LIMIT = 150_000  # bytes; embed small logos, reference larger local assets

def _logo_img_from_path(p, org_name="", class_name="timeline-logo"):
    alt = _e(f"{org_name} logo" if org_name else "Institution logo")
    if p.stat().st_size > _LOGO_SIZE_LIMIT:
        try:
            rel = p.relative_to(ROOT).as_posix()
        except ValueError:
            print(f"[build_html] WARNING: logo_file '{p.name}' is larger than {_LOGO_SIZE_LIMIT} bytes and cannot be referenced from the site root; using fallback initials.")
            return ""
        print(f"[build_html] WARNING: logo_file '{p.name}' is larger than {_LOGO_SIZE_LIMIT} bytes; referencing local asset '{rel}' instead of embedding.")
        return f'<img class="{_e(class_name)}" src="{_e(rel)}" alt="{alt}" loading="lazy" decoding="async">'
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f'<img class="{_e(class_name)}" src="data:{mime};base64,{data}" alt="{alt}" loading="lazy" decoding="async">'

def _institutional_logo(logo_file, org_name="", class_name="timeline-logo"):
    """Return a local logo image, embedding small files and referencing larger ones."""
    if not logo_file or not str(logo_file).strip():
        return ""
    fname = str(logo_file).strip()
    for directory in LOGO_DIRS:
        p = directory / fname
        if p.exists() and p.is_file():
            return _logo_img_from_path(p, org_name, class_name)
    wanted_stem = _norm_name(pathlib.Path(fname).stem)
    for p in _iter_logo_files():
        if _norm_name(p.stem) == wanted_stem:
            return _logo_img_from_path(p, org_name, class_name)
    print(f"[build_html] WARNING: logo_file '{fname}' was not found; using fallback initials.")
    return ""


def _initials_from_text(text, max_chars=4):
    words = [
        word
        for word in re.split(r"[^A-Za-z0-9]+", str(text or ""))
        if word and word.lower() not in {"and", "of", "the", "for"}
    ]
    if not words:
        return "CV"
    initials = "".join(word[0].upper() for word in words[:max_chars])
    return initials[:max_chars] or words[0][:max_chars].upper()


def _logo_placeholder(initials, org_name="", color="", class_name="timeline-logo-placeholder"):
    text = str(initials or "").strip() or _initials_from_text(org_name)
    color_value = str(color or "").strip() or "#4a607e"
    long_class = " placeholder-long" if len(text) > 4 else ""
    label = _e(f"{org_name} logo placeholder" if org_name else "Logo placeholder")
    return (
        f'<div class="{_e(class_name + long_class)}" style="background:{_e(color_value)};color:#fff" '
        f'role="img" aria-label="{label}">{_e(text)}</div>'
    )


def _experience(exp_df, edu_df, skills_comp_df, skills_inter_df, skills_research_df=None, aff_df=None) -> str:
    def _logo_el(row, org_key="org"):
        logo_file = str(row.get("logo_file", "")).strip()
        org_name = str(row.get(org_key, "")).strip()
        img = _institutional_logo(logo_file, org_name)
        if img:
            return img
        return _logo_placeholder(row.get("logo_initials", ""), org_name, row.get("logo_color", ""))

    def timeline_item(row):
        logo = _logo_el(row, "org")
        desc_html = f'\n          <div class="timeline-desc">{_e(row["desc"])}</div>' if row.get("desc","").strip() else ""
        return f"""        <!-- EDIT: Each timeline entry role description -->
        <div class="timeline-item">
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
        logo = _logo_el(row, "org")
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

    exp_items = "\n".join(timeline_item(r) for _, r in exp_df.iterrows())
    edu_items = "\n".join(edu_item(r) for _, r in edu_df.iterrows())

    def _skill_name(r):
        url = str(r.get("url","")).strip()
        name = _e(r["name"])
        return f'<a href="{_e(url)}" target="_blank">{name}</a>' if url else name

    comp_rows = "\n".join(
        f'          <div class="skill-item"><span>{_skill_name(r)}</span><span class="skill-level">{_e(r["level"])}</span></div>'
        for _, r in skills_comp_df.iterrows()
    )
    inter_rows = "\n".join(
        f'          <div class="skill-item">{_e(r["name"])}</div>'
        for _, r in skills_inter_df.iterrows()
    )
    research_rows = ""
    if skills_research_df is not None:
        research_rows = "\n".join(
            f'          <div class="skill-item">{_e(r["name"])}</div>'
            for _, r in skills_research_df.iterrows()
        )
    research_group = f"""
        <div class="skill-group">
          <h3>Research &amp; Analytical</h3>
{research_rows}
        </div>""" if research_rows else ""

    # Lab affiliations section
    aff_section = ""
    if aff_df is not None and len(aff_df) > 0:
        if "show_in_experience" in aff_df.columns:
            show = aff_df[aff_df["show_in_experience"].str.strip().str.lower() == "yes"]
        else:
            show = aff_df
        aff_cards = []
        for _, r in show.iterrows():
            name = _e(r.get("name", ""))
            url = str(r.get("url", "")).strip()
            name_html = f'<a href="{_e(url)}" target="_blank" rel="noopener noreferrer">{name}</a>' if url else name
            hide_meta = str(r.get("hide_meta", "")).strip().lower() == "yes"
            display_detail = str(r.get("display_detail", "")).strip()
            role = str(r.get("role", "")).strip()
            role_display = display_detail if hide_meta and display_detail else role
            role_html = f'<div class="lab-card-role">{_e(role_display)}</div>' if role_display else ""
            detail_html = (
                f'<div class="lab-card-detail">{_e(display_detail)}</div>'
                if display_detail and not (hide_meta and display_detail)
                else ""
            )
            if not hide_meta:
                meta = " · ".join(x for x in [
                    str(r.get("institution", "")).strip(),
                    str(r.get("period", "")).strip(),
                ] if x)
                meta_html = f'<div class="lab-card-inst">{_e(meta)}</div>' if meta else ""
            else:
                meta_html = ""
            logo_img = _institutional_logo(r.get("logo_file", ""), str(r.get("name", "")), "lab-card-logo")
            logo_html = logo_img or _logo_placeholder(
                r.get("logo_initials", ""),
                str(r.get("name", "")),
                r.get("logo_color", ""),
                "lab-card-logo-placeholder",
            )
            link_url_2 = str(r.get("link_url_2", "")).strip()
            links_html = ""
            if link_url_2:
                link_label_2 = str(r.get("link_label_2", "")).strip() or "More"
                chips = []
                if url:
                    chips.append(f'<a href="{_e(url)}" target="_blank" rel="noopener noreferrer" class="ref-link">Website &#8599;</a>')
                chips.append(f'<a href="{_e(link_url_2)}" target="_blank" rel="noopener noreferrer" class="ref-link">{_e(link_label_2)} &#8599;</a>')
                links_html = f'<div class="lab-card-links">{"".join(chips)}</div>'
            aff_cards.append(f"""      <div class="lab-card">
        {logo_html}
        <div class="lab-card-body">
          <div class="lab-card-name">{name_html}</div>
          {role_html}
          {detail_html}
          {meta_html}
          {links_html}
        </div>
      </div>""")
        if aff_cards:
            aff_section = f"""
  <div>
    <div class="lab-affiliations-heading"><h3>Lab Affiliations</h3></div>
    <div class="lab-cards-grid">
{''.join(aff_cards)}
    </div>
  </div>"""

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
      <div class="skills-grid" style="gap:1.5rem;margin-top:.5rem">
        <div class="skill-group">
          <h3>Technical &amp; Software</h3>
{comp_rows}
        </div>
{research_group}
        <div class="skill-group">
          <h3>Interpersonal</h3>
{inter_rows}
        </div>
      </div>
    </div>
  </div>{aff_section}
</div>
</div>"""


def _leadership(leadership_df) -> str:
    cards = []
    for _, r in leadership_df.iterrows():
        # EDIT: Leadership card description
        cards.append(f"""  <!-- EDIT: Leadership card description -->
  <div class="leadership-card">
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


def _dropdown_html(btn_id, panel_id, default_label, options, option_values=None):
    """Render a custom multi-select dropdown."""
    if option_values is None:
        option_values = [o.lower().replace(" ","_").replace("/","").replace("&","").replace("-","") for o in options]
    opts_html = "\n".join(
        f'        <div class="custom-dropdown-option" data-value="{_e(val)}" role="option" tabindex="0" aria-selected="false">'
        f'<input type="checkbox" value="{_e(val)}" aria-label="{_e(label)}"><span class="opt-label">{_e(label)}</span></div>'
        for label, val in zip(options, option_values)
    )
    return f"""      <div class="custom-dropdown">
        <button class="custom-dropdown-btn" id="{btn_id}" type="button" aria-haspopup="listbox" aria-expanded="false" aria-controls="{panel_id}">
          <span class="dropdown-label" data-default="{_e(default_label)}">{_e(default_label)}</span>
          <span class="custom-dropdown-arrow">&#9660;</span>
        </button>
        <div class="custom-dropdown-panel" id="{panel_id}" role="listbox" aria-multiselectable="true">
{opts_html}
        </div>
      </div>"""


def _publications_section() -> str:
    type_dropdown = _dropdown_html(
        "pub-type-btn", "pub-type-panel", "All Types",
        ["Original Articles", "Reviews & Meta-analyses", "Case Reports", "Letters / Editorials"],
        ["original", "review", "case", "letter"]
    )
    auth_dropdown = _dropdown_html(
        "pub-auth-btn", "pub-auth-panel", "All Roles",
        ["1st Author", "2nd / Co-first", "Corresponding Author", "Last / Senior Author"],
        ["first", "co-first", "corresponding", "last"]
    )

    # Build topic filter tree from taxonomy
    topic_tree = ""
    for grp_key in sorted(TAXONOMY.keys()):
        grp = TAXONOMY[grp_key]
        subs_html = "\n".join(
            f'            <button class="filter-btn filter-sub-btn" type="button" aria-pressed="false" onclick="filterPubs(event,\'{sub_key}\',this,\'cat\')" data-cat="{sub_key}" data-main="{grp_key}">{_e(sub_label)}</button>'
            for sub_key, sub_label in sorted(grp["subs"].items(), key=lambda x: x[1])
        )
        topic_tree += f"""
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" type="button" aria-pressed="false" onclick="filterPubsMain(event,this)" data-group="{grp_key}">
            <span>{_e(grp['label'])}</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="grp-{grp_key}" style="display:none">
{subs_html}
          </div>
        </div>"""

    return f"""
<!-- PUBLICATIONS -->
<div class="section-alt" id="publications">
<div class="section-wrap">
  <div class="section-label">Research Output</div>
  <h2>Publications</h2>
  <p class="pub-note pub-author-note" id="pub-author-note">* denotes corresponding author. My name is highlighted in bold.</p>

  <div class="pub-controls">
    <!-- Left: filter sidebar -->
    <div class="pub-filter-sidebar">
      <div class="pub-filter-group">
        <button class="filter-btn" type="button"
          style="width:100%;background:var(--gold);color:var(--navy);border-color:var(--gold);font-weight:500;text-align:center"
          onclick="resetPubFilters(event)" aria-label="Reset all publication filters">&#8635; Reset filters</button>
      </div>
      <div class="pub-filter-group">
        <span class="pub-filter-group-label">Article Type</span>
{type_dropdown}
      </div>
      <div class="pub-filter-group">
        <span class="pub-filter-group-label">Authorship</span>
{auth_dropdown}
      </div>
      <div class="pub-filter-group">
        <span class="pub-filter-group-label">Topic</span>
        <button class="filter-btn active" type="button" aria-pressed="true" onclick="filterPubs(event,'all',this,'cat')" id="cat-all-btn">All Topics</button>
{topic_tree}
      </div>
    </div>
    <!-- Right: search + list -->
    <div class="pub-list-wrap">
      <div class="search-row">
        <label class="search-shell" for="pub-search">
          <span id="pub-search-prefix" class="search-filter-prefix" hidden></span>
          <input class="pub-search search-input" type="search" id="pub-search" aria-label="Search publications" placeholder="Search title, author, journal, keyword..."
            oninput="handlePubSearchInput(this.value)">
        </label>
        <div id="pub-count" class="pub-count">—</div>
      </div>
      <div class="pub-list" id="pub-list"></div>
    </div><!-- /pub-list-wrap -->
  </div><!-- /pub-controls -->
  <div style="text-align:center;padding:2rem 0 0" id="pub-more">
    <button class="btn-outline" type="button" onclick="showAllPubs(event)" style="border-color:var(--navy);color:var(--navy)">Show all publications</button>
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


_PATENT_ISSUER_LABELS = {"IR": "Iranian Patent", "US": "US Patent", "EP": "European Patent"}

def _patents(patents_df) -> str:
    items = []
    for _, r in patents_df.iterrows():
        issuer_raw = str(r.get("issuer", "")).strip()
        issuer_label = _PATENT_ISSUER_LABELS.get(issuer_raw.upper(), issuer_raw or "Patent")
        status = str(r.get("status", "")).strip() or "Issued"
        date = str(r.get("date", "")).strip()
        issued = f"{status} {date}".strip()
        items.append(f"""    <div class="patent-item">
      <div class="patent-date">{_e(date)}</div>
      <div>
        <div class="patent-title">{_e(r["title"])}</div>
        <div class="patent-id">{_e(issuer_label)} No. {_e(r["number"])} &nbsp;·&nbsp; {_e(issued)}</div>
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
        seen = set(); cats_u = [c for c in cats if not (c in seen or seen.add(c))]
        data_cats = ",".join(cats_u)
        keywords = parse_semicolon(r.get("keywords", ""))
        data_keywords = " ".join(keywords)
        cat_labels = " ".join(CAT_LABELS.get(c, c) for c in cats_u)
        type_cls  = r.get("type","poster").strip().lower()
        type_lbl  = type_cls.capitalize()
        tag_labels = (
            keywords
            + [CAT_LABELS.get(c, c) for c in cats_u]
            + [type_lbl, r.get("conference", ""), r.get("location", "")]
        )
        tags_html = _tag_chips_html(tag_labels, "pres-tag-chip", "applyPresSearchTag")
        search_text = " ".join([
            str(r.get("title", "")),
            str(r.get("venue", "")),
            str(r.get("conference", "")),
            str(r.get("location", "")),
            data_keywords,
            cat_labels,
            " ".join(tag_labels),
        ])
        items.append(f"""    <div class="pres-item" data-type="{_e(type_cls)}" data-location="{_e(r.get('location',''))}" data-cats="{_e(data_cats)}" data-keywords="{_e(data_keywords)}" data-search="{_e(search_text)}">
      <div class="pres-date-col">
        <span class="pres-year-txt">{_e(r.get('date',''))}</span>
        <span class="pres-type {type_cls}">{type_lbl}</span>
      </div>
      <div>
        <div class="pres-title">{_e(r.get('title',''))}</div>
        <div class="pres-venue">{_e(r.get('venue',''))}</div>
        <div class="pres-location">{_e(r.get('location',''))}</div>
        <div class="pres-tags-row">{tags_html}</div>
      </div>
    </div>""")

    pres_type_dropdown = _dropdown_html(
        "pres-type-btn", "pres-type-panel", "All Types",
        ["Poster", "Oral"],
        ["poster", "oral"]
    )
    locations = sorted({
        str(r.get("location", "")).strip()
        for _, r in pres_df.iterrows()
        if str(r.get("location", "")).strip()
    })
    pres_loc_dropdown = _dropdown_html(
        "pres-loc-btn", "pres-loc-panel", "All Locations",
        locations,
        locations
    )

    # Presentations topic tree (same taxonomy)
    pres_topic_tree = ""
    for grp_key in sorted(TAXONOMY.keys()):
        grp = TAXONOMY[grp_key]
        subs_html = "\n".join(
            f'            <button class="filter-btn filter-sub-btn" type="button" aria-pressed="false" onclick="filterPres(event,\'cat\',\'{sub_key}\',this)" data-cat="{sub_key}" data-main="{grp_key}">{_e(sub_label)}</button>'
            for sub_key, sub_label in sorted(grp["subs"].items(), key=lambda x: x[1])
        )
        pres_topic_tree += f"""
        <div class="filter-main-group">
          <button class="filter-btn filter-main-btn" type="button" aria-pressed="false" onclick="filterPresMain(event,this)" data-group="{grp_key}">
            <span>{_e(grp['label'])}</span><span class="filter-caret">&#9658;</span>
          </button>
          <div class="filter-sub-group" id="pgrp-{grp_key}" style="display:none">
{subs_html}
          </div>
        </div>"""

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
        <button class="filter-btn" type="button"
          style="width:100%;background:var(--gold);color:var(--navy);border-color:var(--gold);font-weight:500;text-align:center"
          id="pres-reset" aria-label="Reset all presentation filters" onclick="resetPresFilters(event)">&#8635; Reset filters</button>
      </div>
      <div class="pres-filter-group">
        <span class="pub-filter-group-label">Type</span>
{pres_type_dropdown}
      </div>
      <div class="pres-filter-group">
        <span class="pub-filter-group-label">Location</span>
{pres_loc_dropdown}
      </div>
      <div class="pres-filter-group">
        <span class="pub-filter-group-label">Topic</span>
{pres_topic_tree}
      </div>
    </div>
    <!-- Right: search + list -->
    <div class="pres-list-wrap">
      <div class="search-row">
        <label class="search-shell" for="pres-search">
          <span id="pres-search-prefix" class="search-filter-prefix" hidden></span>
          <input class="pres-search search-input" type="search" id="pres-search" aria-label="Search presentations" placeholder="Search title or conference..."
            oninput="filterPresSearch(this.value)">
        </label>
        <div id="pres-count" class="pub-count">{len(pres_df)} presentations</div>
      </div>
      <div class="pres-list" id="pres-list">
{''.join(items)}
      </div>
      <div class="pres-more-wrap" id="pres-more">
        <button class="btn-outline" type="button" onclick="togglePresMore(event)" style="border-color:var(--navy);color:var(--navy)">Show more presentations</button>
      </div>
    </div>
  </div></div>
</div>
</div>"""


def _open_source(profile: dict) -> str:
    github_url = profile.get("github_url", "").strip()
    github_user = profile.get("github_username", "").strip() or "SoRRad"
    github_icon = ICONS.get("github", "")
    github_card = ""
    if github_url:
        github_card = f"""  <div class="github-profile-row">
    <div class="repo-card repo-profile-card">
      <div class="repo-card-header repo-profile-heading">
        <span class="repo-card-icon github-profile-icon">{github_icon}</span>
        <span class="repo-card-name">GitHub Profile</span>
      </div>
      <div class="repo-links">
        <a href="{_e(github_url)}" target="_blank" rel="noopener noreferrer" class="repo-link primary" aria-label="View GitHub profile">View on GitHub &#8599;</a>
      </div>
    </div>
  </div>"""

    return f"""
<!-- OPEN SOURCE MODELS -->
<div id="opensource">
<div class="section-wrap">
  <div class="section-label">Open Science</div>
  <h2>Open Source Models &amp; Code</h2>
  <p style="font-size:.9rem;color:var(--text-muted);margin-bottom:1.8rem;line-height:1.85;max-width:680px">Open-source code, models, and academic software projects — all publicly available at github.com/{_e(github_user)}.</p>
{github_card}
  <div class="repos-grid" id="repos-grid"></div>
</div>
</div>"""


def _hobbies(hobbies_df) -> str:
    cards = []
    for _, r in hobbies_df.iterrows():
        name_esc = _e(r["name"])
        cards.append(f"""    <div class="hobby-card">
      <div class="hobby-icon">{r["icon"]}</div>
      <div><div class="hobby-name">{name_esc}</div><div class="hobby-desc">{_e(r["desc"])}</div></div>
    </div>""")
    return f"""
<!-- HOBBIES -->
<div class="section-alt" id="hobbies">
<div class="section-wrap">
  <div class="section-label">Personal</div>
  <h2>Extracurricular &amp; Hobbies</h2>
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
    profile_links = []
    for label, href in [
        ("Google Scholar", profile.get("scholar_url", "")),
        ("PubMed", profile.get("pubmed_url", "")),
        ("ORCID", profile.get("orcid_url", "")),
        ("Scopus", profile.get("scopus_url", "")),
        ("Web of Science", profile.get("wos_url", "")),
        ("ResearchGate", profile.get("researchgate_url", "")),
        ("LinkedIn", profile.get("linkedin_url", "")),
        ("GitHub", profile.get("github_url", "")),
    ]:
        if href:
            profile_links.append(f'<a href="{_e(href)}" target="_blank" rel="noopener noreferrer">{_e(label)}</a>')
    for label, email in _public_email_records(profile):
        profile_links.append(_email_link(email, label, keep_content=True))
    footer_links_html = "\n    ".join(profile_links)
    footer_institution = "Department of Surgery - Surgical Innovation"

    return f"""
<!-- BACK TO TOP -->
<button class="back-to-top" id="back-to-top" type="button" aria-label="Back to top" title="Back to top">
  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M12 5 4 13h5v6h6v-6h5l-8-8z"/></svg>
</button>
<!-- FOOTER -->
<footer>
  <div class="footer-name">{_e(profile.get('name','Reza Shahriarirad, M.D.'))}</div>
  <!-- EDIT: Footer tagline -->
  <div class="footer-note">{_e(profile.get('title','Research Fellow'))} · {_e(footer_institution)} · {_e(profile.get('city_state','Rochester, MN'))}</div>
  <div class="footer-divider"></div>
  <div class="footer-links">
    {footer_links_html}
  </div>
</footer>"""


# ── JS data generators ─────────────────────────────────────────────────────

def _category_labels_js() -> str:
    payload = {
        **CAT_LABELS,
        **{grp_key: grp["label"] for grp_key, grp in TAXONOMY.items()},
    }
    return "const categoryLabels = " + json.dumps(payload, ensure_ascii=False, sort_keys=True) + ";"


def _pubs_js(pubs_df) -> str:
    """Generate const publications=[...] from the CSV."""
    entries = []
    for _, r in pubs_df.iterrows():
        n_raw = str(r.get("n", "")).strip()
        entries.append({
            "n": int(n_raw) if n_raw.isdigit() else 0,
            "year": str(r.get("year", "")).strip(),
            "month": str(r.get("month", "")).strip(),
            "type": str(r.get("type", "")).strip().lower(),
            "tags": [t.lower() for t in parse_semicolon(r.get("tags", ""))],
            "cat": [c.lower() for c in parse_semicolon(r.get("cat", ""))],
            "title": str(r.get("title", "")).strip(),
            "authors": str(r.get("authors", "")).strip(),
            "journal": str(r.get("journal", "")).strip(),
            "url": clean_url(str(r.get("url", "")).strip()),
            "keywords": parse_semicolon(r.get("keywords", "")),
            "highlight_topics": [h.lower() for h in parse_semicolon(r.get("highlight_topics", ""))],
            "featured": "yes" if _yes(r.get("featured", "")) else "",
        })
    return "const publications = " + json.dumps(entries, ensure_ascii=False, indent=2) + ";"


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


def _affiliations_js(aff_df) -> str:
    if aff_df is None or len(aff_df) == 0:
        return "const affiliations = [];"
    entries = []
    for _, r in aff_df.iterrows():
        if r.get("show_in_experience","yes").strip().lower() != "yes":
            continue
        entries.append(
            f'{{org_key:"{_q(r.get("org_key",""))}",name:"{_q(r.get("name",""))}",role:"{_q(r.get("role",""))}",pi_name:"{_q(r.get("pi_name",""))}",pi_title:"{_q(r.get("pi_title",""))}",institution:"{_q(r.get("institution",""))}",url:"{_q(r.get("url",""))}",logo_file:"{_q(r.get("logo_file",""))}",period:"{_q(r.get("period",""))}",desc:"{_q(r.get("desc",""))}" }}'
        )
    if not entries:
        return "const affiliations = [];"
    return "const affiliations=[\n  " + ",\n  ".join(entries) + "\n];"


# ── main ───────────────────────────────────────────────────────────────────

def main():
    data    = load_all_data()
    profile = get_profile(data)

    css = (ASSETS / "cv_style.css").read_text(encoding="utf-8")
    js  = (ASSETS / "cv_script.js").read_text(encoding="utf-8")
    photo_b64 = (ASSETS / "headshot.b64").read_text(encoding="ascii").strip()

    # Count publications excluding blank/comment rows
    pub_count = len(data["publications"])

    # affiliations data (optional)
    aff_df = data.get("affiliations", None)

    parts = [
        _head(css, profile),
        _nav(),
        _hero(profile, pub_count, photo_b64),
        _about(profile),
        _experience(data["experience"], data["education"],
                    data["skills_computing"], data["skills_interpersonal"],
                    data.get("skills_research", None), aff_df),
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
        '\n<script>',
        _category_labels_js(),
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
    print(f"  Publications in output: {pub_count}")


if __name__ == "__main__":
    main()
