#!/usr/bin/env bash
set -e

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

TOOL_NAME="leviathan"
INSTALL_DIR="/opt/$TOOL_NAME"
BIN_LINK="/usr/local/bin/$TOOL_NAME"

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { echo -e "${CYAN}[*]${RESET} $1"; }
success() { echo -e "${GREEN}[+]${RESET} $1"; }
warning() { echo -e "${YELLOW}[!]${RESET} $1"; }
error()   { echo -e "${RED}[✗]${RESET} $1"; exit 1; }

# ── Root check ────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    error "Run as root: sudo bash setup.sh"
fi

echo -e "${CYAN}"
cat << 'EOF'
 ██▓    ▓█████ ██▒   █▓ ██▓ ▄▄▄     ▄▄▄█████▓ ██░ ██  ▄▄▄       ███▄    █ 
▓██▒    ▓█   ▀▓██░   █▒▓██▒▒████▄   ▓  ██▒ ▓▒▓██░ ██▒▒████▄     ██ ▀█   █ 
▒██░    ▒███   ▓██  █▒░▒██▒▒██  ▀█▄ ▒ ▓██░ ▒░▒██▀▀██░▒██  ▀█▄  ▓██  ▀█ ██▒
▒██░    ▒▓█  ▄  ▒██ █░░░██░░██▄▄▄▄██░ ▓██▓ ░ ░▓█ ░██ ░██▄▄▄▄██ ▓██▒  ▐▌██▒
░██████▒░▒████▒  ▒▀█░  ░██░ ▓█   ▓██▒ ▒██▒ ░ ░▓█▒░██▓ ▓█   ▓██▒▒██░   ▓██░
░ ▒░▓  ░░░ ▒░ ░  ░ ▐░  ░▓   ▒▒   ▓▒█░ ▒ ░░    ▒ ░░▒░▒ ▒▒   ▓▒█░░ ▒░   ▒ ▒ 
░ ░ ▒  ░ ░ ░  ░  ░ ░░   ▒ ░  ▒   ▒▒ ░   ░     ▒ ░▒░ ░  ▒   ▒▒ ░░ ░░   ░ ▒░
  ░ ░      ░       ░░   ▒ ░  ░   ▒    ░       ░  ░░ ░  ░   ▒      ░   ░ ░ 
    ░  ░   ░  ░     ░   ░        ░  ░         ░  ░  ░      ░  ░         ░ 
                   ░                                                      
EOF
echo -e "${RESET}"

# ── Python check ──────────────────────────────────────────────────────────────
info "Checking Python version..."
if ! command -v python3 &>/dev/null; then
    error "Python3 not found. Install it first: sudo apt install python3"
fi

PY_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [[ $PY_VERSION -lt 10 ]]; then
    error "Python 3.10+ required (union types). Found 3.$PY_VERSION"
fi
success "Python 3.$PY_VERSION found"

# ── Copy project to /opt ──────────────────────────────────────────────────────
info "Installing to $INSTALL_DIR..."
if [[ -d "$INSTALL_DIR" ]]; then
    warning "Existing install found at $INSTALL_DIR — overwriting"
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR"
success "Project copied to $INSTALL_DIR"

# ── Virtual environment ───────────────────────────────────────────────────────
info "Creating virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"
success "Virtual environment created"

info "Installing dependencies..."
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"
success "Dependencies installed"

# ── Wrapper script ────────────────────────────────────────────────────────────
info "Creating $BIN_LINK wrapper..."

cat > "$BIN_LINK" << EOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/core.py" "\$@"
EOF

chmod +x "$BIN_LINK"
success "Wrapper created at $BIN_LINK"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
success "Leviathan installed successfully!"
echo -e "    Usage: ${CYAN}$TOOL_NAME -s example.com --crtsh-only${RESET}"
echo -e "           ${CYAN}$TOOL_NAME -s example.com -w wordlist.txt --crtsh${RESET}"
echo -e "           ${CYAN}$TOOL_NAME -d https://example.com -w wordlist.txt${RESET}"
echo ""