import os
from typing import List, Dict, Any
from docx import Document
from .base_processor import DocumentProcessor

class DocxProcessor(DocumentProcessor):
    """
    Document processor for Word (.docx) files using python-docx.
    Extracts text and basic structure while attempting to preserve
    information relevant for later formatting.
    """

    def supports(self, file_path: str) -> bool:
        """
        Checks if the processor supports the given file type.
        """
        return os.path.splitext(file_path)[1].lower() == ".docx"

    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Processes a .docx file and extracts content and metadata.
        Extracts paragraphs and tables as separate chunks.
        """
        if not self.supports(file_path):
            raise ValueError("File type not supported by DocxProcessor")

        try:
            document = Document(file_path)
            chunks: List[Dict[str, Any]] = []

            # Extract paragraphs
            for i, paragraph in enumerate(document.paragraphs):
                if paragraph.text.strip(): # Only process non-empty paragraphs
                    chunks.append({
                        "content": paragraph.text,
                        "type": "paragraph",
                        "metadata": {
                            "source": file_path,
                            "paragraph_index": i,
                            "style": paragraph.style.name if paragraph.style else None,
                            # Add other relevant paragraph properties if needed
                        }
                    })

            # Extract tables (basic representation)
            for i, table in enumerate(document.tables):
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)

                # Represent table as a string for now, could be more structured
                table_string = "\n".join(["\t".join(row) for row in table_data])

                if table_string.strip(): # Only process non-empty tables
                     chunks.append({
                        "content": table_string,
                        "type": "table",
                        "metadata": {
                            "source": file_path,
                            "table_index": i,
                            # Add other relevant table properties if needed
                        }
                    })

            # Add document-level metadata (basic)
            doc_metadata = {
                "source": file_path,
                "title": document.core_properties.title,
                "author": document.core_properties.author,
                # Add other core properties as needed
            }
            # Optionally add document metadata as a separate chunk or to all chunks
            # For now, we'll just return the content chunks with source metadata

            return chunks

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []