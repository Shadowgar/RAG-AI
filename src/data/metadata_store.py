import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
from ..config import settings
from datetime import datetime

class MetadataStore:
    """
    Manages the SQLite database for storing document and chunk metadata.
    Includes versioning for documents and stores chunk content.
    """
    def __init__(self, db_path: str = settings.METADATA_DB_PATH):
        """
        Initializes the MetadataStore and ensures the database directory exists.

        Args:
            db_path: The full path to the SQLite database file.
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._create_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Establishes and returns a connection to the SQLite database.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """
        Creates the necessary tables in the database if they don't exist.
        - documents: Stores metadata for original documents.
        - chunks: Stores metadata and content for document chunks, linked to documents.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT,
                    size INTEGER,
                    creation_time TEXT,
                    modification_time TEXT,
                    title TEXT,
                    author TEXT,
                    version INTEGER DEFAULT 1,
                    ingestion_time TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL, -- Added content column
                    chunk_type TEXT,
                    start_char INTEGER,
                    end_char INTEGER,
                    metadata JSON,
                    previous_chunk_id INTEGER,  -- Add previous_chunk_id column
                    next_chunk_id INTEGER,      -- Add next_chunk_id column
                    FOREIGN KEY (document_id) REFERENCES documents (id),
                    FOREIGN KEY (previous_chunk_id) REFERENCES chunks (id),  -- Add foreign key constraint
                    FOREIGN KEY (next_chunk_id) REFERENCES chunks (id),      -- Add foreign key constraint
                    UNIQUE (document_id, chunk_index)
                )
            """)

            conn.commit()
        print(f"Ensured database tables exist at {self.db_path}")

    def add_document_metadata(self, metadata: Dict[str, Any]) -> Optional[int]:
        """
        Adds metadata for a new document or updates an existing document's version.
        If a document with the same file_path exists, increments its version
        and updates modification_time.

        Args:
            metadata: A dictionary containing document metadata.
                      Expected keys: file_path, filename, file_type, size,
                      creation_time, modification_time, title, author.

        Returns:
            The ID of the inserted or updated document, or None if an error occurred.
        """
        file_path = metadata.get("file_path")
        if not file_path:
            print("Error: 'file_path' is required for adding document metadata.")
            return None

        existing_doc = self.get_document_by_path(file_path)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if existing_doc:
                    # Document exists, increment version and update modification time
                    new_version = existing_doc["version"] + 1
                    current_time = datetime.now().isoformat()
                    cursor.execute("""
                        UPDATE documents
                        SET version = ?, modification_time = ?
                        WHERE id = ?
                    """, (new_version, current_time, existing_doc["id"]))
                    conn.commit()
                    print(f"Updated document '{file_path}' to version {new_version}.")
                    return existing_doc["id"]
                else:
                    # Document does not exist, insert new record
                    cursor.execute("""
                        INSERT INTO documents (file_path, filename, file_type, size, creation_time, modification_time, title, author)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        file_path,
                        metadata.get("filename"),
                        metadata.get("file_type"),
                        metadata.get("size"),
                        metadata.get("creation_time"),
                        metadata.get("modification_time"),
                        metadata.get("title"),
                        metadata.get("author")
                    ))
                    conn.commit()
                    print(f"Added new document '{file_path}'.")
                    return cursor.lastrowid

        except sqlite3.IntegrityError as e:
             print(f"Integrity error adding/updating document metadata for {file_path}: {e}")
             return self.get_document_by_path(file_path)["id"]
        except Exception as e:
            print(f"Error adding/updating document metadata for {file_path}: {e}")
            return None


    def add_chunk_metadata(self, document_id: int, chunks_data: List[Dict[str, Any]]):
        """
        Adds metadata and content for chunks associated with a document to the chunks table.

        Args:
            document_id: The ID of the document the chunks belong to.
            chunks_data: A list of dictionaries, where each dictionary contains
                             chunk data. Expected keys: chunk_index, content,
                             chunk_type, start_char (optional), end_char (optional),
                             metadata (optional, will be stored as JSON).
        """
        if not chunks_data:
            return

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get existing chunks for the document to determine previous/next chunk IDs
                existing_chunks = self.get_chunks_by_document_id(document_id)
                existing_chunk_ids = [chunk['id'] for chunk in existing_chunks]

                # Prepare data for bulk insertion
                data_to_insert = []
                previous_chunk_id = None  # Initialize previous_chunk_id

                for i, chunk_data in enumerate(chunks_data):
                    # Determine next_chunk_id (if it exists)
                    next_chunk_id = None
                    if i + 1 < len(chunks_data):
                        next_chunk_id = None  # We can't know the actual ID yet, set to None for now

                    data_to_insert.append((
                        document_id,
                        chunk_data.get("chunk_index"),
                        chunk_data.get("content"), # Include content
                        chunk_data.get("chunk_type"),
                        chunk_data.get("start_char"),
                        chunk_data.get("end_char"),
                        json.dumps(chunk_data.get("metadata", {})), # Store metadata as JSON string
                        previous_chunk_id,
                        next_chunk_id
                    ))
                    previous_chunk_id = None # We can't know the actual ID yet

                # Consider deleting old chunks for this document_id before inserting new ones
                # This depends on the desired versioning strategy (e.g., keep all versions vs. replace)
                # For now, we'll just insert, assuming external logic handles cleanup if needed.
                # cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))

                cursor.executemany("""
                    INSERT INTO chunks (document_id, chunk_index, content, chunk_type, start_char, end_char, metadata, previous_chunk_id, next_chunk_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data_to_insert)

                # Get the newly inserted chunk IDs
                cursor.execute("SELECT id FROM chunks WHERE document_id = ? ORDER BY chunk_index", (document_id,))
                new_chunk_ids = [row[0] for row in cursor.fetchall()]

                # Update previous_chunk_id and next_chunk_id for all chunks
                for i, chunk_id in enumerate(new_chunk_ids):
                    prev_chunk_id = new_chunk_ids[i - 1] if i > 0 else None
                    next_chunk_id = new_chunk_ids[i + 1] if i < len(new_chunk_ids) - 1 else None

                    cursor.execute("""
                        UPDATE chunks SET previous_chunk_id = ?, next_chunk_id = ? WHERE id = ?
                    """, (prev_chunk_id, next_chunk_id, chunk_id))

                conn.commit()
                print(f"Added {len(chunks_data)} chunk entries for document ID {document_id}.")
        except Exception as e:
            print(f"Error adding chunk data for document ID {document_id}: {e}")

    def get_document_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest version of document metadata by file path.

        Args:
            file_path: The path of the document file.

        Returns:
            A dictionary containing document metadata, or None if not found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents WHERE file_path = ?", (file_path,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error retrieving document by path {file_path}: {e}")
            return None

    def get_chunks_by_document_id(self, document_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves chunk metadata and content for a given document ID.

        Args:
            document_id: The ID of the document.

        Returns:
            A list of dictionaries containing chunk data (including content and metadata).
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index", (document_id,))
                rows = cursor.fetchall()
                # Convert JSON metadata back to dictionary
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error retrieving chunks for document ID {document_id}: {e}")
            return []

    def get_chunk_by_id(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single chunk by its ID.

        Args:
            chunk_id: The ID of the chunk.

        Returns:
            A dictionary containing chunk data, or None if not found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error retrieving chunk by ID {chunk_id}: {e}")
            return None

    def get_previous_chunk(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves the previous chunk given a chunk ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chunks WHERE id = (SELECT previous_chunk_id FROM chunks WHERE id = ?)", (chunk_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error retrieving previous chunk for chunk ID {chunk_id}: {e}")
            return None

    def get_next_chunk(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves the next chunk given a chunk ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chunks WHERE id = (SELECT next_chunk_id FROM chunks WHERE id = ?)", (chunk_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error retrieving next chunk for chunk ID {chunk_id}: {e}")
            return None


# Example Usage
if __name__ == "__main__":
    print("Initializing MetadataStore and creating tables...")
    # Use a temporary database for the example
    temp_db_path = os.path.join(settings.METADATA_DB_DIR, "temp_metadata_test.db")
    metadata_store = MetadataStore(db_path=temp_db_path)
    print("MetadataStore initialized.")

    # Example of adding and updating document metadata
    dummy_doc_meta_v1 = {
        "file_path": "data/documents/versioned_doc.txt",
        "filename": "versioned_doc.txt",
        "file_type": "text/plain",
        "size": 100,
        "creation_time": datetime.now().isoformat(),
        "modification_time": datetime.now().isoformat(),
        "title": "Versioned Document",
        "author": "Test User"
    }

    print("\nAdding document version 1...")
    doc_id_v1 = metadata_store.add_document_metadata(dummy_doc_meta_v1)
    print(f"Document ID: {doc_id_v1}")

    doc_v1 = metadata_store.get_document_by_path("data/documents/versioned_doc.txt")
    print("Document V1 metadata:", dict(doc_v1) if doc_v1 else "Not found")

    # Simulate updating the document
    dummy_doc_meta_v2 = {
        "file_path": "data/documents/versioned_doc.txt", # Same file path
        "filename": "versioned_doc.txt",
        "file_type": "text/plain",
        "size": 150, # Simulate size change
        "creation_time": dummy_doc_meta_v1["creation_time"], # Keep original creation time
        "modification_time": datetime.now().isoformat(), # Update modification time
        "title": "Versioned Document Updated", # Simulate title change
        "author": "Test User"
    }

    print("\nAdding document version 2 (updating existing)...")
    doc_id_v2 = metadata_store.add_document_metadata(dummy_doc_meta_v2)
    print(f"Document ID (should be same as V1): {doc_id_v2}")

    doc_v2 = metadata_store.get_document_by_path("data/documents/versioned_doc.txt")
    print("Document V2 metadata:", dict(doc_v2) if doc_v2 else "Not found")

    # Example of adding chunk metadata (simplified)
    if doc_id_v2:
        dummy_chunks_data = [
            {"chunk_index": 0, "content": "This is the content of chunk 0.", "chunk_type": "paragraph", "metadata": {"page": 1}},
            {"chunk_index": 1, "content": "This is the content of chunk 1.", "chunk_type": "paragraph", "metadata": {"page": 1}},
        ]
        print(f"\nAdding chunk data for document ID {doc_id_v2}...")
        metadata_store.add_chunk_metadata(doc_id_v2, dummy_chunks_data)

        print(f"\nRetrieving chunks for document ID {doc_id_v2}...")
        retrieved_chunks = metadata_store.get_chunks_by_document_id(doc_id_v2)
        print(f"Retrieved {len(retrieved_chunks)} chunks.")
        if retrieved_chunks:
            print("First retrieved chunk content:", retrieved_chunks[0].get("content"))
            print("First retrieved chunk metadata:", json.loads(retrieved_chunks[0].get("metadata", "{}")))

        # Example of retrieving previous and next chunks
        first_chunk_id = retrieved_chunks[0]["id"]
        second_chunk_id = retrieved_chunks[1]["id"]

        prev_chunk = metadata_store.get_previous_chunk(second_chunk_id)
        next_chunk = metadata_store.get_next_chunk(first_chunk_id)

        print("\nPrevious chunk of chunk 2:", prev_chunk.get("content") if prev_chunk else "None")
        print("Next chunk of chunk 1:", next_chunk.get("content") if next_chunk else "None")


    # Clean up the temporary database file
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
        print(f"\nCleaned up temporary database file: {temp_db_path}")
    if os.path.exists(os.path.dirname(temp_db_path)):
         # Clean up the metadata directory if it's empty
         try:
             os.rmdir(os.path.dirname(temp_db_path))
         except OSError:
             # Directory not empty, ignore
             pass