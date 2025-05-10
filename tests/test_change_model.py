# tests/test_change_model.py
import unittest
import uuid
from datetime import datetime
from pydantic import ValidationError

from src.editing.change_model import (
    DocumentChange,
    ChangeType,
    ChangeStatus,
    LocationParagraph,
    LocationTable,
    LocationSection
)

class TestChangeModel(unittest.TestCase):
    """Unit tests for the DocumentChange data model."""

    def test_01_create_text_update_change(self):
        """Test creation of a TEXT_UPDATE change."""
        loc = LocationParagraph(paragraph_index=5, run_index=0)
        change = DocumentChange(
            document_id="doc1.docx",
            change_type=ChangeType.TEXT_UPDATE,
            location=loc,
            old_value="old text",
            new_value="new text",
            description="Fixed a typo."
        )
        self.assertIsInstance(uuid.UUID(change.change_id), uuid.UUID)
        self.assertEqual(change.document_id, "doc1.docx")
        self.assertEqual(change.change_type, ChangeType.TEXT_UPDATE)
        self.assertEqual(change.location, loc)
        self.assertEqual(change.old_value, "old text")
        self.assertEqual(change.new_value, "new text")
        self.assertEqual(change.description, "Fixed a typo.")
        self.assertEqual(change.status, ChangeStatus.PROPOSED)
        self.assertIsInstance(change.timestamp, datetime)

    def test_02_create_paragraph_insert_change(self):
        """Test creation of a PARAGRAPH_INSERT change."""
        # For insertion, location might be the index *before* which to insert,
        # or after which to insert. Let's assume it's 'at this index, this new para appears'.
        # Or, it could be 'after paragraph_index X'.
        # The model's LocationParagraph is flexible. Here, let's say it's inserting at index 3.
        loc = LocationParagraph(paragraph_index=3) 
        change = DocumentChange(
            document_id="doc2.docx",
            change_type=ChangeType.PARAGRAPH_INSERT,
            location=loc, # Signifies insertion at/after this logical point
            new_value="This is a new paragraph.",
            old_value=None 
        )
        self.assertEqual(change.change_type, ChangeType.PARAGRAPH_INSERT)
        self.assertEqual(change.new_value, "This is a new paragraph.")
        self.assertIsNone(change.old_value)

    def test_03_create_paragraph_delete_change(self):
        """Test creation of a PARAGRAPH_DELETE change."""
        loc = LocationParagraph(paragraph_index=7)
        change = DocumentChange(
            document_id="doc3.docx",
            change_type=ChangeType.PARAGRAPH_DELETE,
            location=loc,
            old_value="This paragraph was deleted.",
            new_value=None
        )
        self.assertEqual(change.change_type, ChangeType.PARAGRAPH_DELETE)
        self.assertEqual(change.old_value, "This paragraph was deleted.")
        self.assertIsNone(change.new_value)

    def test_04_create_section_replace_change(self):
        """Test creation of a SECTION_REPLACE change."""
        loc = LocationSection(heading_text="Section Title", heading_style_name="Heading 1")
        new_content = ["New line 1 for section.", "New line 2 for section."]
        change = DocumentChange(
            document_id="doc4.docx",
            change_type=ChangeType.SECTION_REPLACE,
            location=loc,
            old_value="[summary of old section]",
            new_value=new_content
        )
        self.assertEqual(change.change_type, ChangeType.SECTION_REPLACE)
        self.assertEqual(change.new_value, new_content)

    def test_05_create_table_cell_update_change(self):
        """Test creation of a TABLE_CELL_UPDATE change."""
        loc = LocationTable(table_index=0, row_index=1, column_index=2)
        change = DocumentChange(
            document_id="doc5.docx",
            change_type=ChangeType.TABLE_CELL_UPDATE,
            location=loc,
            old_value="old cell data",
            new_value="new cell data"
        )
        self.assertEqual(change.change_type, ChangeType.TABLE_CELL_UPDATE)
        self.assertEqual(change.location, loc)

    def test_06_default_values_and_serialization(self):
        """Test default value generation and JSON serialization."""
        change = DocumentChange(
            document_id="doc6.docx",
            change_type=ChangeType.TEXT_UPDATE,
            location=LocationParagraph(paragraph_index=0),
            new_value="test"
        )
        self.assertIsNotNone(change.change_id)
        self.assertEqual(change.status, ChangeStatus.PROPOSED) # "proposed" as string due to use_enum_values
        self.assertLessEqual(
            (datetime.utcnow() - change.timestamp).total_seconds(), 
            1 # Should be very close to now
        )
        
        json_output = change.model_dump_json()
        self.assertIn(change.change_id, json_output)
        self.assertIn(ChangeType.TEXT_UPDATE.value, json_output) # Enum value
        self.assertIn(ChangeStatus.PROPOSED.value, json_output) # Enum value

    def test_07_invalid_enum_values(self):
        """Test validation for invalid enum values."""
        with self.assertRaises(ValidationError):
            DocumentChange(
                document_id="doc7.docx",
                change_type="INVALID_CHANGE_TYPE", # type: ignore
                location=LocationParagraph(paragraph_index=0),
                new_value="test"
            )
        
        with self.assertRaises(ValidationError):
            DocumentChange(
                document_id="doc7.docx",
                change_type=ChangeType.TEXT_UPDATE,
                location=LocationParagraph(paragraph_index=0),
                new_value="test",
                status="INVALID_STATUS" # type: ignore
            )

    def test_08_location_types(self):
        """Test different valid location types."""
        # Integer as paragraph index
        change_int_loc = DocumentChange(
            document_id="doc8.docx",
            change_type=ChangeType.PARAGRAPH_DELETE,
            location=5, # Interpreted as paragraph index
            old_value="para 5 content"
        )
        self.assertEqual(change_int_loc.location, 5)

        # String as a generic ID (though our specific location models are preferred)
        change_str_loc = DocumentChange(
            document_id="doc8.docx",
            change_type=ChangeType.TEXT_UPDATE,
            location="unique_element_id_123",
            old_value="old",
            new_value="new"
        )
        self.assertEqual(change_str_loc.location, "unique_element_id_123")
        
        # None location
        change_none_loc = DocumentChange(
            document_id="doc8.docx",
            change_type=ChangeType.TEXT_UPDATE, # e.g. a global document property change
            location=None, 
            old_value="v1",
            new_value="v2"
        )
        self.assertIsNone(change_none_loc.location)


if __name__ == "__main__":
    unittest.main()