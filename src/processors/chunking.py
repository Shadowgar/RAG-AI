from typing import List, Dict, Any

def chunk_document_elements(elements: List[Dict[str, Any]], chunk_size: int = 512, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Splits a list of document elements (from document_parser) into smaller,
    overlapping text chunks.

    Args:
        elements: A list of dictionaries representing parsed document elements.
        chunk_size: The maximum size of each text chunk (in characters).
        chunk_overlap: The number of characters to overlap between consecutive chunks.

    Returns:
        A list of dictionaries, where each dictionary represents a text chunk
        with its content and inherited metadata.
    """
    chunks: List[Dict[str, Any]] = []
    current_chunk_text = ""
    current_chunk_metadata: Dict[str, Any] = {}

    for element in elements:
        content = element.get("content", "")
        metadata = element.get("metadata", {})

        # Inherit metadata from the element for the current chunk
        # Simple merge for now, can be refined
        current_chunk_metadata.update(metadata)

        # Append content and split if necessary
        if len(current_chunk_text) + len(content) <= chunk_size:
            current_chunk_text += ("\n" + content).lstrip() # Add newline between elements
        else:
            # Current element makes the chunk too large, finalize current chunk
            if current_chunk_text:
                chunks.append({
                    "content": current_chunk_text,
                    "metadata": current_chunk_metadata.copy() # Use a copy
                })

            # Start a new chunk with overlap from the end of the previous content
            overlap_text = current_chunk_text[-chunk_overlap:] if chunk_overlap > 0 else ""
            current_chunk_text = overlap_text + ("\n" + content).lstrip()
            current_chunk_metadata = metadata.copy() # Start new metadata from current element

            # If the current element itself is larger than chunk_size, split it
            while len(current_chunk_text) > chunk_size:
                 chunks.append({
                    "content": current_chunk_text[:chunk_size],
                    "metadata": current_chunk_metadata.copy()
                })
                 current_chunk_text = current_chunk_text[chunk_size - chunk_overlap:] if chunk_overlap > 0 else current_chunk_text[chunk_size:]
                 current_chunk_metadata = metadata.copy() # Keep metadata for subsequent splits of this element


    # Add the last chunk if it's not empty
    if current_chunk_text:
        chunks.append({
            "content": current_chunk_text,
            "metadata": current_chunk_metadata.copy()
        })

    return chunks

# Example Usage (requires document_parser)
if __name__ == "__main__":
    # This example requires a dummy file and the document_parser module
    # Ensure you have a test file like data/documents/dummy.docx
    dummy_file_path = "data/documents/dummy.docx" # Replace with a real test file path if available
    try:
        from .document_parser import parse_document
        if os.path.exists(dummy_file_path):
            print(f"Parsing and chunking {dummy_file_path}...")
            elements = parse_document(dummy_file_path)
            if elements:
                chunks = chunk_document_elements(elements, chunk_size=200, chunk_overlap=20)
                print(f"Created {len(chunks)} chunks.")
                for i, chunk in enumerate(chunks):
                    print(f"--- Chunk {i+1} ---")
                    print(f"Content: {chunk.get('content')}")
                    print(f"Metadata: {chunk.get('metadata')}")
            else:
                print("No elements parsed from the document.")
        else:
            print(f"Test file not found at {dummy_file_path}. Skipping chunking test.")
            print("Please create a test file (e.g., data/documents/dummy.docx) to run this example.")

    except ImportError:
        print("Could not import document_parser. Skipping chunking test.")
    except Exception as e:
        print(f"Error during chunking test: {e}")

def chunk_text_by_tokens(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> List[str]:
    """Placeholder for chunking text by tokens."""
    return [text]
