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

## Editing CSV Files Safely

Excel's warning that "some features might be lost" is normal when saving as CSV. CSV files cannot store workbook formatting, formulas, filters, colors, or multiple sheets, but that does not affect the website as long as the plain CSV data is preserved.

- Save from Excel as **CSV UTF-8 (Comma delimited) (*.csv)**.
- Keep the file extension as `.csv`; do not save the build inputs as `.xlsx`.
- Preserve the header row exactly.
- Quote any field that contains a comma, for example `"Author A, Author B"`.
- Use semicolons inside multi-value fields such as `tags`, `cat`, `keywords`, and `highlight_topics`.
- Run `python build/validate_data.py` before pushing.

The validator checks for common CSV/Excel issues including UTF-8 BOMs, hidden tabs or non-breaking spaces, missing required columns, invalid category keys, invalid publication or presentation types, duplicate publication numbers, bad yes/no flags, and extra columns usually caused by unquoted commas.

## Updating Content

Use the CSV files in `data/`:

| File | Purpose |
| --- | --- |
| `data/profile.csv` | Name, title, bio, public/private contact fields, profile links, cached metrics, SEO text |
| `data/publications.csv` | Publication list, authorship tags, topic categories, DOI/URLs |
| `data/presentations.csv` | Conference presentations and filters |
| `data/projects.csv` | Stored innovation project data; not rendered on the public website |
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

- Public website contact renders email fields marked public-visible, currently the Mayo email and personal Gmail.
- Phone can remain in the CSV for private generated CV outputs, but it is not rendered publicly unless `phone_public_visible` is set to `yes`.
- Cached metrics use `citations_cached`, `h_index_cached`, `peer_reviews`, `journals_reviewed`, `manuscripts_reviewed`, and `metrics_last_updated`.
- The public site does not fetch live Google Scholar data in the browser.

### Innovation Project Data

`data/projects.csv` is retained for structured project data, but selected innovation projects are not rendered on the public website.

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

`.github/workflows/update-cv.yml` runs on pushes to `main` that change CSV data, build sources, assets, or the workflow. It validates CSV files, rebuilds all generated outputs, commits only when generated files changed, and deploys the public site to GitHub Pages.

The deployed public site includes:

- `index.html`
- `Shahriarirad_Reza_CV.docx`
- `Shahriarirad_Reza_CV.pdf`
- generated JSON files for compatibility
- `assets/` when present

The workflow attempts to refresh cached metrics, but scraping failures are non-fatal and should not break the site build.

Preferred GitHub Pages configuration is **Deploy from a branch -> `gh-pages` / root**. If the repository is instead configured to publish from `main` / root, the workflow still commits the rebuilt generated files back to `main`, so CSV-only pushes can update the live site after validation passes. If a valid build/deploy finishes but the live site is still stale, check **Settings -> Pages** and browser/CDN cache before editing generated files manually.

## Legacy Local Admin

The browser admin panel has been moved to `tools/admin-local/cv-admin.html` and is legacy/local-only. It is not linked from the public website and should not be served publicly because it asks for a GitHub token and may still write legacy JSON files. Prefer editing CSV files directly.
