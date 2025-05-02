import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from ..config import settings

class ConversationManager:
    """
    Manages conversation history storage and context for the RAG system.
    Stores chat turns in a SQLite database.
    """
    def __init__(self, db_path: str = settings.METADATA_DB_PATH):
        """
        Initializes the ConversationManager and ensures the database table exists.

        Args:
            db_path: The full path to the SQLite database file (reusing metadata DB).
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True) # Ensure directory exists
        self._create_table()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Establishes and returns a connection to the SQLite database.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # Access columns by name
        return conn

    def _create_table(self):
        """
        Creates the conversation_history table in the database if it doesn't exist.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_index INTEGER NOT NULL,
                    role TEXT NOT NULL, -- 'user' or 'assistant'
                    message TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON, -- Store any relevant metadata (e.g., document references)
                    UNIQUE (session_id, turn_index)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_state (
                    session_id TEXT PRIMARY KEY NOT NULL,
                    state JSON, -- Store conversation state as JSON
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES conversation_history (session_id) ON DELETE CASCADE
                )
            """)

            conn.commit()
        print(f"Ensured conversation_history and conversation_state tables exist in {self.db_path}")

    def add_message(self, session_id: str, role: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Adds a new message (user or assistant turn) to the conversation history.

        Args:
            session_id: A unique identifier for the conversation session.
            turn_index: The index of the turn within the session (e.g., 0 for first user message, 1 for first assistant response).
            role: The role of the message sender ('user' or 'assistant').
            message: The content of the message.
            metadata: Optional dictionary for storing additional message metadata.
        """
        if role not in ['user', 'assistant']:
            print(f"Warning: Invalid role '{role}'. Message not added.")
            return

        # Determine the next turn index for this session
        last_turn = self.get_last_turn_index(session_id)
        turn_index = last_turn + 1

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversation_history (session_id, turn_index, role, message, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, turn_index, role, message, json.dumps(metadata) if metadata else None))
                conn.commit()
            print(f"Added message to session '{session_id}' (Turn {turn_index}, Role: {role}).")
        except Exception as e:
            print(f"Error adding message to conversation history: {e}")

    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the conversation history for a given session, ordered by turn index.

        Args:
            session_id: The unique identifier for the conversation session.
            limit: Optional maximum number of turns to retrieve (from the most recent).

        Returns:
            A list of dictionaries, where each dictionary represents a message turn.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM conversation_history WHERE session_id = ? ORDER BY turn_index ASC"
                params = (session_id,)
                if limit is not None and limit > 0:
                    # To get the last 'limit' turns, we need to order by turn_index DESC and then reverse
                    query = "SELECT * FROM conversation_history WHERE session_id = ? ORDER BY turn_index DESC LIMIT ?"
                    params = (session_id, limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                history = [dict(row) for row in rows]

                if limit is not None and limit > 0:
                    history.reverse() # Reverse to get chronological order

                # Deserialize metadata
                for turn in history:
                    if turn.get("metadata"):
                        try:
                            turn["metadata"] = json.loads(turn["metadata"])
                        except (json.JSONDecodeError, TypeError):
                            turn["metadata"] = {} # Handle invalid JSON

                return history
        except Exception as e:
            print(f"Error retrieving conversation history for session '{session_id}': {e}")
            return []

    def get_last_turn_index(self, session_id: str) -> int:
        """
        Gets the index of the last turn for a given session.

        Args:
            session_id: The unique identifier for the conversation session.

        Returns:
            The index of the last turn, or -1 if no history exists for the session.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(turn_index) FROM conversation_history WHERE session_id = ?", (session_id,))
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else -1
        except Exception as e:
            print(f"Error getting last turn index for session '{session_id}': {e}")
            return -1

    def clear_conversation(self, session_id: str):
        """
        Clears the entire conversation history for a given session.

        Args:
            session_id: The unique identifier for the conversation session.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversation_history WHERE session_id = ?", (session_id,))
                conn.commit()
            print(f"Cleared conversation history for session '{session_id}'.")
        except Exception as e:
            print(f"Error clearing conversation history for session '{session_id}': {e}")

    def get_context_for_llm(self, session_id: str, max_tokens: int) -> str:
        """
        Retrieves recent conversation history and formats it as context for the LLM,
        respecting a maximum token limit.

        Args:
            session_id: The unique identifier for the conversation session.
            max_tokens: The maximum number of tokens for the context string.

        Returns:
            A formatted string containing recent conversation history.
        """
        history = self.get_conversation_history(session_id)
        context_string = ""
        current_tokens = 0
        # Iterate through history in reverse to add most recent messages first
        for turn in reversed(history):
            message_text = f"{turn['role'].capitalize()}: {turn['message']}\n"
            message_tokens = self._estimate_token_count(message_text)

            if current_tokens + message_tokens <= max_tokens:
                context_string = message_text + context_string # Prepend to maintain chronological order
                current_tokens += message_tokens
            else:
                # If adding the full message exceeds the limit, try adding a truncated version
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 0:
                    # Simple character-based truncation as a fallback
                    truncated_message = message_text[:remaining_tokens * 4] # Approx 4 chars per token
                    context_string = truncated_message + context_string
                    current_tokens = max_tokens # Assume we filled the context
                break # Stop adding messages

        return context_string.strip()

    def _estimate_token_count(self, text: str) -> int:
        """
        Estimates the token count of a given text using a simple word-based approximation.
        This is a placeholder and should be replaced with a proper tokenizer if possible.
        """
        return len(text.split()) # Simple word count approximation

    def save_state(self, session_id: str, state: Dict[str, Any]):
        """
        Saves the conversation state for a given session.
        If state exists, it is updated; otherwise, a new entry is created.

        Args:
            session_id: The unique identifier for the conversation session.
            state: A dictionary containing the state data to save.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                state_json = json.dumps(state)
                current_time = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO conversation_state (session_id, state, last_updated)
                    VALUES (?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        state = excluded.state,
                        last_updated = excluded.last_updated
                """, (session_id, state_json, current_time))
                conn.commit()
            print(f"Saved state for session '{session_id}'.")
        except Exception as e:
            print(f"Error saving state for session '{session_id}': {e}")

    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads the conversation state for a given session.

        Args:
            session_id: The unique identifier for the conversation session.

        Returns:
            A dictionary containing the state data, or None if no state is found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT state FROM conversation_state WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                if row and row['state']:
                    return json.loads(row['state'])
                return None
        except Exception as e:
            print(f"Error loading state for session '{session_id}': {e}")
            return None


