# Reza Shahriarirad, M.D. - Academic CV Website

Academic CV website for Dr. Reza Shahriarirad, Research Fellow at the Surgery Innovation Center, Mayo Clinic.

Live site: `https://SoRRad.github.io/RezaShahriarirad_CV/`

## CSV-First Workflow

The canonical CV content lives in structured CSV files under `data/`. The build system reads those CSV files and regenerates:

- `index.html`
- `Shahriarirad_Reza_CV.docx`
- `Shahriarirad_Reza_CV.pdf`
- legacy generated JSON files: `cv_pubs.json`, `cv_presentations.json`, `cv_journals.json`, and `cv_live_stats.json`

Do not manually edit generated outputs. Make content changes in `data/*.csv`, then run the build or push to `main` and let GitHub Actions rebuild the site.

## Local Build

```bash
pip install -r build/requirements.txt
python build/validate_data.py
python build/build.py
```

The build validates CSV data, regenerates legacy JSON artifacts, then generates the website, Word CV, and PDF CV.

## Updating Content

Use the CSV files in `data/`:

| File | Purpose |
| --- | --- |
| `data/profile.csv` | Name, title, bio, public/private contact fields, profile links, cached metrics, SEO text |
| `data/publications.csv` | Publication list, authorship tags, topic categories, DOI/URLs |
| `data/presentations.csv` | Conference presentations and filters |
| `data/projects.csv` | Public-facing selected innovation projects |
| `data/affiliations.csv` | Compact lab and institutional affiliations |
| `data/experience.csv` | Professional experience |
| `data/education.csv` | Education |
| `data/leadership.csv` | Leadership and service |
| `data/awards.csv` | Awards and honours |
| `data/patents.csv` | Patents and innovations |
| `data/editorial.csv` | Editorial roles |
| `data/journals.csv` | Journals reviewed |
| `data/references.csv` | Professional references |
| `data/skills_computing.csv` | Computing skills |
| `data/skills_interpersonal.csv` | Interpersonal skills |
| `data/hobbies.csv` | Interests |
| `data/open_source.csv` | Public open-source repositories, if any |

### Publications

Add or edit rows in `data/publications.csv`. Required fields include `n`, `year`, `type`, `title`, `authors`, and `journal`.

Valid publication types: `original`, `review`, `case`, `letter`.

Use semicolon-separated category keys from `build/utils.py` for `cat` and `highlight_topics`. Preserve corresponding author markers such as `Shahriarirad R*`.

### Presentations

Edit `data/presentations.csv`. Required fields include `date`, `type`, `title`, `venue`, and `location`.

Valid presentation types: `poster`, `oral`.

### Profile And Metrics

Edit `data/profile.csv`.

- Public website contact uses fields marked public-visible, currently the Mayo email only.
- Personal Gmail and phone can remain in the CSV for private generated CV outputs, but they are not rendered on the public website.
- Cached metrics use `citations_cached`, `h_index_cached`, `peer_reviews`, `journals_reviewed`, `manuscripts_reviewed`, and `metrics_last_updated`.
- The public site does not fetch live Google Scholar data in the browser.

### Selected Innovation Projects

Edit `data/projects.csv`. Only rows with `public_visible` set to `yes` are shown on the public website. Keep descriptions concise and public-safe.

## Generated Files

These files are generated artifacts and should not be edited manually:

- `index.html`
- `Shahriarirad_Reza_CV.docx`
- `Shahriarirad_Reza_CV.pdf`
- `cv_pubs.json`
- `cv_presentations.json`
- `cv_journals.json`
- `cv_live_stats.json`

If a generated file needs to change, update the relevant CSV or build source, then run `python build/build.py`.

## GitHub Actions And Pages

`.github/workflows/update-cv.yml` validates CSV files, rebuilds all generated outputs, commits only when generated files changed, and deploys the public site to GitHub Pages.

The deployed public site is intentionally limited to:

- `index.html`
- `Shahriarirad_Reza_CV.docx`
- `Shahriarirad_Reza_CV.pdf`

The workflow attempts to refresh cached metrics, but scraping failures are non-fatal and should not break the site build.

## Legacy Local Admin

The browser admin panel has been moved to `tools/admin-local/cv-admin.html` and is legacy/local-only. It is not linked from the public website and should not be served publicly because it asks for a GitHub token and may still write legacy JSON files. Prefer editing CSV files directly.
