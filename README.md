# Reza Shahriarirad, M.D. — Academic CV Website

Personal academic CV website for Dr. Reza Shahriarirad, Research Fellow at the Surgery Innovation Center, Mayo Clinic. Built as a single self-contained HTML file with live data integration and an auto-updating downloadable CV.

**Live site:** `https://rezashahriarirad.github.io`

---

## What this repository contains

| File | Description |
|------|-------------|
| `index.html` | The full CV website — single HTML file, no dependencies |
| `Shahriarirad_Reza_CV.docx` | Downloadable CV in Word format, auto-regenerated weekly |
| `cv_generator.js` | Node.js script that builds the DOCX from live data |
| `cv_pubs.json` | All 193 publications as structured JSON |
| `cv_journals.json` | 67 peer-reviewed journals as structured JSON |
| `cv_presentations.json` | 17 conference presentations as structured JSON |
| `cv_live_stats.json` | Latest fetched metrics (citations, H-index, reviews) |
| `.github/workflows/update-cv.yml` | GitHub Actions workflow for weekly auto-updates |

---

## Features

- **Live citation metrics** — Google Scholar data fetched in the browser on every visit (citations, H-index)
- **Live peer review stats** — Web of Science profile scraped for verified review count
- **193 publications** — Searchable and filterable by article type, authorship role (1st, 2nd/co-first, corresponding, last), and 17 specialty topics
- **Auto-updating DOCX** — GitHub Actions runs every Monday to regenerate the CV with fresh stats
- **Self-contained** — The entire website including the headshot photo is embedded in one HTML file; no server, no CDN, no external assets required at runtime

---

## Auto-update mechanism

A GitHub Actions workflow (`.github/workflows/update-cv.yml`) runs automatically every Monday at 6:00 AM UTC. It:

1. Fetches the latest citation count and H-index from Google Scholar
2. Fetches the latest peer review count from Web of Science
3. Runs `cv_generator.js` to rebuild `Shahriarirad_Reza_CV.docx` with the new numbers
4. Updates the fallback stats in `index.html`
5. Commits and pushes the updated files back to the repository

You can also trigger it manually at any time from the **Actions** tab → **Update CV Weekly** → **Run workflow**.

---

## Updating publications

When you publish a new paper, add an entry to `cv_pubs.json`. Each entry follows this structure:

```json
{
  "n": 194,
  "year": "2026",
  "type": "original",
  "title": "Your Paper Title Here",
  "authors": "Shahriarirad R*, Co-author A, Co-author B",
  "journal": "Journal Name",
  "url": "https://doi.org/..."
}
```

**Type options:** `original`, `case`, `letter`

**Author formatting rules (important for filters to work correctly):**
- Mark corresponding author with `*` directly after the last initial: `Shahriarirad R*`
- List all authors in order, comma-separated — no `et al.`
- The website automatically detects your authorship position from the author string

After editing `cv_pubs.json`, also update the publication count in `cv_live_stats.json` (`"pubCount"`) and in `index.html` (search for `id="hero-pubs"`).

---

## Updating other sections

| What to update | Where |
|---|---|
| New presentation | `cv_presentations.json` |
| New journal reviewed | `cv_journals.json` |
| New award, patent, or position | Edit `index.html` directly — find the relevant section |
| Reference contact info | Edit `index.html` — search for `refs-grid` |

---

## Local development

To preview the site locally, just open `index.html` in any browser — no build step or server needed.

To regenerate the DOCX manually with custom stats:

```bash
npm install docx
node cv_generator.js citations=3500 hindex=25 peerReviews=155 journals=68 date="March 2026"
```

This writes a fresh `Shahriarirad_CV_Generated.docx` to the current directory.

---

## Tech stack

- **Website:** Vanilla HTML/CSS/JavaScript — no frameworks, no build tools
- **Fonts:** Cormorant Garamond + DM Sans via Google Fonts
- **DOCX generation:** [docx.js](https://docxjs.org/) (Node.js, server-side only)
- **Live data:** Google Scholar via allorigins.win CORS proxy; Web of Science direct
- **CI/CD:** GitHub Actions

---

## Profile links

| Platform | URL |
|---|---|
| Google Scholar | https://scholar.google.com/citations?user=mOE1KmEAAAAJ |
| PubMed | https://www.ncbi.nlm.nih.gov/myncbi/reza.shahriari.1/bibliography/public/ |
| ORCID | https://orcid.org/0000-0001-5454-495X |
| Scopus | https://www.scopus.com/authid/detail.uri?authorId=57194698048 |
| Web of Science | https://www.webofscience.com/wos/author/record/ABC-9194-2020 |
| ResearchGate | https://www.researchgate.net/profile/Reza-Shahriarirad |
| LinkedIn | https://www.linkedin.com/in/reza-shahriarirad/ |
| GitHub | https://github.com/SoRRad |
