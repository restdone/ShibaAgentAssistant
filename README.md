<img width="500" height="500" alt="shibachess" src="https://github.com/user-attachments/assets/e2ef3fba-f8cb-4078-8c13-5a52d00382e9" />

# Shiba — Personal AI Assistant


Shiba is a locally-running personal AI assistant for Linux. It runs in your terminal, has long-term memory via an Obsidian vault, short-term semantic memory via ChromaDB, and supports both text and voice interaction. An Android companion app lets you approve or reject file writes and shell commands from your phone over local WiFi.

---

## All Started with One Prompt

I asked Claude Code following:

`
Make an agent named Shiba, it has read, write and executeion permission on this machine. I want it to use obsidian as it's long term memory vault to remember what we talked. Shiba also prioritise to understand my intention based on our chats understand what I need. Use a local vector store for indexing our talks and topic, when did we discussed about it to maintain its short term memory and our context. Give it the ability to do necessary coding for fulfill my request after my approval. I want to talk with it in a termional only now.
`

Later on, I used only the Shiba to build itself up, now you can talk with it using English without any button pressed, ask it to use Firefox, put things on a file server. Also, there is a mobile app for approving the actions, acces to file server and read the memories. I found it interesting and fun when I kept talking with it using bluetooth headset in home, so I want to share it.

Keep talking with it and ask it to make its own tool to do your task! The voice function (input and output) is powered by a small local LLM that recongize voice.

---

## What Shiba can do

- Hold natural conversations with memory that persists across sessions
- Read, write, and search files on your machine
- Execute shell commands (with your approval)
- Remember your preferences, projects, and notes in an Obsidian vault
- Speak and listen using fully local voice processing (no audio sent anywhere)
- Send approval requests to your Android phone before taking any action
- Automatically digest each day's conversations into a diary entry at midnight
- Control Firefox via a browser extension — navigate pages, click, type, read content, and take screenshots
- Ask it to improve itself!
---

## NOTE!!

- This agent has a file server and a server for serving request approval. Please note that the traffic used are NOT encrtpyed (HTTP). If you want to secure the traffic, ask Shiba to review the code and then change the its own code with certificate.
- By default there is no obsidian, you need to install it using HomeBrew, but it can still use the file-based search to search long term memory.
- This one is intended for lab use/home use. Use at your own risk.

---

## Requirements

