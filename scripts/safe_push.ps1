param(
  [string]$Message = "Update CV data and rebuild site"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $RepoRoot

function Invoke-GitStep {
  param(
    [string]$FailureMessage,
    [scriptblock]$Command
  )
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw $FailureMessage
  }
}

Write-Host "Repository: $RepoRoot"
Write-Host "Checking current status..."
git status --short

Write-Host "Validating CSV data..."
Invoke-GitStep "Validation failed. Fix CSV errors before pushing." {
  python build/validate_data.py
}

Write-Host "Building generated CV outputs..."
Invoke-GitStep "Build failed. Fix build errors before pushing." {
  python build/build.py
}

Write-Host "Staging CV data, build source, generated outputs, and workflow files..."
git add `
  data/*.csv `
  index.html `
  Shahriarirad_Reza_CV.docx `
  Shahriarirad_Reza_CV.pdf `
  cv_*.json `
  build/*.py `
  build/static_assets/*.js `
  build/static_assets/*.css `
  assets `
  .github/workflows/update-cv.yml `
  .gitignore `
  README.md `
  scripts/safe_push.ps1 `
  scripts/safe_push.sh `
  push_to_github.bat `
  push_to_github.sh `
  tools/admin-local/cv-admin.html
if ($LASTEXITCODE -ne 0) {
  throw "git add failed. Check the staged file list and repository state."
}

git diff --staged --quiet
if ($LASTEXITCODE -eq 1) {
  Write-Host "Committing staged changes..."
  Invoke-GitStep "Commit failed. Check Git identity or staged files." {
    git commit -m $Message
  }
} elseif ($LASTEXITCODE -eq 0) {
  Write-Host "No staged changes to commit."
} else {
  throw "Could not inspect staged changes."
}

Write-Host "Fetching origin/main..."
Invoke-GitStep "Fetch failed. Check network access and remote configuration." {
  git fetch origin main
}

Write-Host "Rebasing on top of origin/main with autostash..."
git pull --rebase --autostash origin main
if ($LASTEXITCODE -ne 0) {
  throw "Remote changes were found and a conflict occurred. Resolve conflicts in VS Code, then run git rebase --continue and git push origin main."
}

Write-Host "Pushing to origin/main..."
git push origin main
if ($LASTEXITCODE -ne 0) {
  throw "Push failed. Check remote status and authentication."
}

Write-Host "Successfully synced, built, committed, rebased, and pushed."
