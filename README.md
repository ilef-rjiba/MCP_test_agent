# 🤖 mcp-test-agent

An AI agent built with **Google ADK** (Agent Development Kit), connected to **Vertex AI** and tools exposed by a private **MCP Gateway** on Cloud Run, with automatic authentication through **Application Default Credentials**.

---

## ⚡ Quick Start (for Linux environments)

```bash
# Clone
git clone https://github.com/ilef-rjiba/MCP_test_agent.git
cd .\MCP_test_agent

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
cd .\MCP_test_agent
```

4. Create and activate the Python virtual environment:

```powershell
python -m venv .venv
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

**(Crucial Step: Make sure to update the .env MCP_API_KEY with its correct value)**

8. Sign in to Google Cloud to create Application Default Credentials:

```powershell
gcloud auth login
```
**(Crucial Step: Make sure you are signed in to the acn-researchplatform project)**

if you are connected to a different project, sign up using this command :  
```
gcloud config set project acn-researchplatform
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