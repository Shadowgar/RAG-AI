import pytest
import json
from typing import List, Dict, Any, Optional
from unittest.mock import MagicMock

from src.rag.retriever import Retriever
from src.rag.embeddings import EmbeddingModel
from src.rag.vector_store import VectorStore
from src.data.metadata_store import MetadataStore
from src.llm.gemini import GeminiClient

# Mock classes and functions for testing
class MockEmbeddingModel:
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [[0.1 * i for i in range(384)] for _ in range(len(texts))]  # Dummy embeddings

class MockVectorStore:
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        # Return dummy search results
        return [{"external_id": i, "distance": 0.1 * i, "faiss_index_id": i} for i in range(k)]

class MockMetadataStore:
    def get_chunk_by_id(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        # Return dummy chunk data
        return {
            "id": chunk_id,
            "document_id": 1,
            "chunk_index": chunk_id,
            "content": f"This is chunk {chunk_id}.",
            "chunk_type": "paragraph",
            "metadata": json.dumps({"topic": "test"}),
        }
    def _get_connection(self):
        # Mock the _get_connection method
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    def get_chunks_by_document_id(self, document_id: int) -> List[Dict[str, Any]]:
        # Return dummy chunk data
        return [
            {
                "id": 1,
                "document_id": document_id,
                "chunk_index": 0,
                "content": "This is chunk 1 for document " + str(document_id),
                "chunk_type": "paragraph",
                "metadata": json.dumps({"topic": "test"}),
            },
            {
                "id": 2,
                "document_id": document_id,
                "chunk_index": 1,
                "content": "This is chunk 2 for document " + str(document_id),
                "chunk_type": "paragraph",
                "metadata": json.dumps({"topic": "test"}),
            },
        ]

class MockGeminiClient:
    def generate_response(self, prompt: str) -> str:
        return "This is a dummy response."

@pytest.fixture
def retriever():
    embedding_model = MockEmbeddingModel()
    vector_store = MockVectorStore()
    metadata_store = MockMetadataStore()
    gemini_client = MockGeminiClient()
    retriever = Retriever(embedding_model, vector_store, metadata_store, gemini_client)
    return retriever

def test_retrieve_basic(retriever: Retriever):
    query = "test query"
    results = retriever.retrieve(query, k=3)
    assert len(results) == 3
    assert all("content" in r for r in results)
    assert all("response" in r for r in results)

def test_retrieve_metadata_filtering(retriever: Retriever):
    query = "test query"
    metadata_filters = {"topic": "test"}
    results = retriever.retrieve(query, k=3, metadata_filters=metadata_filters)
    assert len(results) == 3
    assert all("content" in r for r in results)
    assert all("response" in r for r in results)
    assert all(json.loads(r["metadata"]).get("topic") == "test" for r in results)

def test_retrieve_context_window_management(retriever: Retriever):
    query = "test query"
    results = retriever.retrieve(query, k=5)
    context_length = sum(len(r["content"]) for r in results)
    assert context_length > 0 # Basic check that context is being created

def test_retrieve_caching(retriever: Retriever, capsys):
    """Tests the retrieval caching mechanism."""
    query = "test query"
    k = 3

    # 1. First call - should be a cache MISS
    results_pass1 = retriever.retrieve(query, k=k)
    captured1 = capsys.readouterr()
    assert "Retrieving results from cache - MISS" in captured1.out

    # 2. Second call - should be a cache HIT
    results_pass2 = retriever.retrieve(query, k=k)
    captured2 = capsys.readouterr()
    assert "Retrieving results from cache - HIT" in captured2.out
    assert results_pass1 == results_pass2 # Results should be identical from cache

    # 3. Clear cache
    retriever.clear_cache()
    captured_clear = capsys.readouterr()
    assert "Retrieval cache cleared" in captured_clear.out

    # 4. Third call - should be a cache MISS again
    results_pass3 = retriever.retrieve(query, k=k)
    captured3 = capsys.readouterr()
    assert "Retrieving results from cache - MISS" in captured3.out
    assert results_pass1 == results_pass3 # Results should still be identical if retrieval is deterministic