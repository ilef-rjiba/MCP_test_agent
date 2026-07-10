# 🤖 mcp-adk-agent

Agent IA basé sur **Google ADK** (Agent Development Kit), connecté à **Vertex AI** et aux outils exposés par un **MCP Gateway** (Cloud Run privé), avec authentification automatique via **Application Default Credentials**.

---

## ⚡ Démarrage rapide

```bash
# Clone
git clone https://github.com/julienleber/mcp-adk-agent.git
cd mcp-adk-agent

# Setup + auth + démarrage en une commande
make run
```

Ouvre ensuite [http://localhost:8000](http://localhost:8000), sélectionne **`my_agent`** et discute !

---

## 📋 Prérequis

| Outil | Version | Installation |
|---|---|---|
| Python | ≥ 3.11 | [python.org](https://python.org) |
| gcloud CLI | dernière | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) |
| make | — | pré-installé sur macOS/Linux |

Accès requis sur le projet GCP `acn-researchplatform` : rôle **Vertex AI User** (`roles/aiplatform.user`).

---

## 🛠️ Commandes Make

```
make run     → setup + vérif auth + démarrage web  (commande principale)
make setup   → crée le venv Python + installe les dépendances + copie .env
make auth    → ré-authentification Google Cloud si token expiré
make cli     → interface CLI interactive (terminal)
make clean   → supprime .venv et les caches
make help    → affiche toutes les commandes
```

### Détail du flux `make run`

```
1. Crée .venv et installe les dépendances  (ignoré si déjà fait)
2. Copie .env.example → .env               (ignoré si déjà fait)
3. Vérifie les credentials Google Cloud
   → si expirés : ouvre le navigateur pour ré-authentifier (gcloud auth application-default login)
4. Lance adk web . → http://localhost:8000
```

---

## 🔐 Authentification

Aucune clé API. L'agent utilise les **Application Default Credentials** (ADC) de ton compte Google Cloud.

```bash
# Première fois ou si token expiré
make auth
# ou directement :
gcloud auth application-default login
```

> **Token OIDC pour le MCP Gateway** : le serveur Cloud Run est privé (`--no-allow-unauthenticated`). L'agent récupère automatiquement un identity token OIDC depuis tes ADC au démarrage. Ce token est valable **~1 heure** — relance `make run` s'il expire.

---

## 🏗️ Architecture

```
mcp-adk-agent/
├── my_agent/
│   ├── __init__.py   # Expose root_agent pour ADK
│   ├── agent.py      # Définition de l'agent : modèle, outils, instructions
│   └── tools.py      # Outils Python locaux (heure, calculatrice)
├── .env              # Config Vertex AI (projet, région)
├── .env.example      # Template
├── Makefile          # Commandes de setup et démarrage
├── requirements.txt
└── README.md
```

### Flux de l'agent

```
Utilisateur
    │
    ▼
ADK Web UI (localhost:8000)
    │
    ▼
root_agent (Gemini 2.5 Flash via Vertex AI)
    │
    ├── MCPToolset ──── OIDC token ──►  MCP Gateway (Cloud Run)
    │                                    └── outils dynamiques
    │
    └── outils locaux (get_current_time, calculator)
```

---

## ⚙️ Configuration

Le fichier `.env` (copié depuis `.env.example`) contient :

```ini
GOOGLE_GENAI_USE_VERTEXAI=TRUE        # Backend Vertex AI (obligatoire)
GOOGLE_CLOUD_PROJECT=acn-researchplatform
GOOGLE_CLOUD_LOCATION=us-central1     # Région (modifiable)
```

---

## 🔧 Dépannage

| Erreur | Solution |
|---|---|
| `DefaultCredentialsError` | Relancer `make auth` |
| `Token expiré (401)` après 1h | Relancer `make run` |
| `404 / model not found` | Vérifier `GOOGLE_CLOUD_PROJECT` dans `.env` |
| `Port 8000 déjà utilisé` | `kill $(lsof -ti:8000)` puis relancer |
