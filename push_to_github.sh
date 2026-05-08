#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " CV Push to GitHub"
echo "============================================================"
echo

# ── Detect changed CSV files ─────────────────────────────────────
CSV_FILES=$(git status --short | grep 'data/' | awk '{print $NF}' | xargs -I{} basename {} | paste -sd ', ')

if [[ -n "$CSV_FILES" ]]; then
  COMMIT_MSG="Update CV data: $CSV_FILES"
else
  COMMIT_MSG="Update CV files"
fi

echo "Commit message: $COMMIT_MSG"
echo

# ── Stage all changes ─────────────────────────────────────────────
git add .

# ── Commit ────────────────────────────────────────────────────────
if git diff --cached --quiet; then
  echo "Nothing to commit — working tree is clean."
else
  git commit -m "$COMMIT_MSG"
fi

# ── Push ──────────────────────────────────────────────────────────
git push origin main

echo
echo "Pushed successfully. GitHub Actions is rebuilding your CV. Check the browser tab."

# ── Open Actions page (macOS) ─────────────────────────────────────
if command -v open &>/dev/null; then
  open "https://github.com/SoRRad/RezaShahriarirad_CV/actions"
elif command -v xdg-open &>/dev/null; then
  xdg-open "https://github.com/SoRRad/RezaShahriarirad_CV/actions"
fi
