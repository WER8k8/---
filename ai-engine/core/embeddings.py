from ai_engine.core.config import ai_settings

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name=ai_settings.embedding_model)
except ImportError:
    embeddings = None
