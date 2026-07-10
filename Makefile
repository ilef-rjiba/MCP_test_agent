# ==============================================================================
#  mcp-adk-agent — Makefile
#  Usage : make          → affiche l'aide
#          make setup    → crée le venv + installe les dépendances + copie .env
#          make auth     → authentification Google Cloud (ADC)
#          make run      → lance l'interface web ADK  (= setup + auth + adk web)
#          make cli      → lance l'interface CLI ADK
#          make clean    → supprime le venv et les caches
# ==============================================================================

VENV        := .venv
PYTHON      := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
ADK         := $(VENV)/bin/adk

.DEFAULT_GOAL := help

# ── Aide ──────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  mcp-adk-agent"
	@echo ""
	@echo "  Commandes disponibles :"
	@echo "    make setup   — crée le venv Python + installe les dépendances + copie .env"
	@echo "    make auth    — authentification Google Cloud (Application Default Credentials)"
	@echo "    make run     — lance l'interface web  → http://localhost:8000"
	@echo "    make cli     — lance l'interface CLI (terminal)"
	@echo "    make clean   — supprime .venv et les caches Python"
	@echo ""
	@echo "  Démarrage rapide :"
	@echo "    make run     (fait setup + auth + démarrage en une commande)"
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────────────────
.PHONY: setup
setup: $(VENV)/bin/activate .env
	@echo "✅ Setup terminé."

$(VENV)/bin/activate: requirements.txt
	@echo "📦 Création du venv Python et installation des dépendances..."
	python3 -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --upgrade -r requirements.txt
	@touch $(VENV)/bin/activate

.env:
	@echo "📋 Copie de .env.example → .env"
	cp .env.example .env
	@echo "   ⚠️  Vérifie les valeurs dans .env si nécessaire."

# ── Auth ──────────────────────────────────────────────────────────────────────
.PHONY: auth
auth:
	@echo "🔐 Authentification Google Cloud (Application Default Credentials)..."
	@echo "   → Un navigateur va s'ouvrir pour te connecter."
	gcloud auth application-default login
	@echo "✅ Authentification terminée."

# ── Run ───────────────────────────────────────────────────────────────────────
.PHONY: run
run: setup
	@echo ""
	@echo "🔐 Vérification des credentials Google Cloud..."
	@$(PYTHON) -c "import google.auth, google.auth.transport.requests; \
		creds, p = google.auth.default(scopes=['openid','https://www.googleapis.com/auth/cloud-platform']); \
		creds.refresh(google.auth.transport.requests.Request()); \
		print('✅ Credentials valides pour le projet :', p)" 2>/dev/null || \
	( echo ""; \
	  echo "❌ Credentials expirés ou absents. Lancement de l'authentification..."; \
	  echo ""; \
	  $(MAKE) auth )
	@echo ""
	@echo "🚀 Démarrage de l'agent ADK → http://localhost:8000"
	@echo "   Sélectionne 'my_agent' dans l'interface web, puis discute !"
	@echo ""
	$(ADK) web --log_level DEBUG .

# ── CLI ───────────────────────────────────────────────────────────────────────
.PHONY: cli
cli: setup
	@echo "🚀 Démarrage en mode CLI..."
	$(ADK) run my_agent

# ── Clean ─────────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	@echo "🧹 Suppression du venv et des caches..."
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Nettoyage terminé."
