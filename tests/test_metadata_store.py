import pytest
import os
import sqlite3
import json
from datetime import datetime

# Assuming MetadataStore is in src/data/metadata_store
from src.data.metadata_store import MetadataStore
from src.config import settings # To get the base metadata directory

# Define path for the temporary test database
TEST_METADATA_DIR = "tests/temp_metadata_test_data"
TEST_DB_PATH = os.path.join(TEST_METADATA_DIR, "test_metadata.db")

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_database():
    """
    Fixture to create and remove a temporary database for each test function.
    """
    os.makedirs(TEST_METADATA_DIR, exist_ok=True)
    # Ensure the database file does not exist before the test
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    yield # This is where the test function runs

    # Teardown: remove the database file and directory
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    if os.path.exists(TEST_METADATA_DIR) and not os.listdir(TEST_METADATA_DIR):
         os.rmdir(TEST_METADATA_DIR)


# --- Test MetadataStore ---
def test_metadata_store_initialization():
    store = MetadataStore(db_path=TEST_DB_PATH)
    assert os.path.exists(TEST_DB_PATH)
    # Check if tables were created
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    table_names = [table[0] for table in tables]
    assert "documents" in table_names
    assert "chunks" in table_names

def test_metadata_store_add_document_metadata():
    store = MetadataStore(db_path=TEST_DB_PATH)
    doc_meta = {
        "file_path": "data/documents/doc1.txt",
        "filename": "doc1.txt",
        "file_type": ".txt",
        "size": 100,
        "creation_time": datetime.now().isoformat(),
        "modification_time": datetime.now().isoformat(),
        "title": "Document One",
        "author": "Author A"
    }
    doc_id = store.add_document_metadata(doc_meta)
    assert isinstance(doc_id, int)
    assert doc_id > 0

    # Verify the document was added
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row["file_path"] == doc_meta["file_path"]
    assert row["filename"] == doc_meta["filename"]
    assert row["version"] == 1 # Check default version

def test_metadata_store_add_document_metadata_duplicate_path():
    store = MetadataStore(db_path=TEST_DB_PATH)
    doc_meta_v1 = {
        "file_path": "data/documents/doc_duplicate.txt",
        "filename": "doc_duplicate.txt",
        "file_type": ".txt",
        "size": 100,
        "creation_time": datetime.now().isoformat(),
        "modification_time": datetime.now().isoformat(),
        "title": "Duplicate Document",
        "author": "Author B"
    }
    doc_id_v1 = store.add_document_metadata(doc_meta_v1)
    assert isinstance(doc_id_v1, int)

    # Add again with the same file_path
    doc_meta_v2 = {
        "file_path": "data/documents/doc_duplicate.txt", # Same path
        "filename": "doc_duplicate_v2.txt", # Different filename
        "file_type": ".txt",
        "size": 150, # Different size
        "creation_time": doc_meta_v1["creation_time"], # Same creation time
        "modification_time": datetime.now().isoformat(), # New modification time
        "title": "Duplicate Document Updated", # Different title
        "author": "Author B"
    }
    doc_id_v2 = store.add_document_metadata(doc_meta_v2)
    assert doc_id_v2 == doc_id_v1 # Should return the same ID

    # Verify the version was incremented and modification time updated
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id_v1,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row["file_path"] == doc_meta_v1["file_path"] # File path remains the same
    assert row["filename"] == doc_meta_v1["filename"] # Filename is NOT updated by add_document_metadata
    assert row["version"] == 2 # Version should be 2
    # Note: modification_time check is tricky due to timing, skip for now

def test_metadata_store_add_chunk_metadata():
    store = MetadataStore(db_path=TEST_DB_PATH)
    doc_meta = {
        "file_path": "data/documents/doc_with_chunks.txt",
        "filename": "doc_with_chunks.txt",
        "file_type": ".txt", "size": 200,
        "creation_time": datetime.now().isoformat(),
        "modification_time": datetime.now().isoformat(),
        "title": "Chunked Doc", "author": "Author C"
    }
    doc_id = store.add_document_metadata(doc_meta)
    assert doc_id is not None

    chunks_meta = [
        {"chunk_index": 0, "chunk_type": "paragraph", "metadata": {"page": 1, "text_snippet": "chunk 1 content"}},
        {"chunk_index": 1, "chunk_type": "table", "metadata": {"page": 1, "table_rows": 2}},
        {"chunk_index": 2, "chunk_type": "paragraph", "metadata": {"page": 2, "text_snippet": "chunk 3 content"}},
    ]
    store.add_chunk_metadata(doc_id, chunks_meta)

    # Verify chunks were added
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index", (doc_id,))
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == len(chunks_meta)
    for i, row in enumerate(rows):
        assert row["document_id"] == doc_id
        assert row["chunk_index"] == chunks_meta[i]["chunk_index"]
        assert row["chunk_type"] == chunks_meta[i]["chunk_type"]
        # Check JSON metadata
        retrieved_metadata = json.loads(row["metadata"])
        assert retrieved_metadata == chunks_meta[i]["metadata"]

def test_metadata_store_get_document_by_path():
    store = MetadataStore(db_path=TEST_DB_PATH)
    doc_meta = {
        "file_path": "data/documents/doc_to_get.txt",
        "filename": "doc_to_get.txt",
        "file_type": ".txt", "size": 50,
        "creation_time": datetime.now().isoformat(),
        "modification_time": datetime.now().isoformat(),
        "title": "Document to Retrieve", "author": "Author D"
    }
    store.add_document_metadata(doc_meta)

    retrieved_doc = store.get_document_by_path("data/documents/doc_to_get.txt")
    assert retrieved_doc is not None
    assert isinstance(retrieved_doc, dict)
    assert retrieved_doc["file_path"] == doc_meta["file_path"]
    assert retrieved_doc["filename"] == doc_meta["filename"]

    # Test retrieving non-existent document
    non_existent_doc = store.get_document_by_path("non_existent.txt")
    assert non_existent_doc is None

def test_metadata_store_get_chunks_by_document_id():
    store = MetadataStore(db_path=TEST_DB_PATH)
    doc_meta = {
        "file_path": "data/documents/doc_get_chunks.txt",
        "filename": "doc_get_chunks.txt",
        "file_type": ".txt", "size": 300,
        "creation_time": datetime.now().isoformat(),
        "modification_time": datetime.now().isoformat(),
        "title": "Get Chunks Doc", "author": "Author E"
    }
    doc_id = store.add_document_metadata(doc_meta)
    assert doc_id is not None

    chunks_meta = [
        {"chunk_index": 0, "chunk_type": "paragraph", "metadata": {"page": 1}},
        {"chunk_index": 1, "chunk_type": "paragraph", "metadata": {"page": 1}},
        {"chunk_index": 2, "chunk_type": "paragraph", "metadata": {"page": 2}},
    ]
    store.add_chunk_metadata(doc_id, chunks_meta)

    retrieved_chunks = store.get_chunks_by_document_id(doc_id)
    assert isinstance(retrieved_chunks, list)
    assert len(retrieved_chunks) == len(chunks_meta)
    # Check order and content
    for i, chunk in enumerate(retrieved_chunks):
        assert chunk["document_id"] == doc_id
        assert chunk["chunk_index"] == i # Check order
        assert json.loads(chunk["metadata"]) == chunks_meta[i]["metadata"] # Check metadata content

    # Test retrieving chunks for a non-existent document ID
    retrieved_chunks_non_existent = store.get_chunks_by_document_id(999)
    assert isinstance(retrieved_chunks_non_existent, list)
    assert len(retrieved_chunks_non_existent) == 0