from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    """
    Project settings for the SOP RAG Update System.
    """
    # Gemini API Key
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")

    # Paths
    DATA_DIR: str = "data"
    DOCUMENTS_DIR: str = os.path.join(DATA_DIR, "documents")
    VECTOR_DB_DIR: str = os.path.join(DATA_DIR, "vector_db")
    METADATA_DB_DIR: str = os.path.join(DATA_DIR, "metadata")

    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32 # Optimize for RTX 3060 6GB VRAM

    # Vector Database
    VECTOR_DB_TYPE: str = "FAISS" # Or "ChromaDB"
    FAISS_NLIST: int = 100 # Number of clusters for IndexIVFFlat
    FAISS_NPROBE: int = 10 # Number of clusters to probe during search

    # SQLite Database
    METADATA_DB_NAME: str = "metadata.db"
    METADATA_DB_PATH: str = os.path.join(METADATA_DB_DIR, METADATA_DB_NAME)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

if __name__ == "__main__":
    # Example usage and print settings
    print("Loading settings...")
    print(f"GEMINI_API_KEY: {'*' * len(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else 'Not set'}")
    print(f"DOCUMENTS_DIR: {settings.DOCUMENTS_DIR}")
    print(f"EMBEDDING_MODEL: {settings.EMBEDDING_MODEL}")
    print(f"VECTOR_DB_TYPE: {settings.VECTOR_DB_TYPE}")
    print(f"METADATA_DB_PATH: {settings.METADATA_DB_PATH}")