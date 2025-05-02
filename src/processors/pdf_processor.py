import os
from typing import List, Dict, Any
import fitz  # PyMuPDF
from .base_processor import DocumentProcessor

class PdfProcessor(DocumentProcessor):
    """
    Document processor for PDF (.pdf) files using PyMuPDF (fitz).
    Extracts text content page by page.
    """

    def supports(self, file_path: str) -> bool:
        """
        Checks if the processor supports the given file type.
        """
        return os.path.splitext(file_path)[1].lower() == ".pdf"

    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Processes a .pdf file and extracts content page by page.

        Args:
            file_path: The path to the PDF file.

        Returns:
            A list of dictionaries, where each dictionary represents a page
            with its text content and associated metadata.
        """
        if not self.supports(file_path):
            raise ValueError("File type not supported by PdfProcessor")

        chunks: List[Dict[str, Any]] = []
        try:
            from unstructured.partition.auto import partition
            elements = partition(filename=file_path)

            for element in elements:
                metadata = element.metadata.to_dict() if hasattr(element, 'metadata') and element.metadata else {}
                metadata["source"] = file_path
                chunks.append({
                    "content": str(element),
                    "type": element.category if hasattr(element, 'category') else 'unknown',
                    "metadata": metadata
                })

            return chunks

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []