import pytest
import os
import sqlite3
import json
from datetime import datetime

# Assuming ConversationManager is in src/rag/conversation.py
from src.rag.conversation import ConversationManager
from src.config import settings # To get the base metadata directory

# Define path for the temporary test database
TEST_METADATA_DIR = "tests/temp_conversation_test_data"
TEST_DB_PATH = os.path.join(TEST_METADATA_DIR, "test_conversation.db")

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_database():
    """
    Fixture to create and remove a temporary database for each test function.
    """
    os.makedirs(TEST_METADATA_DIR, exist_ok=True)
    # Ensure the database file does not exist before the test
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    yield # This is where the test function runs

    # Teardown: remove the database file and directory
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    if os.path.exists(TEST_METADATA_DIR) and not os.listdir(TEST_METADATA_DIR):
         os.rmdir(TEST_METADATA_DIR)


# --- Test ConversationManager ---

def test_conversation_manager_initialization():
    """Tests successful initialization and table creation."""
    manager = ConversationManager(db_path=TEST_DB_PATH)
    assert os.path.exists(TEST_DB_PATH)
    # Check if table was created
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    table_names = [table[0] for table in tables]
    assert "conversation_history" in table_names

def test_conversation_manager_add_message():
    """Tests adding messages to the history."""
    manager = ConversationManager(db_path=TEST_DB_PATH)
    session_id = "session_add_message"

    manager.add_message(session_id, 'user', "User message 1")
    manager.add_message(session_id, 'assistant', "Assistant message 1")
    manager.add_message(session_id, 'user', "User message 2", {"doc_ref": "doc1"})

    history = manager.get_conversation_history(session_id)
    assert len(history) == 3

    assert history[0]['session_id'] == session_id
    assert history[0]['turn_index'] == 0
    assert history[0]['role'] == 'user'
    assert history[0]['message'] == 'User message 1'
    assert history[0]['metadata'] is None # Stored as NULL if None

    assert history[1]['session_id'] == session_id
    assert history[1]['turn_index'] == 1
    assert history[1]['role'] == 'assistant'
    assert history[1]['message'] == 'Assistant message 1'
    assert history[1]['metadata'] is None

    assert history[2]['session_id'] == session_id
    assert history[2]['turn_index'] == 2
    assert history[2]['role'] == 'user'
    assert history[2]['message'] == 'User message 2'
    assert history[2]['metadata'] == {"doc_ref": "doc1"} # Check deserialized metadata

def test_conversation_manager_get_conversation_history():
    """Tests retrieving conversation history."""
    manager = ConversationManager(db_path=TEST_DB_PATH)
    session_id = "session_get_history"

    manager.add_message(session_id, 'user', "Msg 1")
    manager.add_message(session_id, 'assistant', "Msg 2")
    manager.add_message(session_id, 'user', "Msg 3")
    manager.add_message(session_id, 'assistant', "Msg 4")

    # Get full history
    full_history = manager.get_conversation_history(session_id)
    assert len(full_history) == 4
    assert full_history[0]['message'] == 'Msg 1'
    assert full_history[3]['message'] == 'Msg 4'

    # Get limited history
    limited_history = manager.get_conversation_history(session_id, limit=2)
    assert len(limited_history) == 2
    assert limited_history[0]['message'] == 'Msg 3' # Should be the last two messages in order
    assert limited_history[1]['message'] == 'Msg 4'

    # Get history for non-existent session
    non_existent_history = manager.get_conversation_history("non_existent_session")
    assert len(non_existent_history) == 0

def test_conversation_manager_get_last_turn_index():
    """Tests getting the last turn index."""
    manager = ConversationManager(db_path=TEST_DB_PATH)
    session_id = "session_last_turn"

    assert manager.get_last_turn_index(session_id) == -1 # No history yet

    manager.add_message(session_id, 'user', "Msg 1")
    assert manager.get_last_turn_index(session_id) == 0

    manager.add_message(session_id, 'assistant', "Msg 2")
    assert manager.get_last_turn_index(session_id) == 1

    manager.add_message(session_id, 'user', "Msg 3")
    assert manager.get_last_turn_index(session_id) == 2

