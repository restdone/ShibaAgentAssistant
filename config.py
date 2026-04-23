import os
import shutil
from pathlib import Path

# Load .env from project root (secrets file — never commit this)
_ENV_PATH = Path(__file__).parent / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                os.environ.setdefault(_key.strip(), _val.strip())

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
MODEL = 'claude-sonnet-4-6'

SHIBA_HOME = Path.home() / '.shiba'
VAULT_PATH = Path.home() / 'Documents' / 'Shiba-Vault'
CHROMA_PATH = SHIBA_HOME / 'chroma'

# obsidian-cli: search common install locations automatically
def _find_obsidian_cli() -> str:
    candidates = [
        shutil.which("obsidian-cli"),                                    # on PATH
        "/home/linuxbrew/.linuxbrew/bin/obsidian-cli",                   # Homebrew (Linux)
        "/opt/homebrew/bin/obsidian-cli",                                # Homebrew (macOS)
        str(Path.home() / ".linuxbrew" / "bin" / "obsidian-cli"),       # user Homebrew
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return c
    return "obsidian-cli"  # fallback: assume it's on PATH

OBSIDIAN_CLI = _find_obsidian_cli()

SHIBA_HOME.mkdir(parents=True, exist_ok=True)

MAX_TOKENS = 8096
MEMORY_SEARCH_RESULTS = 5
RECENT_HISTORY_TURNS = 20

# Voice settings (edge-tts — no API key needed)
TTS_VOICE = "en-US-AriaNeural"
