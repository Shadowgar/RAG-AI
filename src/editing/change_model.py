# src/editing/change_model.py
from enum import Enum
from typing import Any, Dict, Optional, Union, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class ChangeType(str, Enum):
    """Enumeration for types of changes that can be applied to a document."""
    TEXT_UPDATE = "text_update" # General text update in a paragraph or run
    FORMAT_CHANGE = "format_change" # Formatting change for a run or paragraph
    PARAGRAPH_INSERT = "paragraph_insert" # Insertion of a new paragraph
    PARAGRAPH_DELETE = "paragraph_delete" # Deletion of an existing paragraph
    SECTION_REPLACE = "section_replace" # Replacement of content within a section (e.g., after a heading)
    TABLE_CELL_UPDATE = "table_cell_update" # Update text in a table cell
    TABLE_ROW_ADD = "table_row_add" # Add a row to a table
    # Add more types as needed, e.g., LIST_ITEM_UPDATE, TABLE_STRUCTURE_CHANGE

class ChangeStatus(str, Enum):
    """Enumeration for the status of a proposed change."""
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    APPLIED = "applied" # Accepted and successfully written to the document
    FAILED = "failed" # Attempted to apply but failed

class LocationParagraph(BaseModel):
    """Location identifier for a change within a specific paragraph."""
    paragraph_index: int
    run_index: Optional[int] = None # For changes specific to a run within a paragraph

class LocationTable(BaseModel):
    """Location identifier for a change within a table."""
    table_index: int
    row_index: int
    column_index: int

class LocationSection(BaseModel):
    """Location identifier for a change within a document section (e.g., identified by a heading)."""
    heading_text: str
    heading_style_name: Optional[str] = None
    # Could also include paragraph range if known

# Union type for various location specifications
ChangeLocation = Union[LocationParagraph, LocationTable, LocationSection, int, str, None]
# int could be paragraph_index for simple cases, str could be a unique element ID if available.

class DocumentChange(BaseModel):
    """
    Represents a single proposed or applied change to a document.
    """
    change_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str # Identifier for the document this change pertains to (e.g., filepath or DB ID)
    change_type: ChangeType
    location: ChangeLocation # Flexible field to specify where the change occurs
    
    # old_value and new_value can be complex.
    # For text updates, they are strings.
    # For formatting, they could be dicts of formatting attributes.
    # For insertions, old_value might be None.
    # For deletions, new_value might be None.
    # For section replace, new_value could be a list of paragraph strings.
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    description: Optional[str] = None # Human-readable description of the change
    status: ChangeStatus = ChangeStatus.PROPOSED
    source: Optional[str] = None # e.g., "LLM_suggestion", "user_edit"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # For formatting changes, specific attributes
    # old_format: Optional[Dict[str, Any]] = None
    # new_format: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True # Store enum values as strings

# Example Usage (for illustration, not part of the module's runnable code)
if __name__ == "__main__":
    # Example 1: Text update in a paragraph
    change1 = DocumentChange(
        document_id="docs/MySOP.docx",
        change_type=ChangeType.TEXT_UPDATE,
        location=LocationParagraph(paragraph_index=5, run_index=0),
        old_value="The old text segment.",
        new_value="The new, revised text segment.",
        description="Updated safety instruction in section 2.1."
    )
    print(change1.model_dump_json(indent=2))

    # Example 2: Paragraph deletion
    change2 = DocumentChange(
        document_id="docs/MySOP.docx",
        change_type=ChangeType.PARAGRAPH_DELETE,
        location=LocationParagraph(paragraph_index=10), # Location is the paragraph to be deleted
        old_value="This entire paragraph will be removed.", # Storing the old text for record
        new_value=None,
        description="Removed redundant paragraph."
    )
    print(change2.model_dump_json(indent=2))

    # Example 3: Section replacement
    change3 = DocumentChange(
        document_id="docs/MySOP.docx",
        change_type=ChangeType.SECTION_REPLACE,
        location=LocationSection(heading_text="Emergency Procedures", heading_style_name="Heading 1"),
        old_value="[Summary or hash of old section content]", # Or None if not easily captured
        new_value=["New procedure line 1.", "New procedure line 2.", "New procedure line 3."],
        description="Overhauled the Emergency Procedures section."
    )
    print(change3.model_dump_json(indent=2))

    # Example 4: Table cell update
    change4 = DocumentChange(
        document_id="docs/MySOP.docx",
        change_type=ChangeType.TABLE_CELL_UPDATE,
        location=LocationTable(table_index=0, row_index=1, column_index=2),
        old_value="Old cell value",
        new_value="New cell value",
        description="Corrected value in compliance table."
    )
    print(change4.model_dump_json(indent=2))