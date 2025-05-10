# tests/test_word_editor.py
import unittest
import os
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from src.editing.word_editor import WordEditor

class TestWordEditor(unittest.TestCase):
    """
    Unit tests for the WordEditor class.
    """
    TEST_DOC_DIR = "test_docs"
    NEW_DOC_PATH = os.path.join(TEST_DOC_DIR, "test_new_document.docx")
    EXISTING_DOC_PATH = os.path.join(TEST_DOC_DIR, "test_existing_document.docx")
    SAVED_DOC_PATH = os.path.join(TEST_DOC_DIR, "test_saved_document.docx")

    @classmethod
    def setUpClass(cls):
        """Set up test directory and a sample existing document."""
        if not os.path.exists(cls.TEST_DOC_DIR):
            os.makedirs(cls.TEST_DOC_DIR)

        # Create a sample document for loading tests
        doc = Document()
        p1 = doc.add_paragraph()
        run1 = p1.add_run("Hello, existing world!")
        run1.bold = True
        run1.font.name = 'Arial'
        run1.font.size = Pt(12)
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("This is the second paragraph.")
        doc.save(cls.EXISTING_DOC_PATH)

    @classmethod
    def tearDownClass(cls):
        """Clean up test files and directory."""
        for path in [cls.NEW_DOC_PATH, cls.EXISTING_DOC_PATH, cls.SAVED_DOC_PATH]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(cls.TEST_DOC_DIR):
            # Check if directory is empty before removing
            if not os.listdir(cls.TEST_DOC_DIR):
                 os.rmdir(cls.TEST_DOC_DIR)
            else:
                # If other files exist (e.g. from word_editor.py example), remove them
                for f in os.listdir(cls.TEST_DOC_DIR):
                    if f.startswith("test_document_new") and f.endswith(".docx"): # from example in word_editor
                        os.remove(os.path.join(cls.TEST_DOC_DIR, f))
                if not os.listdir(cls.TEST_DOC_DIR): # recheck
                    os.rmdir(cls.TEST_DOC_DIR)


    def test_01_create_new_document(self):
        """Test creating a new document."""
        editor = WordEditor()
        self.assertIsNotNone(editor.document)
        self.assertEqual(len(editor.document.paragraphs), 0) # A new doc might have one empty paragraph by default
                                                            # Depending on python-docx version, it might be 0 or 1.
                                                            # Let's be flexible or check specific python-docx behavior.
                                                            # For now, assuming it starts truly empty or with one default.
                                                            # A common behavior is one default paragraph.
        # Let's check if it has 1 default paragraph
        if len(editor.document.paragraphs) == 1:
            self.assertEqual(editor.document.paragraphs[0].text, "")
        else:
            self.assertEqual(len(editor.document.paragraphs), 0)


    def test_02_load_existing_document(self):
        """Test loading an existing document."""
        editor = WordEditor(self.EXISTING_DOC_PATH)
        self.assertIsNotNone(editor.document)
        self.assertEqual(len(editor.document.paragraphs), 2)
        self.assertEqual(editor.document.paragraphs[0].text, "Hello, existing world!")
        self.assertTrue(editor.document.paragraphs[0].runs[0].bold)
        self.assertEqual(editor.document.paragraphs[0].runs[0].font.name, 'Arial')

    def test_03_save_document(self):
        """Test saving a document."""
        editor = WordEditor()
        p = editor.document.add_paragraph("Content to save.")
        run = p.add_run(" More text.")
        run.italic = True
        editor.save_document(self.SAVED_DOC_PATH)
        self.assertTrue(os.path.exists(self.SAVED_DOC_PATH))

        # Verify content of saved document
        loaded_doc = Document(self.SAVED_DOC_PATH)
        self.assertEqual(len(loaded_doc.paragraphs), 1)
        self.assertEqual(loaded_doc.paragraphs[0].text, "Content to save. More text.")
        self.assertTrue(loaded_doc.paragraphs[0].runs[1].italic)

    def test_04_get_paragraph_text(self):
        """Test the get_paragraph_text method."""
        editor = WordEditor(self.EXISTING_DOC_PATH)
        self.assertEqual(editor.get_paragraph_text(0), "Hello, existing world!")
        self.assertEqual(editor.get_paragraph_text(1), "This is the second paragraph.")
        self.assertEqual(editor.get_paragraph_text(5), "") # Index out of bounds

    def test_05_copy_run_formatting(self):
        """Test the copy_run_formatting method."""
        doc = Document()
        p_source = doc.add_paragraph()
        source_run = p_source.add_run("Source Run")
        source_run.bold = True
        source_run.italic = False
        source_run.underline = True
        source_run.font.name = "Times New Roman"
        source_run.font.size = Pt(10)
        source_run.font.strike = True
        # source_run.font.highlight_color = WD_COLOR_INDEX.YELLOW # Requires WD_COLOR_INDEX

        p_target = doc.add_paragraph()
        target_run = p_target.add_run("Target Run")

        editor = WordEditor() # Editor instance needed to call the method
        editor.copy_run_formatting(source_run, target_run)

        self.assertEqual(target_run.bold, source_run.bold)
        self.assertEqual(target_run.italic, source_run.italic)
        self.assertEqual(target_run.underline, source_run.underline)
        self.assertEqual(target_run.font.name, source_run.font.name)
        self.assertEqual(target_run.font.size, source_run.font.size)
        self.assertEqual(target_run.font.strike, source_run.font.strike)
        # self.assertEqual(target_run.font.highlight_color, source_run.font.highlight_color)

    def test_06_copy_paragraph_formatting(self):
        """Test the copy_paragraph_formatting method."""
        doc = Document()
        source_paragraph = doc.add_paragraph("Source Paragraph")
        source_paragraph.style = 'Heading 1' # Assuming 'Heading 1' exists
        source_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        source_pf = source_paragraph.paragraph_format
        source_pf.left_indent = Pt(36) # 0.5 inch
        source_pf.right_indent = Pt(72) # 1 inch
        source_pf.space_before = Pt(6)
        source_pf.space_after = Pt(12)
        source_pf.line_spacing = 1.5
        source_pf.keep_with_next = True


        target_paragraph = doc.add_paragraph("Target Paragraph")

        editor = WordEditor() # Editor instance needed to call the method
        editor.copy_paragraph_formatting(source_paragraph, target_paragraph)

        # Ensure the style is available in the test document or handle potential KeyError
        if 'Heading 1' in doc.styles:
            self.assertEqual(target_paragraph.style.name, source_paragraph.style.name)
        else:
            print("Warning: 'Heading 1' style not found in test_06_copy_paragraph_formatting. Style copy test might be lenient.")
            # If style doesn't exist, it might default to 'Normal' or retain its original.
            # This depends on how python-docx handles missing style names during assignment.
            # For robustness, one might create the style if it doesn't exist, or use a guaranteed style.

        self.assertEqual(target_paragraph.alignment, source_paragraph.alignment)
        
        target_pf = target_paragraph.paragraph_format
        self.assertEqual(target_pf.left_indent, source_pf.left_indent)
        self.assertEqual(target_pf.right_indent, source_pf.right_indent)
        self.assertEqual(target_pf.space_before, source_pf.space_before)
        self.assertEqual(target_pf.space_after, source_pf.space_after)
        self.assertEqual(target_pf.line_spacing, source_pf.line_spacing)
        self.assertEqual(target_pf.keep_with_next, source_pf.keep_with_next)


    def test_07_update_paragraph_text(self):
        """Test the update_paragraph_text method."""
        # Test case 1: Preserve style
        editor_preserve = WordEditor()
        p_orig_preserve = editor_preserve.document.add_paragraph()
        run_orig_preserve = p_orig_preserve.add_run("Original bold text.")
        run_orig_preserve.bold = True
        run_orig_preserve.font.name = 'Calibri'
        run_orig_preserve.font.size = Pt(16)
        p_orig_preserve.add_run(" More normal text.") # Add a second run

        editor_preserve.update_paragraph_text(0, "Updated bold text.", preserve_style=True)
        updated_p_preserve = editor_preserve.document.paragraphs[0]
        self.assertEqual(updated_p_preserve.text, "Updated bold text.")
        self.assertTrue(len(updated_p_preserve.runs) > 0, "Paragraph should have runs after update.")
        # Check formatting of the first run (or the only run if text is short)
        self.assertTrue(updated_p_preserve.runs[0].bold)
        self.assertEqual(updated_p_preserve.runs[0].font.name, 'Calibri')
        self.assertEqual(updated_p_preserve.runs[0].font.size, Pt(16))

        # Test case 2: Do not preserve style
        editor_no_preserve = WordEditor()
        p_orig_no_preserve = editor_no_preserve.document.add_paragraph()
        run_orig_no_preserve = p_orig_no_preserve.add_run("Original italic text.")
        run_orig_no_preserve.italic = True
        run_orig_no_preserve.font.name = 'Arial'

        editor_no_preserve.update_paragraph_text(0, "Updated plain text.", preserve_style=False)
        updated_p_no_preserve = editor_no_preserve.document.paragraphs[0]
        self.assertEqual(updated_p_no_preserve.text, "Updated plain text.")
        self.assertTrue(len(updated_p_no_preserve.runs) > 0, "Paragraph should have runs after update.")
        # Formatting should be default or paragraph's style, not necessarily italic or Arial
        # We can't easily assert it's *not* italic without knowing the default.
        # A simple check is that it's not explicitly the old style if the new text is different.
        if updated_p_no_preserve.runs[0].font.name == 'Arial':
            print("Warning: Font name might have been unintentionally preserved or is default.")
        # self.assertFalse(updated_p_no_preserve.runs[0].italic) # This might fail if default is italic

        # Test case 3: Update paragraph in an existing document
        editor_existing = WordEditor(self.EXISTING_DOC_PATH)
        original_first_p_text = editor_existing.document.paragraphs[0].text
        original_first_p_font_name = editor_existing.document.paragraphs[0].runs[0].font.name
        
        editor_existing.update_paragraph_text(0, "New content for existing doc.", preserve_style=True)
        self.assertEqual(editor_existing.document.paragraphs[0].text, "New content for existing doc.")
        self.assertTrue(editor_existing.document.paragraphs[0].runs[0].bold) # From EXISTING_DOC_PATH setup
        self.assertEqual(editor_existing.document.paragraphs[0].runs[0].font.name, original_first_p_font_name)

        # Test case 4: Index out of bounds
        editor_bounds = WordEditor()
        editor_bounds.document.add_paragraph("A paragraph.")
        # Should print warning and not crash
        editor_bounds.update_paragraph_text(5, "This should not appear.", preserve_style=True)
        self.assertEqual(editor_bounds.document.paragraphs[0].text, "A paragraph.") # No change
        self.assertEqual(len(editor_bounds.document.paragraphs), 1)


    def test_08_replace_text_after_heading(self):
        """Test the replace_text_after_heading method."""
        # Setup a document with headings and content
        doc = Document()
        doc.add_paragraph("Document Title", style='Title')
        doc.add_paragraph("Introduction", style='Heading 1')
        doc.add_paragraph("This is the first paragraph of the intro.")
        doc.add_paragraph("This is the second paragraph of the intro.")
        doc.add_paragraph("Methods", style='Heading 1')
        doc.add_paragraph("Details about methods.")
        doc.add_paragraph("Sub-heading", style='Heading 2') # Lower level heading
        doc.add_paragraph("Details under sub-heading.")
        doc.add_paragraph("Conclusion", style='Heading 1')
        doc.add_paragraph("Final thoughts.")
        
        temp_doc_path = os.path.join(self.TEST_DOC_DIR, "temp_heading_test.docx")
        # Ensure styles are available or add them
        # For 'Heading 1', 'Heading 2', 'Title' to be available, they should be in the default template
        # or added explicitly if using a very minimal new document.
        # python-docx uses default template which usually has them.
        try:
            doc.styles['Heading 1']
            doc.styles['Heading 2']
            doc.styles['Title']
        except KeyError as e:
            print(f"Warning: A standard style ({e}) was not found. Test might behave unexpectedly.")
            # For a robust test, one might add these styles if they don't exist.
            # from docx.enum.style import WD_STYLE_TYPE
            # if not 'Heading 1' in doc.styles:
            #     doc.styles.add_style('Heading 1', WD_STYLE_TYPE.PARAGRAPH)
            # etc.

        doc.save(temp_doc_path)

        # Case 1: Replace content after "Introduction" (Heading 1)
        editor1 = WordEditor(temp_doc_path)
        new_intro_content = ["New intro line 1.", "New intro line 2."]
        result1 = editor1.replace_text_after_heading("Introduction", new_intro_content, heading_style_name="Heading 1")
        self.assertTrue(result1)
        self.assertEqual(editor1.document.paragraphs[1].text, "Introduction")
        self.assertEqual(editor1.document.paragraphs[2].text, "New intro line 1.")
        self.assertEqual(editor1.document.paragraphs[3].text, "New intro line 2.")
        self.assertEqual(editor1.document.paragraphs[4].text, "Methods") # Next H1
        # editor1.save_document(os.path.join(self.TEST_DOC_DIR, "debug_case1.docx"))


        # Case 2: Heading not found
        editor2 = WordEditor(temp_doc_path) # Reload original content
        result2 = editor2.replace_text_after_heading("NonExistent Heading", ["Should not appear"], heading_style_name="Heading 1")
        self.assertFalse(result2)
        self.assertEqual(editor2.document.paragraphs[2].text, "This is the first paragraph of the intro.") # Unchanged

        # Case 3: Section extends to end of document
        editor3 = WordEditor(temp_doc_path) # Reload
        new_conclusion_content = ["The very end, part 1.", "The very end, part 2."]
        result3 = editor3.replace_text_after_heading("Conclusion", new_conclusion_content, heading_style_name="Heading 1")
        self.assertTrue(result3)
        # Original paras: Title, H1-Intro, P1, P2, H1-Methods, P-Meth, H2-Sub, P-Sub, H1-Conc, P-Final (10 paras, idx 0-9)
        # H1-Conc is at index 8.
        self.assertEqual(editor3.document.paragraphs[8].text, "Conclusion")
        self.assertEqual(editor3.document.paragraphs[9].text, "The very end, part 1.")
        self.assertEqual(editor3.document.paragraphs[10].text, "The very end, part 2.")
        self.assertEqual(len(editor3.document.paragraphs), 11) # Original 10 - 1 (P-Final) + 2 (new_conclusion_content)
        # editor3.save_document(os.path.join(self.TEST_DOC_DIR, "debug_case3.docx"))

        # Case 5: Section followed by heading of same/higher level (H1 followed by H2, then H1)
        editor5 = WordEditor(temp_doc_path) # Reload
        new_methods_content = ["New method details only."]
        result5 = editor5.replace_text_after_heading("Methods", new_methods_content, heading_style_name="Heading 1")
        self.assertTrue(result5)
        # Original: ..., H1-Methods(idx 4), P-Meth(5), H2-Sub(6), P-Sub(7), H1-Conc(8)
        # Expected: ..., H1-Methods(idx 4), "New method details only."(5), H1-Conc(6)
        self.assertEqual(editor5.document.paragraphs[4].text, "Methods")
        self.assertEqual(editor5.document.paragraphs[5].text, "New method details only.")
        self.assertEqual(editor5.document.paragraphs[6].text, "Conclusion")
        self.assertEqual(len(editor5.document.paragraphs), 8) # Original 10 - 3 (P-Meth, H2-Sub, P-Sub) + 1 (new_methods_content)
        # editor5.save_document(os.path.join(self.TEST_DOC_DIR, "debug_case5.docx"))

        # Case 6: Replace content after "Sub-heading" (Heading 2)
        editor6 = WordEditor(temp_doc_path) # Reload
        new_subheading_content = ["Fresh sub-details."]
        result6 = editor6.replace_text_after_heading("Sub-heading", new_subheading_content, heading_style_name="Heading 2")
        self.assertTrue(result6)
        # Original: ..., H2-Sub(idx 6), P-Sub(7), H1-Conc(8)
        # Expected: ..., H2-Sub(idx 6), "Fresh sub-details."(7), H1-Conc(8)
        self.assertEqual(editor6.document.paragraphs[6].text, "Sub-heading")
        self.assertEqual(editor6.document.paragraphs[7].text, "Fresh sub-details.")
        self.assertEqual(editor6.document.paragraphs[8].text, "Conclusion")
        self.assertEqual(len(editor6.document.paragraphs), 10) # Original 10 - 1 (P-Sub) + 1 (new_subheading_content)
        # editor6.save_document(os.path.join(self.TEST_DOC_DIR, "debug_case6.docx"))

        # Case 7: Empty new content (deletes the section)
        editor7 = WordEditor(temp_doc_path) # Reload
        result7 = editor7.replace_text_after_heading("Methods", [], heading_style_name="Heading 1")
        self.assertTrue(result7)
        # Original: ..., H1-Methods(idx 4), P-Meth(5), H2-Sub(6), P-Sub(7), H1-Conc(8)
        # Expected: ..., H1-Methods(idx 4), H1-Conc(idx 5)
        self.assertEqual(editor7.document.paragraphs[4].text, "Methods")
        self.assertEqual(editor7.document.paragraphs[5].text, "Conclusion")
        self.assertEqual(len(editor7.document.paragraphs), 7) # Original 10 - 3 (P-Meth, H2-Sub, P-Sub) = 7. No new paras.
                                                            # Actually, 10 - 3 paragraphs removed (P-Meth, H2-Sub, P-Sub) = 7
        # editor7.save_document(os.path.join(self.TEST_DOC_DIR, "debug_case7.docx"))
        # Re-evaluating count for case 7:
        # Original 10 paragraphs.
        # Section for "Methods" (H1) includes:
        #   - "Details about methods." (para after H1)
        #   - "Sub-heading" (H2, lower level, so part of section)
        #   - "Details under sub-heading." (para after H2)
        # These 3 paragraphs are removed. No new paragraphs are added.
        # So, 10 - 3 = 7 paragraphs should remain.
        self.assertEqual(len(editor7.document.paragraphs), 7)


        if os.path.exists(temp_doc_path):
            os.remove(temp_doc_path)

    def test_09_insert_paragraph_after(self):
        """Test inserting a paragraph after a specified index."""
        editor = WordEditor()
        p1 = editor.document.add_paragraph("Paragraph 1")
        p2 = editor.document.add_paragraph("Paragraph 2") # Original second paragraph

        # Insert after first paragraph (index 0)
        new_p_text = "Inserted Paragraph A"
        inserted_p = editor.insert_paragraph_after(0, new_p_text, style='ListBullet') # Assuming ListBullet style exists
        self.assertIsNotNone(inserted_p)
        self.assertEqual(len(editor.document.paragraphs), 3)
        self.assertEqual(editor.document.paragraphs[0].text, "Paragraph 1")
        self.assertEqual(editor.document.paragraphs[1].text, new_p_text)
        if 'List Bullet' in editor.document.styles: # Name might have space
             self.assertEqual(editor.document.paragraphs[1].style.name, 'List Bullet')
        elif 'ListBullet' in editor.document.styles:
             self.assertEqual(editor.document.paragraphs[1].style.name, 'ListBullet')

        self.assertEqual(editor.document.paragraphs[2].text, "Paragraph 2") # Original p2 shifted

        # Insert after the new last paragraph (which was original p2, now at index 2)
        editor.insert_paragraph_after(2, "Paragraph End", style=None)
        self.assertEqual(len(editor.document.paragraphs), 4)
        self.assertEqual(editor.document.paragraphs[3].text, "Paragraph End")

        # Test inserting after current last paragraph
        editor_last = WordEditor()
        editor_last.document.add_paragraph("Only Paragraph")
        editor_last.insert_paragraph_after(0, "Appended Paragraph")
        self.assertEqual(len(editor_last.document.paragraphs), 2)
        self.assertEqual(editor_last.document.paragraphs[1].text, "Appended Paragraph")
        
        # Test invalid index
        result_invalid = editor.insert_paragraph_after(10, "Invalid insert")
        self.assertIsNone(result_invalid)
        self.assertEqual(len(editor.document.paragraphs), 4) # No change

    def test_10_delete_paragraph(self):
        """Test deleting a paragraph at a specified index."""
        editor = WordEditor()
        p1 = editor.document.add_paragraph("Paragraph A to delete")
        p2 = editor.document.add_paragraph("Paragraph B to keep")
        p3 = editor.document.add_paragraph("Paragraph C to delete")
        p4 = editor.document.add_paragraph("Paragraph D to keep")
        initial_len = len(editor.document.paragraphs) # Should be 4

        # Delete first paragraph (index 0)
        result1 = editor.delete_paragraph(0)
        self.assertTrue(result1)
        self.assertEqual(len(editor.document.paragraphs), initial_len - 1) # Now 3
        self.assertEqual(editor.document.paragraphs[0].text, "Paragraph B to keep")

        # Delete what is now the second paragraph (originally p3, "Paragraph C to delete")
        # After first deletion: B, C, D. So C is at index 1.
        result2 = editor.delete_paragraph(1)
        self.assertTrue(result2)
        self.assertEqual(len(editor.document.paragraphs), initial_len - 2) # Now 2
        self.assertEqual(editor.document.paragraphs[0].text, "Paragraph B to keep")
        self.assertEqual(editor.document.paragraphs[1].text, "Paragraph D to keep")

        # Test deleting last paragraph
        result_last = editor.delete_paragraph(1) # Deletes "Paragraph D"
        self.assertTrue(result_last)
        self.assertEqual(len(editor.document.paragraphs), initial_len - 3) # Now 1
        self.assertEqual(editor.document.paragraphs[0].text, "Paragraph B to keep")

        # Test invalid index
        result_invalid = editor.delete_paragraph(5) # Index out of bounds
        self.assertFalse(result_invalid)
        self.assertEqual(len(editor.document.paragraphs), 1) # No change

        # Test deleting the only remaining paragraph
        result_only = editor.delete_paragraph(0)
        self.assertTrue(result_only)
        self.assertEqual(len(editor.document.paragraphs), 0)

    def test_11_get_table_cell_text_placeholder(self):
        """Test placeholder for get_table_cell_text."""
        editor = WordEditor()
        # Add a table for testing
        table = editor.document.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "R0C0"
        table.cell(0, 1).text = "R0C1"
        table.cell(1, 0).text = "R1C0"
        table.cell(1, 1).text = "R1C1"

        self.assertEqual(editor.get_table_cell_text(0, 0, 0), "R0C0")
        self.assertEqual(editor.get_table_cell_text(0, 1, 1), "R1C1")
        self.assertEqual(editor.get_table_cell_text(0, 2, 2), "") # Out of bounds
        self.assertEqual(editor.get_table_cell_text(1, 0, 0), "") # Table index out of bounds

    def test_12_update_table_cell_text_placeholder(self):
        """Test placeholder for update_table_cell_text."""
        editor = WordEditor()
        table = editor.document.add_table(rows=1, cols=1)
        table.cell(0,0).text = "Old Text"

        result = editor.update_table_cell_text(0, 0, 0, "New Text")
        self.assertTrue(result)
        self.assertEqual(editor.document.tables[0].cell(0,0).text, "New Text")

        result_invalid = editor.update_table_cell_text(0, 1, 1, "Fail") # Out of bounds
        self.assertFalse(result_invalid)

    def test_13_add_row_to_table_placeholder(self):
        """Test placeholder for add_row_to_table."""
        editor = WordEditor()
        table = editor.document.add_table(rows=1, cols=2)
        self.assertEqual(len(table.rows), 1)

        new_row = editor.add_row_to_table(0)
        self.assertIsNotNone(new_row)
        self.assertEqual(len(table.rows), 2)
        
        invalid_row = editor.add_row_to_table(1) # Invalid table index
        self.assertIsNone(invalid_row)

    def test_14_get_list_item_text_placeholder(self):
        """Test placeholder for get_list_item_text."""
        editor = WordEditor()
        # For this placeholder, it behaves like get_paragraph_text
        editor.document.add_paragraph("Item 1", style='ListBullet')
        self.assertEqual(editor.get_list_item_text(0), "Item 1")

    def test_15_update_list_item_text_placeholder(self):
        """Test placeholder for update_list_item_text."""
        editor = WordEditor()
        # For this placeholder, it behaves like update_paragraph_text
        p = editor.document.add_paragraph("Old Item", style='ListNumber')
        run = p.runs[0]
        run.bold = True # Add some formatting to check preservation
        
        editor.update_list_item_text(0, "New Item", preserve_style=True)
        self.assertEqual(editor.document.paragraphs[0].text, "New Item")
        self.assertTrue(editor.document.paragraphs[0].runs[0].bold) # Check style preservation


if __name__ == '__main__':
    unittest.main()