# Reza Shahriarirad, M.D. — Academic CV Website

Personal academic CV website for Dr. Reza Shahriarirad, Research Fellow at the Surgery Innovation Center, Mayo Clinic. A single self-contained HTML file with live citation metrics, filterable publications, and an auto-updating downloadable Word CV.

**Live site:** `https://SoRRad.github.io/RezaShahriarirad_CV`
**Admin panel:** `https://SoRRad.github.io/RezaShahriarirad_CV/cv-admin.html`

---

## Data-driven workflow

All CV content now lives in structured CSV files under `/data/`. A Python build system reads these files and regenerates `index.html`, `Shahriarirad_Reza_CV.docx`, and `Shahriarirad_Reza_CV.pdf` automatically.

### How to update your CV

1. Edit the relevant CSV file in `/data/` (e.g. open `data/publications.csv` in Excel or a text editor)
2. Commit and push to `main`
3. GitHub Actions rebuilds all outputs within ~2 minutes

### Run the build locally

```bash
pip install -r build/requirements.txt
python build/build.py
```

### Admin panel note

`cv-admin.html` still works for quick browser-based edits, but changes made there do **not** update the CSV files. You must manually sync them back to keep the CSVs as the source of truth.

### CSV files

| File | Contents |
|------|----------|
| `data/profile.csv` | Name, title, bio paragraphs, contact info, social URLs, cached metrics |
| `data/experience.csv` | Professional positions (period, role, org, city, description) |
| `data/education.csv` | Academic degrees |
| `data/leadership.csv` | Leadership and service roles |
| `data/awards.csv` | Awards and honours |
| `data/patents.csv` | Patents and innovations |
| `data/publications.csv` | All 193+ publications (type, title, authors, journal, URL, tags, categories) |
| `data/presentations.csv` | Conference presentations (date, type, title, venue, location, categories) |
| `data/journals.csv` | Peer-reviewed journals reviewed (with acknowledgement URLs) |
| `data/editorial.csv` | Editorial roles (Guest Editor, Associate Editor, etc.) |
| `data/hobbies.csv` | Extracurricular interests |
| `data/references.csv` | Professional references with contact links |
| `data/skills_computing.csv` | Computing skills with proficiency levels |
| `data/skills_interpersonal.csv` | Interpersonal skills |
| `data/open_source.csv` | Open-source GitHub repos (currently empty; add via admin panel) |

---

## Repository contents

| File | Description |
|------|-------------|
| `index.html` | The full CV website — rename from `Shahriarirad_CV_Website_v4.html` before uploading |
| `cv-admin.html` | Admin panel for editing all CV sections directly from the browser |
| `cv_pubs.json` | All 193 publications as structured JSON |
| `cv_presentations.json` | 17 conference presentations with location and topic data |
| `cv_journals.json` | 67 peer-reviewed journals reviewed |
| `cv_generator.js` | Node.js script that builds the downloadable DOCX from live data |
| `cv_live_stats.json` | Latest fetched metrics — auto-updated by the weekly workflow |
| `Shahriarirad_Reza_CV.docx` | Downloadable CV in Word format — auto-regenerated weekly |
| `.github/workflows/update-cv.yml` | GitHub Actions workflow for weekly auto-updates |
| `README.md` | This file |

---

## CV sections

The website covers the following sections, all editable via the admin panel:

- **About** — Bio, headshot, Mayo Clinic ongoing research projects, specialty tags
- **Experience & Education** — Professional timeline and academic credentials
- **Leadership & Community Service**
- **Publications** — 193 papers filterable by type, authorship role, and 17 topic categories
- **Awards & Honours**
- **Patents & Innovations**
- **Editor & Reviewer Experience** — Editorial roles and 149 verified peer reviews across 67 journals
- **Presentations** — 17 conference presentations filterable by type, location, and topic
- **Extracurricular & Interests**
- **References** — 9 professional references

---

## Live data

| Metric | Source | Update frequency |
|--------|--------|-----------------|
| Citations | Google Scholar (via CORS proxy) | Every page load |
| H-index | Google Scholar (via CORS proxy) | Every page load |
| Publications count | Hardcoded (193) | Manual — update when you publish |
| Peer reviews | Hardcoded (149) | Manual via admin panel |

Google Scholar data is fetched live on every page visit using three CORS proxy fallbacks. If all proxies fail, the last known values (3,248 citations, H-index 24) are shown.

---

## Auto-update workflow

A GitHub Actions workflow (`.github/workflows/update-cv.yml`) runs every **Monday at 6:00 AM UTC**. It:

1. Fetches the latest citation count and H-index from Google Scholar
2. Regenerates `Shahriarirad_Reza_CV.docx` with fresh stats
3. Updates `index.html` fallback values
4. Commits and pushes all changes back to the repository

You can also trigger it manually: **Actions tab → Update CV Weekly → Run workflow**.

For this to work, the repository must have **read and write permissions** enabled:
**Settings → Actions → General → Workflow permissions → Read and write permissions → Save**

---

## Admin panel

The admin panel at `cv-admin.html` connects directly to GitHub via a Personal Access Token and lets you edit every section of your CV without touching code.

**To use it:**
1. Go to `https://github.com/settings/tokens/new?scopes=repo&description=CV+Admin`
2. Generate a token with **repo** scope
3. Open `cv-admin.html`, paste the token, enter `SoRRad/RezaShahriarirad_CV`
4. Click Connect

**What you can edit:**

| Section | Capabilities |
|---------|-------------|
| About & Headshot | Edit bio paragraphs, upload a new profile photo |
| Contact Info | Email, Mayo email, phone, location, research interests, languages |
| Mayo Research | IRB project count, description paragraph, specialty tags (add/remove) |
| Experience | Add, edit, or delete any timeline entry |
| Education | Add, edit, or delete any education entry |
| Leadership | Add, edit, or delete leadership entries |
| Skills | Add, edit, or delete skills with proficiency levels |
| Peer Reviews | Update count with optional journal name, manuscript count, and hyperlink |
| Publications | Add new papers; edit type, categories, authors, URL for any existing paper |
| Presentations | Add new presentations with month, year, location, and topic categories |
| Awards | Add new awards or edit existing ones |
| Patents | Add new patents or edit existing ones |
| Hobbies | Add, edit, or delete hobby entries |
| Deploy | Trigger the GitHub Actions workflow manually |

The token is stored in browser memory only and never persisted. Each session requires re-entering the token.

---

## Adding a new publication

### Via admin panel (recommended)
Go to admin panel → Publications → Add New Publication. Fill in year, type, authors, journal, and DOI, select topic categories, and click **Add & Push to GitHub**.

### Manual JSON edit
Add an entry to `cv_pubs.json` directly on GitHub:

```json
{
  "n": 194,
  "year": "2026",
  "type": "original",
  "title": "Your Paper Title Here",
  "authors": "Shahriarirad R*, Co-author A, Co-author B",
  "journal": "Journal Name",
  "url": "https://doi.org/...",
  "tags": [],
  "cat": ["plastic"]
}
```

**Type options:** `original`, `review`, `case`, `letter`

**Category keys:** `plastic`, `thoracic`, `vascular`, `gi`, `endocrine`, `ortho`, `burns`, `infectious`, `covid`, `oncology`, `transplant`, `ai`, `pulm`, `neuro`, `derm`, `urology`, `pubhealth`

**Author formatting:** Mark corresponding author with `*` after last initial — `Shahriarirad R*`. List all authors in full, no `et al.` The site auto-detects authorship position (1st, co-first, last, corresponding) from the author string.

After editing `cv_pubs.json`, also update `"pubCount"` in `cv_live_stats.json`.

---

## Adding a presentation

Via admin panel → Presentations → Add New Presentation. You can specify month, year, type (poster/oral), title, venue, location/country, and topic categories.

Or edit `cv_presentations.json` directly:

```json
{
  "date": "Mar 2026",
  "month": "Mar",
  "year": "2026",
  "type": "poster",
  "title": "Presentation title",
  "venue": "Conference name",
  "conference": "Short conference name",
  "location": "United States",
  "cat": ["plastic"]
}
```

---

## Updating peer reviews

1. Open `cv-admin.html` → Peer Reviews
2. Set the new total, optionally add journal and note
3. Click **Push to GitHub**

The count updates instantly on the live website.

---

## Local development

Open `index.html` in any browser — no build step or server required.

To regenerate the DOCX locally:

```bash
npm install docx
node cv_generator.js citations=3500 hindex=25 peerReviews=155 journals=68
```

---

## Profile links

| Platform | Link |
|----------|------|
| Google Scholar | https://scholar.google.com/citations?user=mOE1KmEAAAAJ |
| PubMed | https://www.ncbi.nlm.nih.gov/myncbi/reza.shahriari.1/bibliography/public/ |
| ORCID | https://orcid.org/0000-0001-5454-495X |
| Scopus | https://www.scopus.com/authid/detail.uri?authorId=57194698048 |
| Web of Science | https://www.webofscience.com/wos/author/record/ABC-9194-2020 |
| ResearchGate | https://www.researchgate.net/profile/Reza-Shahriarirad |
| LinkedIn | https://www.linkedin.com/in/reza-shahriarirad/ |

---

## Tech stack

- **Website:** Vanilla HTML/CSS/JavaScript — zero frameworks, zero build tools, zero dependencies
- **Fonts:** Cormorant Garamond + DM Sans via Google Fonts
- **DOCX generation:** [docx.js](https://docxjs.org/) (Node.js, runs server-side in GitHub Actions)
- **Live citations:** Google Scholar via CORS proxy (allorigins.win, corsproxy.io, codetabs.com)
- **CI/CD:** GitHub Actions — runs every Monday, self-commits updated stats and DOCX