def test_conversation_manager_clear_conversation():
    """Tests clearing conversation history."""
    manager = ConversationManager(db_path=TEST_DB_PATH)
    session_id = "session_clear"

    manager.add_message(session_id, 'user', "Msg 1")
    manager.add_message(session_id, 'assistant', "Msg 2")
    assert len(manager.get_conversation_history(session_id)) == 2

    manager.clear_conversation(session_id)
    assert len(manager.get_conversation_history(session_id)) == 0
    assert manager.get_last_turn_index(session_id) == -1 # Index should reset

def test_conversation_manager_get_context_for_llm():
    """Tests generating context for the LLM with token limit."""
    manager = ConversationManager(db_path=TEST_DB_PATH)
    session_id = "session_llm_context"

    # Add messages with varying lengths
    manager.add_message(session_id, 'user', "Short message.") # Approx 2 tokens
    manager.add_message(session_id, 'assistant', "A slightly longer response with more words.") # Approx 6 tokens
    manager.add_message(session_id, 'user', "This is a much longer message to test truncation and token limits.") # Approx 10 tokens
    manager.add_message(session_id, 'assistant', "Final short reply.") # Approx 3 tokens

    # Test with a large token limit (should include all messages)
    context_large = manager.get_context_for_llm(session_id, max_tokens=100)
    assert "User: Short message." in context_large
    assert "Assistant: A slightly longer response with more words." in context_large
    assert "User: This is a much longer message to test truncation and token limits." in context_large
    assert "Assistant: Final short reply." in context_large
    # Check order (should be chronological)
    assert context_large.index("User: Short message.") < context_large.index("Assistant: A slightly longer response with more words.")

    # Test with a smaller token limit (should truncate or exclude earlier messages)
    # Approximate token counts: 2, 6, 10, 3. Total ~21.
    # Let's set a limit of 15 tokens. Should get the last two messages and maybe part of the third.
    context_small = manager.get_context_for_llm(session_id, max_tokens=15)
    # Should definitely include the last message
    assert "Assistant: Final short reply." in context_small
    # Should include the third message, potentially truncated
    assert "User: This is a much longer message" in context_small
    # Should NOT include the first two messages
    assert "User: Short message." not in context_small
    assert "Assistant: A slightly longer response" not in context_small

    # Test with a very small token limit
    context_very_small = manager.get_context_for_llm(session_id, max_tokens=5)
    assert "Assistant: Final short reply." in context_very_small # Should at least get the last message
    assert "User: This is a much longer message" not in context_very_small # Should not get the third message

    # Test with zero token limit
    context_zero = manager.get_context_for_llm(session_id, max_tokens=0)
    assert context_zero == ""

    # Test with empty history
    manager.clear_conversation(session_id)
    context_empty = manager.get_context_for_llm(session_id, max_tokens=100)
    assert context_empty == ""

# Note: The _estimate_token_count is a simple approximation.
# For more accurate token counting, a proper tokenizer (like from transformers) would be needed.
# This test relies on the simple word split, which is sufficient for basic functionality testing.

def test_conversation_manager_save_and_load_state():
    """Tests saving and loading conversation state."""
    manager = ConversationManager(db_path=TEST_DB_PATH)
    session_id = "session_state"
    initial_state = {"active_document": "report.pdf", "status": "draft"}

    # Save initial state
    manager.save_state(session_id, initial_state)

    # Load state and verify
    loaded_state = manager.load_state(session_id)
    assert loaded_state == initial_state

    # Update and save state
    updated_state = {"active_document": "report.pdf", "status": "final", "reviewers": ["user1", "user2"]}
    manager.save_state(session_id, updated_state)

    # Load updated state and verify
    loaded_updated_state = manager.load_state(session_id)
    assert loaded_updated_state == updated_state

    # Test loading state for a non-existent session
    non_existent_state = manager.load_state("non_existent_session_state")
    assert non_existent_state is None

def test_conversation_manager_clear_conversation_clears_state():
    """Tests that clearing conversation history also clears the state due to cascade delete."""
    manager = ConversationManager(db_path=TEST_DB_PATH)
    session_id = "session_clear_state"

    # Add a message and save state
    manager.add_message(session_id, 'user', "Message to clear.")
    manager.save_state(session_id, {"some_state": True})

    # Verify history and state exist
    assert len(manager.get_conversation_history(session_id)) > 0
    assert manager.load_state(session_id) is not None

    # Clear conversation
    manager.clear_conversation(session_id)

    # Verify history and state are cleared
    assert len(manager.get_conversation_history(session_id)) == 0
    assert manager.load_state(session_id) is None