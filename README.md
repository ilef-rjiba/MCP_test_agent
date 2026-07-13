# 🤖 mcp-adk-agent

An AI agent built with **Google ADK** (Agent Development Kit), connected to **Vertex AI** and tools exposed by a private **MCP Gateway** on Cloud Run, with automatic authentication through **Application Default Credentials**.

---

## ⚡ Quick Start

```bash
# Clone
git clone https://github.com/ilef-rjiba/MCP_test_agent.git
cd mcp-adk-agent

# Setup + auth + launch in one command
make run
```

Then open [http://localhost:8000](http://localhost:8000), select **`my_agent`**, and start chatting.

---

## 🪟 Windows Setup

If the machine has nothing installed, follow this order:

1. Install these tools:
   - [Git for Windows](https://git-scm.com/download/win) 
   - [Python 3.11+](https://www.python.org/downloads/windows/)
   **(Crucial Step: During installation, the user must check the box that says "Add Python to PATH". Without this, the python command will fail in the terminal.)**
   - [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Restart PowerShell after installation if needed.
3. Clone the repository and open the project folder:

```powershell
git clone https://github.com/ilef-rjiba/MCP_test_agent.git
cd mcp-adk-agent
```

4. Create and activate the Python virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

5. Install the Python dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. Create the `.env` file from the template:

```powershell
Copy-Item .env.example .env
```

7. Make sure `.env` contains at least:

```ini
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=acn-researchplatform
GOOGLE_CLOUD_LOCATION=us-central1
MCP_API_KEY=...
```

8. Sign in to Google Cloud to create Application Default Credentials:

```powershell
gcloud auth application-default login
```

9. Start the agent:

```powershell
adk web .
```

10. Open [http://localhost:8000](http://localhost:8000), select **`my_agent`**, then begin chatting.

---

## 📋 Prerequisites

| Tool | Version | Installation |
|---|---|---|
| Python | >= 3.11 | [python.org](https://python.org) |
| gcloud CLI | latest | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) |
| make | — | preinstalled on macOS/Linux |

On Windows, `make` is not required. Use the PowerShell steps above instead.

You also need access to the GCP project `acn-researchplatform` with the **Vertex AI User** role (`roles/aiplatform.user`).

---

## 🛠️ Make Commands

```
make run     -> setup + auth check + web launch  (main command)
make setup   -> create the Python venv + install dependencies + copy .env
make auth    -> re-authenticate with Google Cloud if the token expired
make cli     -> interactive CLI mode (terminal)
make clean   -> remove .venv and Python caches
make help    -> show all commands
```

### What `make run` Does

```
1. Creates .venv and installs dependencies  (skipped if already done)
2. Copies .env.example -> .env              (skipped if already done)
3. Checks Google Cloud credentials
   -> if expired: opens the browser to re-authenticate (gcloud auth application-default login)
4. Starts adk web . -> http://localhost:8000
```

---

## 🔐 Authentication

No API key is required for Google Cloud access. The agent uses your Google Cloud **Application Default Credentials** (ADC).

```bash
# First time or when the token expired
make auth
# or directly:
gcloud auth application-default login
```

> **OIDC token for the MCP Gateway**: the Cloud Run server is private (`--no-allow-unauthenticated`). The agent automatically fetches an OIDC identity token from your ADC at startup. That token is valid for about **1 hour** — rerun `make run` if it expires.

---

## 🏗️ Architecture

```
mcp-adk-agent/
├── my_agent/
│   ├── __init__.py   # Exposes root_agent for ADK
│   ├── agent.py      # Agent definition: model, tools, instructions
│   └── tools.py      # Local Python tools (time, calculator)
├── .env              # Vertex AI config (project, region)
├── .env.example      # Template
├── Makefile          # Setup and launch commands
├── requirements.txt
└── README.md
```

### Agent Flow

```
User
    │
    ▼
ADK Web UI (localhost:8000)
    │
    ▼
root_agent (Gemini 2.5 Flash via Vertex AI)
    │
    ├── MCPToolset ──── OIDC token ──►  MCP Gateway (Cloud Run)
    │                                    └── dynamic tools
    │
    └── local tools (get_current_time, calculator)
```

---

## ⚙️ Configuration

The `.env` file (copied from `.env.example`) contains:

```ini
GOOGLE_GENAI_USE_VERTEXAI=TRUE        # Vertex AI backend (required)
GOOGLE_CLOUD_PROJECT=acn-researchplatform
GOOGLE_CLOUD_LOCATION=us-central1     # Region (editable)
```

---

## 🔧 Troubleshooting

| Error | Fix |
|---|---|
| `DefaultCredentialsError` | Run `make auth` again |
| `Expired token (401)` after 1 hour | Run `make run` again |
| `404 / model not found` | Check `GOOGLE_CLOUD_PROJECT` in `.env` |
| `Port 8000 already in use` | `kill $(lsof -ti:8000)` and retry |
