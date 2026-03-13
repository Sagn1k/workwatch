#!/bin/bash
# WorkWatch Release Script
# Builds the binary, creates release tarballs, and generates checksums.
# Run this on macOS to produce the release artifacts.
#
# Usage: ./scripts/release.sh [version]
#   version defaults to reading from workwatch/__init__.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info() { echo -e "${CYAN}ℹ${NC} $1"; }
success() { echo -e "${GREEN}✅${NC} $1"; }

# Get version
VERSION="${1:-$(python3 -c "import workwatch; print(workwatch.__version__)")}"
ARCH=$(uname -m)
RELEASE_DIR="release"
DIST_DIR="dist"

echo ""
echo -e "${BOLD}WorkWatch Release Builder v${VERSION}${NC}"
echo -e "Architecture: ${ARCH}"
echo ""

# ── Build ─────────────────────────────────────────────────────────

VENV_DIR="${PROJECT_DIR}/.venv-build"

if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating build virtualenv..."
    python3 -m venv "$VENV_DIR"
fi

source "${VENV_DIR}/bin/activate"

info "Installing build dependencies..."
pip install pyinstaller --quiet

info "Building binary..."
pyinstaller workwatch.spec --clean --noconfirm 2>&1 | tail -3

if [[ ! -f "${DIST_DIR}/workwatch" ]]; then
    echo "❌ Build failed — no binary produced."
    exit 1
fi

success "Binary built: $(ls -lh ${DIST_DIR}/workwatch | awk '{print $5}')"

# ── Package ───────────────────────────────────────────────────────

mkdir -p "$RELEASE_DIR"

TAR_NAME="workwatch-${VERSION}-darwin-${ARCH}.tar.gz"

info "Creating ${TAR_NAME}..."
cd "$DIST_DIR"
tar -czf "../${RELEASE_DIR}/${TAR_NAME}" workwatch
cd "$PROJECT_DIR"

# ── Checksum ──────────────────────────────────────────────────────

info "Generating checksums..."
cd "$RELEASE_DIR"
shasum -a 256 "$TAR_NAME" > "${TAR_NAME}.sha256"
cd "$PROJECT_DIR"

# ── Summary ───────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}Release artifacts:${NC}"
ls -lh "${RELEASE_DIR}/"
echo ""
echo -e "${BOLD}Checksum:${NC}"
cat "${RELEASE_DIR}/${TAR_NAME}.sha256"
echo ""
success "Done! Upload contents of ${RELEASE_DIR}/ to your server:"
echo ""
echo -e "  scp ${RELEASE_DIR}/* your-server:/var/www/sagnikbhowmick.com/workwatch/releases/"
echo -e "  scp scripts/install.sh your-server:/var/www/sagnikbhowmick.com/workwatch/install.sh"
echo ""
