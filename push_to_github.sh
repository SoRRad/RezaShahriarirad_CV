#!/usr/bin/env bash
set -euo pipefail

MESSAGE="${1:-Update CV data and rebuild site}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================================"
echo " CV Safe Sync to GitHub"
echo "============================================================"
echo

bash "$SCRIPT_DIR/scripts/safe_push.sh" "$MESSAGE"

echo
echo "GitHub Actions should now validate, rebuild, and deploy the CV."
if command -v open >/dev/null 2>&1; then
  open "https://github.com/SoRRad/RezaShahriarirad_CV/actions"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "https://github.com/SoRRad/RezaShahriarirad_CV/actions"
fi
