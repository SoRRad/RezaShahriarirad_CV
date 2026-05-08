@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  CV Push to GitHub
echo ============================================================
echo.

REM ── Detect changed CSV files ─────────────────────────────────
set "CSV_CHANGES="
for /f "tokens=*" %%F in ('git status --short ^| findstr "data\\"') do (
    set "LINE=%%F"
    set "LINE=!LINE: =!"
    for %%P in (!LINE!) do (
        set "NAME=%%~nxP"
        if not "!CSV_CHANGES!"=="" set "CSV_CHANGES=!CSV_CHANGES!, "
        set "CSV_CHANGES=!CSV_CHANGES!!NAME!"
    )
)

REM ── Generate commit message ───────────────────────────────────
if not "!CSV_CHANGES!"=="" (
    set "COMMIT_MSG=Update CV data: !CSV_CHANGES!"
) else (
    set "COMMIT_MSG=Update CV files"
)

echo Commit message: !COMMIT_MSG!
echo.

REM ── Stage all changes ─────────────────────────────────────────
git add .
if errorlevel 1 (
    echo ERROR: git add failed.
    echo Push failed. Check the error above.
    pause
    exit /b 1
)

REM ── Commit ───────────────────────────────────────────────────
git diff --cached --quiet
if %errorlevel%==0 (
    echo Nothing to commit — working tree is clean.
    goto open_browser
)

git commit -m "!COMMIT_MSG!"
if errorlevel 1 (
    echo ERROR: git commit failed.
    echo Push failed. Check the error above.
    pause
    exit /b 1
)

REM ── Push ─────────────────────────────────────────────────────
git push origin main
if errorlevel 1 (
    echo ERROR: git push failed.
    echo Push failed. Check the error above.
    pause
    exit /b 1
)

echo.
echo Pushed successfully. GitHub Actions is rebuilding your CV. Check the browser tab.

:open_browser
REM ── Open Actions page ────────────────────────────────────────
start "" "https://github.com/SoRRad/RezaShahriarirad_CV/actions"

echo.
echo Done. This window will close in 5 seconds.
timeout /t 5 /nobreak >nul
exit /b 0
