#!/usr/bin/env bash
# =============================================================================
#  Shiba — First-time setup script
#  Run from the project root:  bash setup.sh
# =============================================================================
set -e

BOLD="\033[1m"
CYAN="\033[1;36m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

info()    { echo -e "${CYAN}[shiba]${RESET} $*"; }
success() { echo -e "${GREEN}[shiba]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[shiba]${RESET} $*"; }
error()   { echo -e "${RED}[shiba]${RESET} $*"; exit 1; }

echo ""
echo -e "${BOLD}${CYAN}====================================================${RESET}"
echo -e "${BOLD}${CYAN}        Shiba — Personal AI Assistant Setup         ${RESET}"
echo -e "${BOLD}${CYAN}====================================================${RESET}"
echo ""

# ── 0. Prerequisites check ────────────────────────────────────────────────────
info "Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    error "Python 3 is required but not found. Install it with: sudo apt install python3"
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    error "Python 3.10+ is required. You have Python ${PYTHON_VERSION}."
fi

success "Python ${PYTHON_VERSION} found."

# ── 1. System dependencies ────────────────────────────────────────────────────
echo ""
info "[1/6] Installing system dependencies..."

if command -v apt &>/dev/null; then
    info "  Using apt..."
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends \
        portaudio19-dev \
        ffmpeg \
        python3-dev \
        python3-venv \
        build-essential \
        curl \
        git \
        2>/dev/null || warn "  Some apt packages failed — continuing anyway."
    success "  System packages installed."
else
    warn "  apt not found — skipping system package installation."
    warn "  For voice mode, manually install: portaudio19-dev, ffmpeg"
fi

# ── 2. Python virtual environment ─────────────────────────────────────────────
echo ""
info "[2/6] Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "  Virtual environment created."
else
    success "  Virtual environment already exists, skipping."
fi

# Activate
source venv/bin/activate
success "  Activated: $(which python)"

# ── 3. Python dependencies ────────────────────────────────────────────────────
echo ""
info "[3/6] Installing Python dependencies from requirements.txt..."

pip install --upgrade pip setuptools wheel --quiet
pip install -r requirements.txt --quiet

success "  Python packages installed."

# ── 4. .env file ──────────────────────────────────────────────────────────────
echo ""
info "[4/6] Setting up environment file..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    warn "  Created .env from template."
    warn "  ACTION REQUIRED: Open .env and add your Anthropic API key:"
    warn "    ANTHROPIC_API_KEY=sk-ant-..."
    warn "  Get a key at: https://console.anthropic.com/"
else
    success "  .env already exists, skipping."
fi

# ── 5. Obsidian vault ─────────────────────────────────────────────────────────
echo ""
info "[5/6] Setting up Obsidian vault..."

VAULT_DIR="$HOME/Documents/Shiba-Vault"
mkdir -p "$VAULT_DIR/Daily Notes"
mkdir -p "$VAULT_DIR/Topics"
mkdir -p "$VAULT_DIR/Projects"
mkdir -p "$VAULT_DIR/.obsidian"

if [ ! -f "$VAULT_DIR/.obsidian/app.json" ]; then
    echo '{}' > "$VAULT_DIR/.obsidian/app.json"
fi

success "  Vault structure ready at $VAULT_DIR"

# Optional: install obsidian-cli (used for full-text vault search)
if ! command -v obsidian-cli &>/dev/null; then
    if command -v brew &>/dev/null; then
        info "  Installing obsidian-cli via Homebrew..."
        brew install yakitrak/yakitrak/obsidian-cli 2>/dev/null && \
            success "  obsidian-cli installed." || \
            warn "  obsidian-cli install failed — vault search will use fallback."
    else
        warn "  obsidian-cli not found and Homebrew is not installed."
        warn "  Vault search will use file-based fallback (search_vault still works)."
        warn "  To install Homebrew: https://brew.sh"
    fi
else
    success "  obsidian-cli already installed: $(which obsidian-cli)"
    obsidian-cli set-default "Shiba-Vault" "$VAULT_DIR" 2>/dev/null || true
fi

# ── 6. ChromaDB memory store ──────────────────────────────────────────────────
echo ""
info "[6/6] Initialising ChromaDB short-term memory store..."

CHROMA_DIR="$HOME/.shiba/chroma"
mkdir -p "$CHROMA_DIR"

python - <<'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import chromadb
chroma_path = Path.home() / ".shiba" / "chroma"
client = chromadb.PersistentClient(path=str(chroma_path))

col = client.get_or_create_collection(
    name="conversations",
    metadata={"hnsw:space": "cosine"},
)
print(f"      Collection 'conversations' ready ({col.count()} entries).")
PYEOF

success "  ChromaDB ready at $CHROMA_DIR"

# ── Browser extension WebSocket server (autostart hint) ───────────────────────
echo ""
info "Browser Extension WebSocket Server"
echo "  Shiba controls Firefox via a local WebSocket server (ws_server.py)."
echo "  You need to start it before running Shiba:"
echo ""
echo -e "    ${CYAN}source venv/bin/activate${RESET}"
echo -e "    ${CYAN}python browser_extension/ws_server.py &${RESET}"
echo ""
echo "  Then install the browser extension in Firefox:"
echo "    1. Open Firefox → about:debugging → This Firefox"
echo "    2. Click 'Load Temporary Add-on'"
echo "    3. Select: browser_extension/manifest.json"
echo ""
echo "  Optional: Add ws_server.py to your ~/.bashrc to autostart it."

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}====================================================${RESET}"
echo -e "${BOLD}${GREEN}                 Setup complete!                    ${RESET}"
echo -e "${BOLD}${GREEN}====================================================${RESET}"
echo ""
echo -e "${BOLD}How to start Shiba:${RESET}"
echo ""
echo -e "  ${CYAN}source venv/bin/activate${RESET}"
echo -e "  ${CYAN}python shiba.py${RESET}              # text mode"
echo -e "  ${CYAN}python shiba.py --voice${RESET}      # push-to-talk voice mode"
echo -e "  ${CYAN}python shiba.py --vad${RESET}        # always-listening voice mode"
echo -e "  ${CYAN}python shiba.py --mobile${RESET}     # enable Android approval app"
echo ""
echo -e "${BOLD}Next steps:${RESET}"
echo "  1. Open .env and add your Anthropic API key (if not done)"
echo "  2. Start the browser extension WebSocket server"
echo "  3. Load the Firefox extension from browser_extension/"
echo "  4. Run: python shiba.py"
echo ""
