@echo off
echo ==========================================
echo Semgrep Installation Script
echo ==========================================
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo X pip not found. Please install Python and pip first.
    exit /b 1
)

echo Installing Semgrep...
pip install semgrep

REM Verify installation
semgrep --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo X Installation failed. Try manual installation:
    echo    pip install semgrep
    exit /b 1
) else (
    echo.
    echo √ Semgrep installed successfully!
    echo.
    semgrep --version
    echo.
    echo You're ready to use Semgrep!
    echo.
    echo Next steps:
    echo   1. Run test: python test_semgrep.py
    echo   2. Run full scan: python test_real_scan.py
    echo   3. Read docs: type SEMGREP_INTEGRATION.md
)
