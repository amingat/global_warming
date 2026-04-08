# Déploiement Streamlit Community Cloud

## Principe

- **CI** : GitHub Actions vérifie le code à chaque push / pull request.
- **CD** : un second workflow construit l'index Chroma puis pousse une branche `streamlit-cloud`.
- **Déploiement Streamlit Cloud** : l'application Streamlit est reliée à la branche `streamlit-cloud` et à l'entrypoint `streamlit_app.py`.

## Pourquoi une branche `streamlit-cloud` ?

L'application a besoin d'un index vectoriel déjà construit (`storage/chroma`). Streamlit Community Cloud redéploie le dépôt GitHub, mais ne consomme pas directement les artefacts GitHub Actions. Le workflow `deploy-streamlit-cloud.yml` écrit donc l'index dans le dépôt et pousse le résultat vers une branche dédiée.

## Secrets GitHub à créer

Dans **GitHub > Settings > Secrets and variables > Actions**, créez :

- `OPENAI_API_KEY`
- `TAVILY_API_KEY` (optionnel)

## Déploiement initial sur Streamlit Cloud

1. Poussez votre repo sur GitHub.
2. Lancez le workflow **Deploy Streamlit Cloud branch** ou poussez sur `main`.
3. Vérifiez que la branche `streamlit-cloud` a bien été créée.
4. Dans Streamlit Community Cloud, cliquez sur **Create app**.
5. Sélectionnez :
   - **Repository** : votre repo GitHub
   - **Branch** : `streamlit-cloud`
   - **Main file path** : `streamlit_app.py`
6. Dans **Advanced settings > Secrets**, collez le contenu de `.streamlit/secrets.toml.example` en remplaçant les valeurs.
7. Déployez.

## Secrets Streamlit Cloud

Exemple à coller dans **Advanced settings > Secrets** :

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
TAVILY_API_KEY = ""
DOCS_PATH = "data/pdfs"
CHROMA_DIR = "storage/chroma"
SQLITE_PATH = "storage/memory/chat_history.db"
TODO_PATH = "storage/memory/todo.json"
APP_RUNTIME_MODE = "direct"
TOP_K = 4
RAG_SCORE_THRESHOLD = 0.2
```

## Après le premier déploiement

- chaque push sur `main` déclenche la CI ;
- si la CI passe, le workflow CD peut régénérer l'index et mettre à jour la branche `streamlit-cloud` ;
- Streamlit Community Cloud redéploie automatiquement les changements de la branche liée.
