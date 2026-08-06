# Reza Shahriarirad, M.D. - Academic CV Website

Academic CV website for Dr. Reza Shahriarirad, Research Fellow in Department of Surgery - Surgical Innovation at Mayo Clinic.

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
python build/smoke_test.py
```

The build validates CSV data, regenerates legacy JSON artifacts, then generates the website, Word CV, and PDF CV. The smoke test confirms the newest publication, generated JSON, download links, filter elements, tag chips, and lab-logo markup are present.

## Optional: NIH Biosketch

`build/build_biosketch.py` generates an NIH Non-Fellowship Biographical Sketch from the same CSV data. It is a manual, optional tool — it is not part of `build/build.py` and is not deployed:

```bash
python build/build_biosketch.py                      # general biosketch
python build/build_biosketch.py --project "Project Name"
```

The output, `Shahriarirad_NIH_Biosketch_General.docx`, is git-ignored; regenerate it whenever you need a current copy.

## Editing CSV Files Safely

Excel's warning that "some features might be lost" is normal when saving as CSV. CSV files cannot store workbook formatting, formulas, filters, colors, or multiple sheets, but that does not affect the website as long as the plain CSV data is preserved.

- Save from Excel as **CSV UTF-8 (Comma delimited) (*.csv)**.
- Keep the file extension as `.csv`; do not save the build inputs as `.xlsx`.
- Preserve the header row exactly.
- Do not leave trailing commas in header rows or comment guide rows.
- Quote any field that contains a comma, for example `"Author A, Author B"`.
- Use semicolons inside multi-value fields such as `tags`, `cat`, `keywords`, and `highlight_topics`.
- Use only subcategory keys from `build/utils.py` in `cat` and `highlight_topics`; do not use top-level group keys such as `surgery`, `internal_medicine`, `ai`, or `health_sciences`.
- Run `python build/validate_data.py` before pushing.
- Then run `scripts/safe_push.ps1` to validate, build, commit, pull/rebase, and push.

The validator checks for common CSV/Excel issues including UTF-8 BOMs, hidden tabs or non-breaking spaces, missing required columns, invalid category keys, invalid publication or presentation types, duplicate publication numbers, bad yes/no flags, and extra columns usually caused by unquoted commas.

## Safe Push Workflow

From the repository root on Windows PowerShell, use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/safe_push.ps1 -Message "Update publications"
```

For general CV data updates, this is the usual command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/safe_push.ps1 -Message "Update CV data"
```

This script fetches `origin/main`, pulls with `--rebase --autostash`, validates the CSV files, rebuilds `index.html`, DOCX, PDF, and JSON outputs, runs smoke tests, stages the relevant CV files, commits only when there are staged changes, fetches/pulls again, and then pushes. It does not force-push; if a conflict occurs, resolve it in VS Code, then run `git rebase --continue` and rerun the safe push command if needed.

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
| `data/skills_research.csv` | Research and analytical skills |
| `data/skills_interpersonal.csv` | Interpersonal skills |
| `data/hobbies.csv` | Hobbies and extracurricular interests |
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
- Phone can remain in the CSV for private reference, but it is hidden from both the public website and the generated downloadable DOCX/PDF CV.
- Cached metrics use `citations_cached`, `h_index_cached`, `peer_reviews`, `journals_reviewed`, `manuscripts_reviewed`, and `metrics_last_updated`.
- The public site does not fetch live Google Scholar data in the browser.

#### Keeping citation metrics current

Google Scholar blocks automated scraping from GitHub Actions (HTTP 403), so the workflow's metric refresh almost never succeeds on its own. The practical routine is:

1. Open your [Google Scholar profile](https://scholar.google.com/citations?user=mOE1KmEAAAAJ&hl=en) roughly once a month.
2. Update `citations_cached`, `h_index_cached`, and `metrics_last_updated` in `data/profile.csv` (and `peer_reviews` / `journals_reviewed` / `manuscripts_reviewed` when they change).
3. Push with the safe-push script; the build regenerates everything else.

The weekly build now prints a workflow warning when `metrics_last_updated` is more than 45 days old, so a stale number surfaces in the Actions summary instead of silently aging. The smoke test enforces that cached metrics never go *down* (floor checks) but no longer pins exact values, so a successful refresh cannot break the build.

Authorship counts (`first`/`co-first`/`last`/`corresponding`) come from the explicit `tags` column in `data/publications.csv`, which is curated against full author lists. The website's authorship filter treats those tags as authoritative; keep them up to date when adding publications.

### Innovation Project Data

`data/projects.csv` is retained for structured project data, but selected innovation projects are not rendered on the public website.

## Generated Files

These files are generated artifacts and should not be edited manually:

- `index.html`
- `Shahriarirad_Reza_CV.docx` (kept in the repo, **not** deployed publicly)
- `Shahriarirad_Reza_CV.pdf`
- `cv_pubs.json`
- `cv_presentations.json`
- `cv_journals.json`
- `cv_live_stats.json`
- `sitemap.xml`

If a generated file needs to change, update the relevant CSV or build source, then run `python build/build.py`.

### Privacy

- The phone number is **not** stored in the repository. `data/profile.csv` keeps `phone` blank and `phone_public_visible,no`. If a private local phone is ever needed, put it in `data/profile_private.csv` (git-ignored) — never commit it.
- The Word CV (`Shahriarirad_Reza_CV.docx`) is generated and committed but is never copied into the public GitHub Pages payload; the public page links to the PDF only. The workflow fails if a DOCX ends up in the deployment payload.

## GitHub Actions And Pages

`.github/workflows/update-cv.yml` runs on pushes to `main` that change CSV data, build sources, assets, or the workflow. It validates CSV files, rebuilds all generated outputs, commits only when generated files changed, and deploys the public site to GitHub Pages.

The deployed public site includes:

- `index.html`
- `Shahriarirad_Reza_CV.pdf` (the Word `.docx` is intentionally excluded)
- generated JSON files for compatibility
- `robots.txt` and `sitemap.xml`
- required static asset folders such as `assets/`, `images/`, `img/`, `public/`, `static/`, and `build/static_assets/logos/` when present

The workflow attempts to refresh cached metrics, but scraping failures are non-fatal and should not break the site build. When cached metrics are more than 45 days old, the workflow emits a warning in the run summary as a reminder to update `data/profile.csv` manually (see "Keeping citation metrics current" above).

Preferred GitHub Pages configuration is **Deploy from a branch -> `gh-pages` / root**. If the repository is instead configured to publish from `main` / root, the workflow still commits the rebuilt generated files back to `main`, so CSV-only pushes can update the live site after validation passes. If a valid build/deploy finishes but the live site is still stale, check **Settings -> Pages** and browser/CDN cache before editing generated files manually.

## Legacy Local Admin

The browser admin panel has been moved to `tools/admin-local/cv-admin.html` and is legacy/local-only. It is not linked from the public website and should not be served publicly because it asks for a GitHub token. It cannot perform a local `git pull --rebase`; browser GitHub API writes re-check the latest remote file SHA and stop if the remote changed.

> **Do not use it to write CV content.** The file still contains hard-coded copies of an older bio, institution name, and experience list. Saving from it would overwrite the current `data/*.csv` values and regress the CV. It is retained only for reference. Edit the CSV files directly and publish with `scripts/safe_push.ps1`.
