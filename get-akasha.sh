#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
#  Akasha Installer — One-line install for Akasha server
#
#  Usage:
#    curl -fsSL https://raw.githubusercontent.com/ocuil/akasha-public/main/deploy/get-akasha.sh | bash
#
#  Or with a specific version:
#    curl -fsSL ... | bash -s -- --version 1.0.8
# ──────────────────────────────────────────────────────────────────

set -euo pipefail

VERSION="${1:-latest}"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
GITHUB_REPO="ocuil/akasha-public"
BINARY_NAME="akasha"

# ── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info()  { echo -e "  ${CYAN}→${RESET} $1"; }
ok()    { echo -e "  ${GREEN}✓${RESET} $1"; }
warn()  { echo -e "  ${YELLOW}⚠${RESET} $1"; }
error() { echo -e "  ${RED}✗${RESET} $1"; exit 1; }

# ── Banner ────────────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}╔══════════════════════════════════════════════╗${RESET}"
echo -e "  ${BOLD}║    ${CYAN}Akasha${RESET}${BOLD} — Shared Cognitive Fabric Installer  ║${RESET}"
echo -e "  ${BOLD}╚══════════════════════════════════════════════╝${RESET}"
echo ""

# ── Detect OS and Architecture ────────────────────────────────────
detect_platform() {
    local os arch

    case "$(uname -s)" in
        Linux)  os="linux" ;;
        Darwin) os="darwin" ;;
        *)      error "Unsupported OS: $(uname -s). Akasha supports Linux and macOS." ;;
    esac

    case "$(uname -m)" in
        x86_64|amd64)   arch="amd64" ;;
        aarch64|arm64)  arch="arm64" ;;
        *)              error "Unsupported architecture: $(uname -m). Akasha supports amd64 and arm64." ;;
    esac

    echo "${os}-${arch}"
}

PLATFORM=$(detect_platform)
info "Platform: ${BOLD}${PLATFORM}${RESET}"

# ── Resolve version ──────────────────────────────────────────────
if [ "$VERSION" = "latest" ] || [ "$VERSION" = "--version" ]; then
    # If --version flag, grab next arg
    if [ "$VERSION" = "--version" ] && [ -n "${2:-}" ]; then
        VERSION="$2"
    else
        info "Fetching latest version..."
        VERSION=$(curl -fsSL "https://api.github.com/repos/${GITHUB_REPO}/releases/latest" \
            | grep '"tag_name"' | head -1 | sed 's/.*"v\?\([^"]*\)".*/\1/')

        if [ -z "$VERSION" ]; then
            VERSION="1.0.8"
            warn "Could not detect latest version, using ${VERSION}"
        fi
    fi
fi

# Remove 'v' prefix if present
VERSION="${VERSION#v}"
info "Version: ${BOLD}v${VERSION}${RESET}"

# ── Download ─────────────────────────────────────────────────────
TARBALL="akasha-v${VERSION}-${PLATFORM}.tar.gz"
DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/download/v${VERSION}/${TARBALL}"

info "Downloading ${BOLD}${TARBALL}${RESET}..."

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

if ! curl -fsSL -o "${TMPDIR}/${TARBALL}" "${DOWNLOAD_URL}" 2>/dev/null; then
    error "Download failed. Check that version ${VERSION} exists at:\n       ${DOWNLOAD_URL}"
fi

ok "Downloaded ($(du -h "${TMPDIR}/${TARBALL}" | cut -f1 | xargs))"

# ── Extract ──────────────────────────────────────────────────────
info "Extracting..."
tar -xzf "${TMPDIR}/${TARBALL}" -C "${TMPDIR}"

if [ ! -f "${TMPDIR}/${BINARY_NAME}" ]; then
    # Might be in a subdirectory
    BINARY_PATH=$(find "${TMPDIR}" -name "${BINARY_NAME}" -type f | head -1)
    if [ -z "$BINARY_PATH" ]; then
        error "Binary '${BINARY_NAME}' not found in archive"
    fi
else
    BINARY_PATH="${TMPDIR}/${BINARY_NAME}"
fi

chmod +x "${BINARY_PATH}"
ok "Extracted"

# ── Install ──────────────────────────────────────────────────────
info "Installing to ${BOLD}${INSTALL_DIR}/${BINARY_NAME}${RESET}..."

if [ -w "${INSTALL_DIR}" ]; then
    mv "${BINARY_PATH}" "${INSTALL_DIR}/${BINARY_NAME}"
else
    warn "Need sudo to install to ${INSTALL_DIR}"
    sudo mv "${BINARY_PATH}" "${INSTALL_DIR}/${BINARY_NAME}"
fi

ok "Installed"

# ── Verify ───────────────────────────────────────────────────────
if command -v akasha &>/dev/null; then
    INSTALLED_VERSION=$(akasha --version 2>/dev/null || echo "unknown")
    ok "akasha is ready: ${BOLD}${INSTALLED_VERSION}${RESET}"
else
    warn "Binary installed but not found in PATH. Add ${INSTALL_DIR} to your PATH."
fi

# ── Next steps ───────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}Next steps:${RESET}"
echo ""
echo -e "    ${CYAN}# Start Akasha${RESET}"
echo -e "    akasha"
echo ""
echo -e "    ${CYAN}# Or use Docker${RESET}"
echo -e "    docker run -d -p 7777:7777 alejandrosl/akasha:latest"
echo ""
echo -e "    ${CYAN}# Install the Python SDK${RESET}"
echo -e "    pip install akasha-client"
echo ""
echo -e "  ${BOLD}Dashboard:${RESET}  https://localhost:7777"
echo -e "  ${BOLD}Docs:${RESET}       https://github.com/ocuil/akasha-public"
echo -e "  ${BOLD}Docker Hub:${RESET} https://hub.docker.com/r/alejandrosl/akasha"
echo ""
