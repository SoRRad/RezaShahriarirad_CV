@echo off
setlocal

set "COMMIT_MSG=%~1"
if "%COMMIT_MSG%"=="" set "COMMIT_MSG=Update CV data and rebuild site"

echo ============================================================
echo  CV Safe Sync to GitHub
echo ============================================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\safe_push.ps1" -Message "%COMMIT_MSG%"
if errorlevel 1 (
    echo.
    echo Safe push failed. Read the error above.
    pause
    exit /b 1
)

start "" "https://github.com/SoRRad/RezaShahriarirad_CV/actions"
echo.
echo Done. GitHub Actions should now validate, rebuild, and deploy the CV.
timeout /t 5 /nobreak >nul
exit /b 0
