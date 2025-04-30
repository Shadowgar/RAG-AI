import faiss
import numpy as np
import os
from typing import List, Dict, Any, Optional
from ..config import settings # Assuming config is in src/

class VectorStore:
    """
    Manages the FAISS vector index for storing and searching document embeddings.
    Metadata is assumed to be stored and managed externally (e.g., in SQLite).
    This class stores a mapping from FAISS index ID to an external ID.
    """
    def __init__(self, index_path: str = settings.VECTOR_DB_DIR):
        """
        Initializes or loads the FAISS index.

        Args:
            index_path: Directory path to save/load the index and ID mapping.
        """
        self.index_path = index_path
        self.index: Optional[faiss.Index] = None
        self.index_id_to_external_id: List[Any] = [] # Map FAISS internal ID to external ID (e.g., chunk ID)
        self.dimension = None # Dimension of the embeddings

        os.makedirs(self.index_path, exist_ok=True)
        self._index_file = os.path.join(self.index_path, "faiss.index")
        self._id_map_file = os.path.join(self.index_path, "id_map.npy")

        self.load() # Attempt to load existing index on initialization

    def initialize_index(self, dimension: int) -> None:
        """
        Initializes a new FAISS index (IndexIVFFlat) if one does not exist.
        IndexIVFFlat is an inverted file index that uses a flat (L2) index for
        quantization. It requires a training step to cluster the data.

        Args:
            dimension: The dimension of the vectors to be stored.
        """
        if self.index is None:
            self.dimension = dimension
            # Using IndexIVFFlat for faster search
            quantizer = faiss.IndexFlatL2(self.dimension)  # Quantizer is a simple L2 index
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, settings.FAISS_NLIST, faiss.METRIC_L2)
            print(f"Initialized new IndexIVFFlat index with dimension {self.dimension} and nlist {settings.FAISS_NLIST}")
        elif self.dimension != dimension:
            raise ValueError(f"Attempted to initialize index with dimension {dimension}, but existing index has dimension {self.dimension}")


    def train(self, embeddings: List[List[float]]) -> None:
        """
        Trains the IndexIVFFlat index with a sample of the data.
        This is a required step before adding vectors to the index.
        """
        if self.index is None:
            raise ValueError("Index not initialized. Call initialize_index first.")

        embeddings_np = np.array(embeddings).astype('float32')
        print("Training IndexIVFFlat...")
        self.index.train(embeddings_np)
        print("IndexIVFFlat training complete.")

    def add_embeddings(self, embeddings: List[List[float]], external_ids: List[Any]) -> None:
        """
        Adds embeddings to the FAISS index and updates the ID mapping.

        Args:
            embeddings: A list of embeddings (list of floats).
            external_ids: A list of external identifiers corresponding to the embeddings.
                          Must be the same length as embeddings.
        """
        if not embeddings:
            return

        embeddings_np = np.array(embeddings).astype('float32')

        if self.dimension is None:
            self.initialize_index(embeddings_np.shape[1])
        elif self.dimension != embeddings_np.shape[1]:
             raise ValueError(f"Embedding dimension mismatch. Expected {self.dimension}, got {embeddings_np.shape[1]}")


        if not self.index.is_trained:
            print("Index is not trained yet. Training now with a sample of the embeddings...")
            self.train(embeddings) # Train with a sample of the embeddings

        # Add vectors to the index
        self.index.add(embeddings_np)

        # Update the ID mapping
        self.index_id_to_external_id.extend(external_ids)

        print(f"Added {len(embeddings)} embeddings to the index.")


    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a similarity search on the FAISS index.

        Args:
            query_embedding: The embedding of the query.
            k: The number of nearest neighbors to retrieve.

        Returns:
            A list of dictionaries, each containing the external ID,
            FAISS distance, and FAISS index ID of a retrieved item.
        """
        if self.index is None or self.index.ntotal == 0:
            print("Index is empty. Cannot perform search.")
            return []

        query_embedding_np = np.array([query_embedding]).astype('float32')

        if self.dimension != query_embedding_np.shape[1]:
             raise ValueError(f"Query embedding dimension mismatch. Expected {self.dimension}, got {query_embedding_np.shape[1]}")


        # Set the number of probes (trade-off between speed and accuracy)
        self.index.nprobe = settings.FAISS_NPROBE

        # Perform the search
        distances, indices = self.index.search(query_embedding_np, k)

        results: List[Dict[str, Any]] = []
        # indices[0] contains the indices of the k nearest neighbors for the first query
        # distances[0] contains the distances for the k nearest neighbors
        for i in range(len(indices[0])):
            faiss_index_id = indices[0][i]
            distance = distances[0][i]

            # Ensure the FAISS index ID is valid and within the bounds of our mapping
            if 0 <= faiss_index_id < len(self.index_id_to_external_id):
                 external_id = self.index_id_to_external_id[faiss_index_id]
                 results.append({
                    "external_id": external_id,
                    "distance": float(distance), # Convert numpy float to standard float
                    "faiss_index_id": int(faiss_index_id) # Convert numpy int to standard int
                 })
            else:
                print(f"Warning: FAISS index ID {faiss_index_id} out of bounds for ID mapping.")


        return results

    def save(self):
        """
        Saves the FAISS index and the ID mapping to disk.
        """
        if self.index is not None:
            faiss.write_index(self.index, self._index_file) # Save trained index
            np.save(self._id_map_file, np.array(self.index_id_to_external_id, dtype=object))  # Use dtype=object for mixed types
            print(f"FAISS index and ID mapping saved to {self.index_path}")
        else:
            print("No index to save.")

    def load(self):
        """
        Loads the FAISS index and the ID mapping from disk.
        """
        if os.path.exists(self._index_file) and os.path.exists(self._id_map_file):
            try:
                self.index = faiss.read_index(self._index_file)  # Load trained index
                self.index_id_to_external_id = np.load(self._id_map_file, allow_pickle=True).tolist()
                self.dimension = self.index.d
                print(f"FAISS index and ID mapping loaded from {self.index_path}")
            except Exception as e:
                print(f"Error loading FAISS index or ID mapping: {e}")
                self.index = None
                self.index_id_to_external_id = []
                self.dimension = None
        else:
            print(f"No existing FAISS index or ID mapping found at {self.index_path}. A new index will be created when embeddings are added.")

    def get_size(self) -> int:
        """
        Returns the number of vectors in the index.
        """
        return self.index.ntotal if self.index else 0

# Example Usage
if __name__ == "__main__":
    # This example requires the embeddings module
    try:
        from .embeddings import EmbeddingModel
        # Create a dummy directory for the vector store
        test_vector_db_dir = "data/vector_db_test"
        os.makedirs(test_vector_db_dir, exist_ok=True)

        print("\nInitializing VectorStore...")
        vector_store = VectorStore(index_path=test_vector_db_dir)

        # Initialize embedding model
        embedding_model = EmbeddingModel()

        # Sample text chunks and their external IDs (e.g., chunk index or unique ID)
        sample_chunks = [
            "This is the first sentence for embedding.",
            "Here is the second sentence, which is different.",
            "And a third sentence to test adding to the index.",
            "Another piece of text for the fourth embedding.",
            "Fifth sentence to demonstrate adding more data.",
            "Sixth sentence to be added to the index."
        ]
        sample_external_ids = [f"chunk_{i}" for i in range(len(sample_chunks))]

        print("\nGenerating embeddings for sample chunks...")
        sample_embeddings = embedding_model.generate_embeddings(sample_chunks)

        print("\nAdding embeddings to VectorStore...")
        vector_store.add_embeddings(sample_embeddings, sample_external_ids) # Adds and trains if needed

        print(f"Vector store size: {vector_store.get_size()}")

        # Save the index
        vector_store.save()

        # Load the index into a new instance
        print("\nLoading VectorStore from disk...")
        loaded_vector_store = VectorStore(index_path=test_vector_db_dir)
        print(f"Loaded vector store size: {loaded_vector_store.get_size()}")

        # Perform a search
        query_text = "search for the first sentence"
        print(f"\nGenerating embedding for query: '{query_text}'")
        query_embedding = embedding_model.generate_embeddings([query_text])[0]

        print(f"\nSearching the vector store for top 3 similar chunks...")
        search_results = loaded_vector_store.search(query_embedding, k=3)

        print("\nSearch Results:")
        if search_results:
            for result in search_results:
                print(f"  External ID: {result['external_id']}, Distance: {result['distance']:.4f}, FAISS Index ID: {result['faiss_index_id']}")
        else:
            print("No search results.")

    except ImportError:
        print("Could not import EmbeddingModel. Skipping VectorStore test.")
    except Exception as e:
        print(f"Error during VectorStore test: {e}")
    finally:
        # Clean up dummy directory
        if os.path.exists(test_vector_db_dir):
            import shutil
            shutil.rmtree(test_vector_db_dir)
            print(f"\nCleaned up {test_vector_db_dir}")