- Ubuntu 22.04 / 24.04 (or similar Debian-based Linux)
- Python 3.10 or higher
- An [Anthropic API key](https://console.anthropic.com/) — this is the only external service required
- Firefox with the Shiba browser extension loaded
- [Obsidian](https://obsidian.md/) — optional, for browsing your vault as notes
- [obsidian-cli](https://github.com/Yakitrak/obsidian-cli) — optional, used by the vault tools

---
## TL;DR

```bash
cd shiba
chmod +x setup.sh
python3 -m venv venv
source venv/bin/activate
./setup.sh

Install the shiba apk. You can find it in the workplace folder.
You can install it by downloading the apk to the android, and then install it. 
And..talk to it
```

### System dependencies for voice mode

```bash
sudo apt install portaudio19-dev ffmpeg
```


## Quick start

### 1. Run the setup script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all Python dependencies
- Create your `.env` file from the template
- Create the Obsidian vault folder structure at `~/Documents/Shiba-Vault`
- Initialise the ChromaDB short-term memory store at `~/.shiba/chroma`

### 2. Add your Anthropic API key

Open `.env` and fill in your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

You can get a key from [console.anthropic.com](https://console.anthropic.com/).

### 3. Start the browser extension WebSocket server

```bash
source venv/bin/activate
python browser_extension/ws_server.py &
```

### 4. Load the Firefox extension

1. Open Firefox and go to `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Select `browser_extension/manifest.json`

### 5. Start Shiba

```bash
source venv/bin/activate
python shiba.py
```

---

## Manual installation (step by step)

### 1. Clone or unpack the project

```bash
cd shiba
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

```bash
cp .env.example .env
```

Open `.env` and add your Anthropic key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 5. Configure paths (optional)

Open `config.py` and adjust if needed:

- `VAULT_PATH` — path to your Obsidian vault (default: `~/Documents/Shiba-Vault`)
- `CHROMA_PATH` — where ChromaDB stores data (default: `~/.shiba/chroma`)
- `OBSIDIAN_CLI` — path to the `obsidian-cli` binary if installed
- `MODEL` — the Claude model to use (default: `claude-sonnet-4-6`)

---

## Usage

Activate the virtual environment first, then run:

### Text mode

```bash
python shiba.py
```

### Voice mode — push to talk (press Enter to speak)

```bash
python shiba.py --voice
```

### Voice mode — automatic voice activity detection (just speak naturally)

```bash
python shiba.py --vad
```

---

## In-session commands

| Command | What it does |
|---|---|
| `exit` / `quit` / `bye` | Save session and exit |
| `clear` | Clear the current conversation history |
| "start a new conversation" | Save session and start fresh |
| Ctrl+C | Save session and exit |

---

## Approval server

Before writing any file or running any shell command, Shiba posts the request to a local Flask server on port `7845`. You must approve or reject it before Shiba proceeds. You can do this in the terminal, or using the Android app (see below).

The approval server starts automatically when you run Shiba.

---

## Android companion app — Shiba Approver

The `shiba-approver/` folder contains an Android app that receives approval requests from Shiba over your local WiFi.

### How it works

1. Shiba posts a request (file write or shell command) to the approval server on port `7845`.
2. The app polls the server every 2 seconds.
3. When a request arrives, a high-priority notification fires on your phone.
4. Tap the notification to see the full details — Approve or Reject.
5. The decision is sent back, and Shiba proceeds or cancels.

### Building the APK

You need Android command line tools or Android Studio.

#### Option A — Android Studio

1. Open the `shiba-approver/` folder as a project in Android Studio.
2. Let Gradle sync.
3. Build → Build Bundle(s) / APK(s) → Build APK(s).
4. APK lands at `shiba-approver/app/build/outputs/apk/debug/app-debug.apk`.

#### Option B — Command line

Install Android SDK tools:

```bash
# Ubuntu/Debian
sudo apt install android-sdk

# or download from https://developer.android.com/studio#command-line-tools-only
```

Accept licences and install required components:

```bash
sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```

Build the APK:

```bash
cd shiba-approver
./gradlew assembleDebug
```

Install to a connected phone:

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

### First-time setup on the phone

1. Open the Shiba Approver app.
2. Enter your machine's local IP — find it with `ip addr` or `hostname -I` on the machine.
3. Port is `7845` by default.
4. Tap **Test Connection** — should say "Connected".
5. Tap **Start Polling**.

The app will restart polling automatically on phone reboot.

---

## Memory system

Shiba uses two memory layers:

**Short-term — ChromaDB** (`~/.shiba/chroma`): Every conversation turn is indexed and searchable semantically. Used to recall relevant past exchanges within and across sessions.

**Long-term — Obsidian Vault** (`~/Documents/Shiba-Vault`): Markdown notes organised into Daily Notes, Topics, and Projects. Shiba reads and writes these during conversation. You can browse and edit them in the Obsidian desktop app at any time.

The vault is personal. Do not share it. If deploying Shiba on a new machine, a fresh empty vault is created automatically by `setup.sh`.

### Nightly digest

Every night at 23:59, `digest.py` runs automatically via a cron job. It pulls all of that day's conversation turns from ChromaDB, sends them to Claude to write a coherent diary entry in plain prose, saves the diary into the vault under `Daily Notes/`, and then deletes those entries from ChromaDB. This keeps short-term memory lean while preserving a permanent human-readable record of every day in the vault.

Digest logs are written to `~/.shiba/digest.log`.

To set up the cron job manually if it isn't already installed:

```bash
crontab -e
```

Add this line (adjust the path to match your installation):

```
59 23 * * * /home/shiba/Shiba/venv/bin/python /home/shiba/Shiba/digest.py >> ~/.shiba/digest.log 2>&1
```

---

## File server

`file_server.py` runs a lightweight local HTTP server that exposes files on your machine to the Android companion app and other local clients. It starts automatically alongside the approval server when you run Shiba. The file server is used internally — you do not need to interact with it directly.

---

## Browser control

Shiba controls Firefox through a local WebSocket bridge and a lightweight browser extension. There is no Playwright or headless browser dependency — Shiba works directly inside the Firefox instance you already have open on your screen.

### How it works

`browser_extension/ws_server.py` runs a local WebSocket server. The Firefox extension connects to it and relays commands (navigate, click, type, read text, screenshot, etc.) back and forth. Shiba sends a tool call, the extension executes it in the active tab, and the result is returned.

### Starting the WebSocket server

```bash
source venv/bin/activate
python browser_extension/ws_server.py &
```

To have it start automatically, add that line to your `~/.bashrc`.

### Loading the Firefox extension

1. Open Firefox and go to `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Select `browser_extension/manifest.json`

The extension will need to be reloaded each time Firefox restarts (unless you install it permanently as a signed extension).

### Browser tools available to Shiba

| Tool | What it does |
|---|---|
| `browser_navigate` | Go to a URL |
| `browser_search_google` | Search Google and return results |
| `browser_search_youtube` | Search YouTube and return results |
| `browser_get_text` | Read the visible text content of the current page |
| `browser_click` | Click an element by CSS selector |
| `browser_type` | Type text into an element |
| `browser_press` | Press a keyboard key (e.g. Enter, Tab) |
| `browser_screenshot` | Take a screenshot of the current page |
| `browser_scroll` | Scroll the page by a number of pixels |
| `browser_wait` | Wait a number of seconds |
| `browser_current_url` | Get the current page URL and title |
| `browser_evaluate` | Run arbitrary JavaScript in the current tab |
| `browser_open_tab` | Open a new tab |
| `browser_close` | Close the browser session |

---

## Project structure

```
shiba/
├── shiba.py                  # Entry point
├── config.py                 # Paths, model, and settings
├── approval_server.py        # Flask server for approvals
├── digest.py                 # Nightly memory digest — writes diary to vault, clears ChromaDB
├── file_server.py            # Local HTTP file server for the Android companion app
├── requirements.txt          # Python dependencies
├── .env.example              # Template for your API key
├── setup.sh                  # First-time setup script
├── agent/
│   ├── core.py               # Main agent loop and session management
│   ├── tools.py              # Tool definitions and tool execution
│   └── browser.py            # Placeholder (browser handled via Firefox extension)
├── memory/
│   ├── vector.py             # ChromaDB short-term memory
│   └── vault.py              # Obsidian vault read/write
├── voice/
│   ├── tts.py                # Text-to-speech (edge-tts, local)
│   ├── stt.py                # Speech-to-text (faster-whisper, local)
│   ├── push_to_talk.py       # Push-to-talk input mode
│   └── voice_activity.py     # VAD input mode
├── browser_extension/
│   ├── manifest.json         # Firefox extension manifest
│   ├── background.js         # Extension background script
│   ├── content.js            # Content script injected into pages
│   └── ws_server.py          # Local WebSocket bridge server
└── shiba-approver/           # Android companion app (source)
```

---

## Notes

- Voice transcription runs fully locally using `faster-whisper` — no audio leaves your machine.
- TTS uses `edge-tts` (Microsoft Edge neural voices) — free, no API key needed.
- The only external API call is to Anthropic for the language model.
- The `.env` file is never packaged or committed — keep it private.
