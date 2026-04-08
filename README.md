# Climate RAG Agent

Assistant intelligent spécialisé sur les questions **météo** et **climatiques**, combinant :

- un pipeline **RAG** sur des PDF climatiques du GIEC ;
- un **agent d’outils** pour la météo, le calcul, la recherche web et une todo locale ;
- une **API FastAPI** ;
- une **interface Streamlit** ;
- une **mémoire conversationnelle persistée en SQLite** avec **reprise d’anciennes sessions** ;
- un mode **Streamlit Cloud standalone** qui n'a pas besoin du backend FastAPI pour fonctionner.

## Architecture

```text
Utilisateur
    |
    v
Streamlit UI
    |
    +--> mode direct (Streamlit Cloud) -> ClimateAssistantService
    |
    +--> mode API (local / autre cloud) -> FastAPI /chat + /sessions + /memory/clear
                                              |
                                              v
                                      ClimateAssistantService
                                              |
                +-----------------------------+----------------------------+
                |                                                          |
                v                                                          v
           Router LLM                                                Mémoire SQLite
                |                                                          |
        +-------+--------+                                                 v
        |                |                                           Historique persistant
        v                v                                           + reprise de session
       RAG          Agent d'outils
        |                |
        |        +-------+-----------------------------+
        |        |       |             |              |
        v        v       v             v              v
     Chroma   Météo   Calculatrice  Web search     Todo locale
```

## Variables d’environnement

Copiez `.env.example` en `.env` puis renseignez au minimum :

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
APP_RUNTIME_MODE=auto
```

Pour Streamlit Cloud, utilisez plutôt `.streamlit/secrets.toml.example` comme modèle et définissez `APP_RUNTIME_MODE = "direct"`.

## Lancement local

### 1) Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2) Créer `.env`

```bash
cp .env.example .env
```

### 3) Construire l’index RAG

```bash
python -m scripts.ingest --reset
```

### 4) Lancer l’API

```bash
python -m uvicorn api.main:app --reload
```

### 5) Lancer Streamlit

```bash
python -m streamlit run streamlit_app.py
```

## Déploiement Streamlit Community Cloud

Le repo inclut :

- `.github/workflows/ci.yml` : lint + smoke tests Streamlit
- `.github/workflows/deploy-streamlit-cloud.yml` : construit l'index Chroma et pousse une branche `streamlit-cloud`

La procédure complète est décrite dans [`docs/streamlit_cloud_deployment.md`](docs/streamlit_cloud_deployment.md).

## Fichiers clés

```text
api/main.py
app/config.py
app/services/assistant.py
app/memory/store.py
app/rag/indexer.py
app/rag/retriever.py
ui/streamlit_app.py
streamlit_app.py
.github/workflows/ci.yml
.github/workflows/deploy-streamlit-cloud.yml
.streamlit/config.toml
.streamlit/secrets.toml.example
```
