from abc import ABC, abstractmethod
from typing import List, Dict, Any

class DocumentProcessor(ABC):
    """
    Abstract base class for document processors.
    Defines the interface for processing various document types.
    """

    @abstractmethod
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Processes a document file and extracts content and metadata.

        Args:
            file_path: The path to the document file.

        Returns:
            A list of dictionaries, where each dictionary represents a chunk
            or section of the document with its content and associated metadata.
        """
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """
        Checks if the processor supports the given file type.

        Args:
            file_path: The path to the document file.

        Returns:
            True if the processor supports the file type, False otherwise.
        """
        pass