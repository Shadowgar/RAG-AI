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

    def process(self, file_path: str, replacements: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Processes a .docx file and extracts content and metadata.
        Extracts paragraphs and tables as separate chunks.
        """
        if not self.supports(file_path):
            raise ValueError("File type not supported by DocxProcessor")

        try:
            from docxtpl import DocxTemplate
            document = DocxTemplate(file_path)
            context = replacements if replacements else {}  # Use the replacements dictionary

            # Apply replacements
            document.render(context)

            # Manually update formatting after rendering
            for paragraph in document.paragraphs:
                for run in paragraph.runs:
                    if run.text.strip() in context.values():
                        for key, value in context.items():
                            if run.text.strip() == value:
                                if key == "bold":
                                    run.bold = True
                                elif key == "italic":
                                    run.italic = True

            # Extract chunks from the modified document
            chunks: List[Dict[str, Any]] = []
            for paragraph in document.paragraphs:
                for run in paragraph.runs:
                    metadata = {
                        "bold": run.bold,
                        "italic": run.italic,
                        "font_name": run.font.name,
                        "font_size": run.font.size.pt if run.font.size else None,
                        "source": file_path
                    }

                    # Debug print for run content and metadata
                    print(f"Run content: {run.text}, Metadata: {metadata}")

                    # Check if the run contains the replaced text
                    if run.text.strip() in context.values():
                        # Update metadata based on the context
                        for key, value in context.items():
                            if run.text.strip() == value:
                                if key == "bold":
                                    metadata["bold"] = True
                                elif key == "italic":
                                    metadata["italic"] = True

                    chunks.append({
                        "content": run.text,
                        "type": "paragraph",
                        "metadata": metadata
                    })

            return chunks

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []