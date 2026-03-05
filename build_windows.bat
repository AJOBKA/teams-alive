@echo off
:: ============================================================
:: build_windows.bat
:: Builds TeamsAlive into a single-file installer for Windows.
:: No Python required on the end-user's machine.
::
:: Prerequisites (only needed on YOUR build machine):
::   1. Python 3.9+  (python.org)
::   2. Run this script – it installs everything else automatically
:: ============================================================

setlocal enabledelayedexpansion
title TeamsAliveWin – Windows Build

echo.
echo  =============================================
echo   TeamsAliveWin  ^|  Windows Build Script
echo  =============================================
echo.

:: ── 1. Check Python ─────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)
echo  [OK] Python found

:: ── 2. Install / upgrade dependencies ───────────────────────
echo  [..] Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install pyinstaller pyautogui Pillow pystray --quiet
if errorlevel 1 ( echo  [ERROR] pip install failed & pause & exit /b 1 )
echo  [OK] Dependencies installed

:: ── 3. PyInstaller – one-file EXE (Python bundled inside) ───
echo  [..] Building standalone EXE...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --name TeamsAliveWin ^
    --icon "icon.ico" ^
    --add-data "icon.ico;." ^
    --add-data "icon.png;." ^
    --hidden-import pystray._win32 ^
    --hidden-import PIL._tkinter_finder ^
    teams_alive.py
if errorlevel 1 ( echo  [ERROR] PyInstaller failed & pause & exit /b 1 )
echo  [OK] dist\TeamsAliveWin.exe created

:: ── 4. NSIS installer (optional – skip if makensis not found) ─
where makensis >nul 2>&1
if errorlevel 1 (
    echo  [SKIP] NSIS not found – skipping installer. Get it at https://nsis.sourceforge.io
    echo         The standalone dist\TeamsAliveWin.exe is still fully usable without an installer.
    goto :done
)

echo  [..] Building NSIS installer...
makensis installer.nsi
if errorlevel 1 ( echo  [WARN] NSIS build failed – EXE still available in dist\ )
echo  [OK] TeamsAliveWin-Setup.exe created

:done
echo.
echo  =============================================
echo   Build complete!
echo.
echo   Standalone EXE : dist\TeamsAliveWin.exe
echo   Setup installer: TeamsAliveWin-Setup.exe  (if NSIS was available)
echo.
echo   Both run on any Windows 10/11 PC with no Python required.
echo  =============================================
echo.
pause
