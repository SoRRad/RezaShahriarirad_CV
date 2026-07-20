#!/usr/bin/env bash
set -euo pipefail

MESSAGE="${1:-Update CV data and rebuild site}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "Repository: $REPO_ROOT"
echo "Checking current status..."
git status --short

echo "Fetching origin/main before build..."
git fetch origin main

echo "Rebasing local work on top of origin/main before build..."
if ! git pull --rebase --autostash origin main; then
  echo "Conflict during rebase. Resolve in VS Code, then run git rebase --continue and scripts/safe_push.ps1 again if needed." >&2
  exit 1
fi

echo "Validating CSV data..."
if ! python build/validate_data.py; then
  echo "Validation failed. Fix CSV errors before pushing." >&2
  exit 1
fi

echo "Building generated CV outputs..."
if ! python build/build.py; then
  echo "Build failed. Fix build errors before pushing." >&2
  exit 1
fi

echo "Running smoke tests..."
if ! python build/smoke_test.py; then
  echo "Smoke test failed. Fix generated site or data issues before pushing." >&2
  exit 1
fi

echo "Staging CV data, build source, generated outputs, and workflow files..."
git add \
  data/*.csv \
  index.html \
  Shahriarirad_Reza_CV.docx \
  Shahriarirad_Reza_CV.pdf \
  cv_*.json \
  build/*.py \
  build/static_assets/*.js \
  build/static_assets/*.css \
  assets \
  scripts \
  .github/workflows/update-cv.yml \
  .gitignore \
  README.md \
  tools/admin-local/cv-admin.html

if git diff --staged --quiet; then
  echo "No staged changes to commit."
else
  echo "Committing staged changes..."
  git commit -m "$MESSAGE"
fi

echo "Fetching origin/main..."
git fetch origin main

echo "Rebasing on top of origin/main with autostash..."
if ! git pull --rebase --autostash origin main; then
  echo "Conflict during rebase. Resolve in VS Code, then run git rebase --continue and scripts/safe_push.ps1 again if needed." >&2
  exit 1
fi

echo "Pushing to origin/main..."
if ! git push origin main; then
  echo "Push failed. Check remote status and authentication." >&2
  exit 1
fi

echo "Successfully synced, built, committed, rebased, and pushed."
