import sys
import uuid
from pathlib import Path

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import get_settings
from app.services.assistant import ClimateAssistantService


settings = get_settings()


def detect_runtime_mode(api_url: str, configured_mode: str) -> str:
    mode = (configured_mode or 'auto').strip().lower()
    if mode in {'api', 'direct'}:
        return mode

    try:
        response = requests.get(f'{api_url}/health', timeout=3)
        response.raise_for_status()
        return 'api'
    except Exception:
        return 'direct'


@st.cache_resource
def get_direct_service() -> ClimateAssistantService:
    return ClimateAssistantService()


def fetch_sessions(api_url: str, runtime_mode: str) -> list[dict]:
    try:
        if runtime_mode == 'api':
            response = requests.get(f'{api_url}/sessions', timeout=30)
            response.raise_for_status()
            payload = response.json()
            return payload.get('sessions', [])

        return get_direct_service().list_sessions().model_dump().get('sessions', [])
    except Exception as exc:
        st.warning(f'Impossible de récupérer les anciennes sessions: {exc}')
        return []


def load_session_messages(api_url: str, session_id: str, runtime_mode: str) -> list[dict]:
    if runtime_mode == 'api':
        response = requests.get(f'{api_url}/sessions/{session_id}/messages', timeout=30)
        response.raise_for_status()
        payload = response.json()
        return payload.get('messages', [])

    return get_direct_service().get_session_messages(session_id).model_dump().get('messages', [])


def clear_session_memory(api_url: str, session_id: str, runtime_mode: str) -> None:
    if runtime_mode == 'api':
        response = requests.post(
            f'{api_url}/memory/clear',
            json={'session_id': session_id},
            timeout=30,
        )
        response.raise_for_status()
        return

    get_direct_service().clear_memory(session_id)


def send_chat_message(api_url: str, session_id: str, message: str, runtime_mode: str) -> dict:
    if runtime_mode == 'api':
        response = requests.post(
            f'{api_url}/chat',
            json={'session_id': session_id, 'message': message},
            timeout=90,
        )
        response.raise_for_status()
        return response.json()

    return get_direct_service().chat(session_id=session_id, message=message).model_dump()


def build_session_label(session: dict) -> str:
    preview = session.get('first_message_preview') or 'Session sans aperçu'
    updated_at = session.get('updated_at', '')
    count = session.get('message_count', 0)
    return f"{session['session_id']} — {preview} ({count} messages, maj: {updated_at})"


st.set_page_config(page_title='Climate RAG Agent', page_icon='🌦️', layout='wide')
st.title('🌦️ Climate RAG Agent')
st.caption('Assistant météo / climat avec RAG, outils, mémoire persistante et reprise de session.')

if 'session_id' not in st.session_state:
    st.session_state.session_id = f"streamlit-{uuid.uuid4().hex[:8]}"
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'loaded_session_id' not in st.session_state:
    st.session_state.loaded_session_id = st.session_state.session_id

with st.sidebar:
    st.subheader('Configuration')
    api_url = st.text_input('URL API', value=settings.api_base_url)
    runtime_mode = detect_runtime_mode(api_url, settings.app_runtime_mode)
    st.caption(f'Mode courant : {runtime_mode}')

    if runtime_mode == 'direct':
        st.info("Mode Streamlit Cloud / standalone : l'interface appelle directement le service Python sans backend FastAPI séparé.")

    if st.button('Rafraîchir la liste des sessions'):
        st.session_state.available_sessions = fetch_sessions(api_url, runtime_mode)

    available_sessions = st.session_state.get('available_sessions')
    if available_sessions is None:
        available_sessions = fetch_sessions(api_url, runtime_mode)
        st.session_state.available_sessions = available_sessions

    st.markdown('### Session active')
    st.code(st.session_state.session_id)

    manual_session_id = st.text_input('Reprendre une session par ID', value='')
    if st.button('Charger cette session par ID', use_container_width=True):
        target_session = manual_session_id.strip()
        if not target_session:
            st.warning('Veuillez saisir un session_id existant.')
        else:
            try:
                st.session_state.messages = load_session_messages(api_url, target_session, runtime_mode)
                st.session_state.session_id = target_session
                st.session_state.loaded_session_id = target_session
                st.success(f'Session rechargée: {target_session}')
            except Exception as exc:
                st.error(f'Impossible de charger la session: {exc}')

    if available_sessions:
        labels = {build_session_label(session): session['session_id'] for session in available_sessions}
        selected_label = st.selectbox('Anciennes sessions détectées', [''] + list(labels.keys()))
        if st.button('Reprendre la session sélectionnée', use_container_width=True):
            if not selected_label:
                st.warning('Choisissez une session dans la liste.')
            else:
                selected_session_id = labels[selected_label]
                try:
                    st.session_state.messages = load_session_messages(api_url, selected_session_id, runtime_mode)
                    st.session_state.session_id = selected_session_id
                    st.session_state.loaded_session_id = selected_session_id
                    st.success(f'Session rechargée: {selected_session_id}')
                except Exception as exc:
                    st.error(f'Impossible de recharger la session: {exc}')

    if st.button('Créer une nouvelle session', use_container_width=True):
        st.session_state.session_id = f"streamlit-{uuid.uuid4().hex[:8]}"
        st.session_state.loaded_session_id = st.session_state.session_id
        st.session_state.messages = []
        st.success(f'Nouvelle session créée: {st.session_state.session_id}')

    if st.button('Effacer la mémoire de la session active', use_container_width=True):
        clear_session_memory(api_url, st.session_state.session_id, runtime_mode)
        st.session_state.messages = []
        st.success('Mémoire effacée pour la session active.')

    st.markdown('### Exemples')
    st.markdown('- Que dit le GIEC sur 1,5°C ?')
    st.markdown('- Quelle est la météo à Paris aujourd’hui ?')
    st.markdown('- Calcule (18.5 * 4) / 3')
    st.markdown('- Ajoute à ma todo : revoir le chapitre sur les précipitations')

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if message.get('route'):
            st.caption(f"Route : {message['route']}")
        if message.get('used_tools'):
            st.caption('Outils: ' + ', '.join(message['used_tools']))
        if message.get('sources'):
            with st.expander('Sources'):
                for source in message['sources']:
                    st.markdown(
                        f"- **{source['source']}**" + (f" — page {source['page']}" if source.get('page') else '')
                    )
                    if source.get('excerpt'):
                        st.write(source['excerpt'])

user_input = st.chat_input('Posez une question météo ou climat...')
if user_input:
    st.session_state.messages.append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    with st.chat_message('assistant'):
        with st.spinner('Réponse en cours...'):
            payload = send_chat_message(api_url, st.session_state.session_id, user_input, runtime_mode)

        st.markdown(payload['answer'])
        st.caption(f"Route : {payload['route']}")
        if payload.get('used_tools'):
            st.caption('Outils: ' + ', '.join(payload['used_tools']))
        if payload.get('sources'):
            with st.expander('Sources'):
                for source in payload['sources']:
                    st.markdown(
                        f"- **{source['source']}**" + (f" — page {source['page']}" if source.get('page') else '')
                    )
                    if source.get('excerpt'):
                        st.write(source['excerpt'])

    st.session_state.messages.append(
        {
            'role': 'assistant',
            'content': payload['answer'],
            'route': payload['route'],
            'used_tools': payload.get('used_tools', []),
            'sources': payload.get('sources', []),
        }
    )
