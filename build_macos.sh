#!/usr/bin/env bash
# =============================================================
# build_macos.sh
# Builds TeamsAlive into a distributable .dmg for macOS.
# No Python required on the end-user's machine.
#
# Prerequisites (only needed on YOUR build machine):
#   1. macOS 11+
#   2. Python 3.9+  (brew install python  OR  python.org)
#   3. Run this script – it installs everything else automatically
# =============================================================

set -euo pipefail

APP_NAME="TeamsAlive"
BUNDLE_ID="com.yourname.teamsalive"
VERSION="1.0"
DMG_NAME="${APP_NAME}-${VERSION}-macOS.dmg"
DIST_DIR="dist"

echo ""
echo " ============================================="
echo "  ${APP_NAME}  |  macOS Build Script"
echo " ============================================="
echo ""

# ── 1. Check Python ──────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] python3 not found."
    echo "         Install via: brew install python   OR   https://python.org"
    exit 1
fi
PYTHON=$(command -v python3)
echo " [OK] Python: $($PYTHON --version)"

# ── 2. Install dependencies ──────────────────────────────────
echo " [..] Installing dependencies..."
$PYTHON -m pip install --upgrade pip --quiet
$PYTHON -m pip install pyinstaller pyautogui Pillow pystray --quiet
echo " [OK] Dependencies installed"

# ── 3. PyInstaller – .app bundle (Including icon data) ────
echo " [..] Building .app bundle..."
$PYTHON -m PyInstaller \
    --noconfirm \
    --onefile \
    --windowed \
    --clean \
    --name "$APP_NAME" \
    --icon "icon.icns" \
    --osx-bundle-identifier "$BUNDLE_ID" \
    --add-data "icon.ico:." \
    --add-data "icon.png:." \
    --hidden-import pystray._darwin \
    --hidden-import PIL._tkinter_finder \
    --info-plist-additions '{"NSHighResolutionCapable": true, "LSUIElement": true}' \
    teams_alive.py

echo " [OK] ${DIST_DIR}/${APP_NAME}.app created"

# ── 4. Wrap .app in a distributable .dmg ─────────────────────
echo " [..] Creating DMG..."

# Temporary staging folder
STAGING=$(mktemp -d)
cp -r "${DIST_DIR}/${APP_NAME}.app" "${STAGING}/"

# Symlink to /Applications so user can drag-and-drop
ln -s /Applications "${STAGING}/Applications"

# Create the DMG
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$STAGING" \
    -ov \
    -format UDZO \
    "$DMG_NAME"

rm -rf "$STAGING"
echo " [OK] ${DMG_NAME} created"

# ── 5. Remind about Gatekeeper / notarisation ────────────────
echo ""
echo " ============================================="
echo "  Build complete!"
echo ""
echo "  App bundle : ${DIST_DIR}/${APP_NAME}.app"
echo "  DMG        : ${DMG_NAME}"
echo ""
echo "  Distribution notes:"
echo "   • For personal/team use: share the .dmg directly."
echo "   • First launch on a new Mac: right-click › Open"
echo "     (bypasses Gatekeeper for unsigned apps)."
echo "   • For public distribution: sign & notarise with:"
echo "     codesign --deep -s 'Developer ID Application: YOU' dist/${APP_NAME}.app"
echo "     xcrun notarytool submit ${DMG_NAME} --apple-id ... --wait"
echo ""
echo "  End-user setup (one-time, ~10 sec):"
echo "   System Settings › Privacy & Security › Accessibility"
echo "   → add ${APP_NAME}.app   (needed to move the mouse)"
echo " ============================================="
echo ""
