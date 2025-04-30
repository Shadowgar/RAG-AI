import torch
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from ..config import settings # Assuming config is in src/

class EmbeddingModel:
    """
    Handles loading and generating embeddings using Sentence-Transformers.
    Optimized for batched processing on available hardware (CPU or GPU).
    Includes an in-memory cache for embeddings.
    """
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        """
        Initializes the embedding model and the embedding cache.

        Args:
            model_name: The name of the Sentence-Transformer model to load.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            print(f"Loaded embedding model: {model_name} on {self.device}")
        except Exception as e:
            print(f"Error loading embedding model {model_name}: {e}")
            print("Falling back to CPU.")
            self.device = "cpu"
            self.model = SentenceTransformer(model_name, device=self.device)
            print(f"Loaded embedding model: {model_name} on {self.device}")

        self.cache: Dict[str, List[float]] = {} # In-memory cache: text -> embedding

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of text strings using batched processing
        and an in-memory cache.

        Args:
            texts: A list of text strings (document chunks).

        Returns:
            A list of embeddings, where each embedding is a list of floats.
        """
        if not texts:
            return []

        # Separate texts into cached and non-cached
        texts_to_embed = []
        cached_embeddings = {}
        original_order_map = {} # To maintain the original order

        for i, text in enumerate(texts):
            if text in self.cache:
                cached_embeddings[text] = self.cache[text]
            else:
                texts_to_embed.append(text)
            original_order_map[text] = i # Store original index

        generated_embeddings = []
        if texts_to_embed:
            print(f"Generating embeddings for {len(texts_to_embed)} non-cached texts...")
            # Generate embeddings for non-cached texts in batches
            # Use mixed precision if on CUDA for potential memory savings
            precision = 'float16' if self.device == 'cuda' else 'float32'
            generated_embeddings_tensors = self.model.encode(
                texts_to_embed,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                show_progress_bar=True,
                convert_to_numpy=False,
                convert_to_tensor=True,
                precision=precision
            )
            generated_embeddings = generated_embeddings_tensors.tolist() # Convert to list of lists

            # Store newly generated embeddings in the cache
            for text, embedding in zip(texts_to_embed, generated_embeddings):
                self.cache[text] = embedding

        # Combine cached and generated embeddings, maintaining original order
        all_embeddings = [None] * len(texts)
        for text in texts:
            if text in self.cache:
                all_embeddings[original_order_map[text]] = self.cache[text]
            # Note: If a text was in texts_to_embed, its embedding is already in cache now

        return all_embeddings


# Example Usage
if __name__ == "__main__":
    # This example requires some text chunks
    sample_chunks = [
        "This is the first sentence for embedding.",
        "Here is the second sentence, which is different.",
        "And a third sentence to test batching.",
        "Another piece of text for the fourth embedding.",
        "Fifth sentence to fill up the batch.",
        "Sixth sentence to demonstrate another batch.",
        "This is the first sentence for embedding.", # Duplicate text for cache test
        "Here is the second sentence, which is different." # Duplicate text
    ]

    print("Initializing EmbeddingModel...")
    embedding_model = EmbeddingModel()

    print("\nGenerating embeddings for sample chunks (first pass)...")
    embeddings_pass1 = embedding_model.generate_embeddings(sample_chunks)

    print(f"\nGenerated {len(embeddings_pass1)} embeddings in the first pass.")
    print(f"Cache size after first pass: {len(embedding_model.cache)}")

    print("\nGenerating embeddings for sample chunks (second pass with duplicates)...")
    embeddings_pass2 = embedding_model.generate_embeddings(sample_chunks)

    print(f"\nGenerated {len(embeddings_pass2)} embeddings in the second pass.")
    print(f"Cache size after second pass: {len(embedding_model.cache)}")

    # Verify that embeddings for duplicate texts are the same
    assert embeddings_pass1[0] == embeddings_pass2[0]
    assert embeddings_pass1[1] == embeddings_pass2[1]
    assert embeddings_pass1[0] == embeddings_pass2[6] # Compare first text embedding with its duplicate
    assert embeddings_pass1[1] == embeddings_pass2[7] # Compare second text embedding with its duplicate

    print("\nCache test successful: Embeddings for duplicate texts were retrieved from cache.")

    if embeddings_pass1:
        print(f"Embedding dimension: {len(embeddings_pass1[0])}")