# Example Usage
if __name__ == "__main__":
    print("Initializing ConversationManager...")
    # Use a temporary database for the example
    temp_db_path = os.path.join(settings.METADATA_DB_DIR, "temp_conversation_test.db")
    conv_manager = ConversationManager(db_path=temp_db_path)
    print("ConversationManager initialized.")

    session_id = "test_session_123"

    # Add some messages
    print(f"\nAdding messages to session '{session_id}'...")
    conv_manager.add_message(session_id, 'user', "Hello, what is the policy on remote work?")
    conv_manager.add_message(session_id, 'assistant', "The policy allows remote work up to 3 days a week.")
    conv_manager.add_message(session_id, 'user', "Can I roll over unused vacation days?")
    conv_manager.add_message(session_id, 'assistant', "Yes, unused vacation days can be rolled over, up to a maximum of 5 days.")

    # Retrieve conversation history
    print(f"\nRetrieving full conversation history for session '{session_id}'...")
    history = conv_manager.get_conversation_history(session_id)
    for turn in history:
        print(f"[{turn['timestamp']}] {turn['role'].capitalize()}: {turn['message']}")

    # Retrieve limited conversation history
    print(f"\nRetrieving last 2 turns for session '{session_id}'...")
    limited_history = conv_manager.get_conversation_history(session_id, limit=2)
    for turn in limited_history:
        print(f"[{turn['timestamp']}] {turn['role'].capitalize()}: {turn['message']}")

    # Get context for LLM (example max tokens)
    print(f"\nGetting context for LLM (max 50 tokens) for session '{session_id}'...")
    llm_context = conv_manager.get_context_for_llm(session_id, max_tokens=50)
    print("LLM Context:\n", llm_context)

    # --- State Management Example ---
    print(f"\nSaving state for session '{session_id}'...")
    initial_state = {"active_document": "policy.docx", "suggested_changes_count": 5}
    conv_manager.save_state(session_id, initial_state)

    print(f"\nLoading state for session '{session_id}'...")
    loaded_state = conv_manager.load_state(session_id)
    print("Loaded State:", loaded_state)
    assert loaded_state == initial_state

    print(f"\nUpdating and saving state for session '{session_id}'...")
    updated_state = {"active_document": "policy.docx", "suggested_changes_count": 3, "status": "review"}
    conv_manager.save_state(session_id, updated_state)

    print(f"\nLoading updated state for session '{session_id}'...")
    loaded_updated_state = conv_manager.load_state(session_id)
    print("Loaded Updated State:", loaded_updated_state)
    assert loaded_updated_state == updated_state

    print(f"\nLoading state for a non-existent session...")
    non_existent_state = conv_manager.load_state("non_existent_session")
    print("Non-existent State:", non_existent_state)
    assert non_existent_state is None
    # --- End State Management Example ---


    # Clear conversation history (should also cascade delete state due to FOREIGN KEY ON DELETE CASCADE)
    print(f"\nClearing conversation history for session '{session_id}'...")
    conv_manager.clear_conversation(session_id)

    # Verify history is cleared
    print(f"\nRetrieving history after clearing for session '{session_id}'...")
    cleared_history = conv_manager.get_conversation_history(session_id)
    print(f"History length: {len(cleared_history)}")

    # Verify state is also cleared
    print(f"\nRetrieving state after clearing history for session '{session_id}'...")
    cleared_state = conv_manager.load_state(session_id)
    print("Cleared State:", cleared_state)
    assert cleared_state is None


    # Clean up the temporary database file
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
        print(f"\nCleaned up temporary database file: {temp_db_path}")
    if os.path.exists(os.path.dirname(temp_db_path)):
         # Clean up the metadata directory if it's empty
         try:
             os.rmdir(os.path.dirname(temp_db_path))
         except OSError:
             # Directory not empty, ignore
             pass