import shutil
import time

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import Settings
from app.rag.loader import load_pdf_documents


def build_vector_store(settings: Settings, reset: bool = False) -> int:
    if reset and settings.chroma_path.exists():
        shutil.rmtree(settings.chroma_path, ignore_errors=True)
        settings.chroma_path.mkdir(parents=True, exist_ok=True)

    raw_documents = load_pdf_documents(settings.docs_dir)
    if not raw_documents:
        raise FileNotFoundError(
            f"Aucun PDF trouvé dans {settings.docs_dir.resolve()}. Ajoutez les documents puis relancez l'ingestion."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        separators=['\n\n', '\n', '. ', ' '],
    )
    chunks = splitter.split_documents(raw_documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata['chunk_id'] = index

    embeddings = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )

    vector_store = Chroma(
        persist_directory=str(settings.chroma_path),
        embedding_function=embeddings,
        collection_name='climate_docs',
    )

    batch_size = 20
    sleep_seconds = 2

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        vector_store.add_documents(batch)
        print(f'Batch ingéré : {start + 1} à {min(start + batch_size, len(chunks))} / {len(chunks)}')
        if start + batch_size < len(chunks):
            time.sleep(sleep_seconds)

    return len(chunks)
