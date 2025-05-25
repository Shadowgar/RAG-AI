# src/app.py
import streamlit as st
import os # Needed for file operations if handling uploads directly
from typing import Dict, Any

# Define initial session state
def init_session_state():
    """Initializes the Streamlit session state variables."""
    if 'document_metadata' not in st.session_state:
        st.session_state['document_metadata'] = {} # Stores metadata for uploaded documents {doc_id: metadata}
    if 'vector_store' not in st.session_state:
        st.session_state['vector_store'] = None # Stores the FAISS index
    if 'metadata_db' not in st.session_state:
        st.session_state['metadata_db'] = None # Stores the SQLite connection/object
    if 'conversation_history' not in st.session_state:
        st.session_state['conversation_history'] = [] # Stores chat messages
    if 'current_workflow' not in st.session_state:
        st.session_state['current_workflow'] = None # Stores the active ChangeWorkflow
    if 'word_editor' not in st.session_state:
        st.session_state['word_editor'] = None # Stores the WordEditor instance for the current document
    if 'current_document_id' not in st.session_state:
        st.session_state['current_document_id'] = None # ID of the document currently being worked on

def main():
    """
    Main function for the Streamlit SOP RAG Update System application.
    """
    st.set_page_config(page_title="SOP RAG Update System", layout="wide")

    st.title("SOP RAG Update System")

    # Initialize session state
    init_session_state()

    # --- Navigation ---
    # In a more complex app, this could be a sidebar or tabs
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Document Management", "Conversation", "Settings"])

    # Create a split-screen layout
    col1, col2 = st.columns(2)

    with col1:
        # --- Document Viewer/Editor Area ---
        st.header("Document Viewer")
        if st.session_state.get('current_document_id'):
            st.write(f"Viewing: {st.session_state['current_document_id']}")
            # TODO: Implement document content display here
            st.info("Document content will be displayed here.")
            # TODO: Add inline acceptance/rejection controls and suggestion highlighting

            # Placeholder for section navigation
            st.subheader("Section Navigation")
            if st.session_state.get('current_document_id'):
                # TODO: Extract sections from the document and display as links
                st.write("Section links will appear here.")
            else:
                st.write("Select a document to enable section navigation.")

            # Placeholder for suggested changes and accept/reject controls
            if st.session_state.get('current_workflow') and st.session_state['current_workflow'].get_proposed_changes():
                st.subheader("Suggested Changes")
                st.write("Review the suggested changes below:")

            # Placeholder for suggested changes and accept/reject controls
            if st.session_state.get('current_workflow') and st.session_state['current_workflow'].get_proposed_changes():
                st.subheader("Suggested Changes")
                st.write("Review the suggested changes below:")

                for change in st.session_state['current_workflow'].get_proposed_changes():
                    st.write(f"- **Change Type:** {change.change_type.value}")
                    st.write(f"  **Location:** {change.location}")
                    st.write(f"  **Description:** {change.description}")
                    st.write(f"  **Proposed Change:** {change.new_value}") # Simplified display

                    # Add accept/reject buttons for each change
                    col_accept, col_reject = st.columns(2)
                    with col_accept:
                        # TODO: Implement logic to accept the change
                        if st.button(f"Accept Change {change.change_id[:4]}...", key=f"accept_{change.change_id}"):
                            st.info(f"Accepted change {change.change_id[:4]}... (Logic not implemented)")
                            # Update change status in workflow (requires workflow object to be mutable or re-assigned)
                            # st.session_state['current_workflow'].update_change_status(change.change_id, ChangeStatus.ACCEPTED)
                            # st.experimental_rerun() # Rerun to update display

                    with col_reject:
                        # TODO: Implement logic to reject the change
                        if st.button(f"Reject Change {change.change_id[:4]}...", key=f"reject_{change.change_id}"):
                            st.info(f"Rejected change {change.change_id[:4]}... (Logic not implemented)")
                            # Update change status in workflow
                            # st.session_state['current_workflow'].update_change_status(change.change_id, ChangeStatus.REJECTED)
                            # st.experimental_rerun() # Rerun to update display

                    st.markdown("---") # Separator between changes

                # Button to apply all accepted changes (placeholder)
                if st.button("Apply Accepted Changes", key="apply_all_changes"):
                    st.info("Applying accepted changes... (Logic not implemented)")
                    # TODO: Implement logic to apply accepted changes using WorkflowApplier
                    # applier = WorkflowApplier(st.session_state['word_editor'])
                    # applier.apply_workflow(st.session_state['current_workflow'])
                    # st.experimental_rerun() # Rerun to update display and potentially show edited document

            elif st.session_state.get('current_workflow') and not st.session_state['current_workflow'].get_proposed_changes():
                 st.info("No proposed changes for this document yet.")

        else:
            st.info("Select or upload a document to view its content.")


    with col2:
        # --- Right Panel (Content changes based on navigation) ---
        if page == "Document Management":
            st.header("Document Management")
            st.write("Upload and manage your SOP documents here.")

        st.subheader("Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=["docx", "pdf", "pptx"],
            help="Upload a Word (.docx), PDF (.pdf), or PowerPoint (.pptx) document."
        )

        if uploaded_file is not None:
            # Display file details
            st.write("File uploaded successfully!")
            st.write(f"File name: {uploaded_file.name}")
            st.write(f"File type: {uploaded_file.type}")
            st.write(f"File size: {uploaded_file.size} bytes")

            # TODO: Add logic here to process the uploaded file:
            # 1. Save the file to the document directory.
            # 2. Use the appropriate document processor to parse the file.
            # 3. Generate embeddings for the document chunks.
            # 4. Add the document and its embeddings to the vector store.
            # 5. Store document metadata in the SQLite database.
            # 6. Update session state with the new document information.

            st.info("Document processing and indexing will be implemented here.")


        elif page == "Conversation":
            st.header("Conversation")
            st.write("Discuss document updates with the AI here.")

        # Chat message display area
        chat_container = st.container()

        # Display chat messages from history
        with chat_container:
            for message in st.session_state.get('conversation_history', []):
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # Chat input field
        if st.session_state.get('current_document_id'):
            user_input = st.chat_input("Ask a question or suggest a change...")
            if user_input:
                # Add user message to conversation history
                st.session_state['conversation_history'].append({"role": "user", "content": user_input})

                # Display user message immediately
                with chat_container:
                    with st.chat_message("user"):
                        st.write(user_input)

                # Add typing indicator/loading state for AI response
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            # TODO: Implement RAG to retrieve relevant document chunks
                            # For now, add a placeholder for retrieved context
                            retrieved_context = "Placeholder: Retrieved document context based on your query."
                            st.info(f"Retrieved Context: {retrieved_context}") # Display retrieved context (optional)

                            # TODO: Implement LLM call with query, context, and history
                            # For now, add a placeholder AI response after a short delay
                            import time
                            time.sleep(2) # Simulate processing time
                            ai_response = f"You asked: '{user_input}'. (AI response based on RAG and LLM will appear here.)"
                            st.write(ai_response) # Display the placeholder response

                # Add AI response to conversation history
                st.session_state['conversation_history'].append({"role": "assistant", "content": ai_response})

                # Streamlit automatically re-runs the script when session state changes or input is submitted,
                # which will update the chat display. No explicit rerun needed.

        else: # This else belongs to 'if st.session_state.get('current_document_id'):'
            st.info("Please select or upload a document in the Document Management tab to start a conversation.")


        elif page == "Settings":
            st.header("Settings")
            st.write("Configure system settings and API keys here.")

        st.subheader("API Configuration")
        gemini_api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API key.")
        # TODO: Add logic to save/load API key securely (e.g., using Streamlit secrets or a config file)

        st.subheader("Data Storage Paths")
        document_dir = st.text_input("Document Directory", value="./data/documents", help="Path to the directory for storing original documents.")
        vector_db_dir = st.text_input("Vector Database Directory", value="./data/vector_db", help="Path to the directory for storing the vector database.")
        metadata_db_path = st.text_input("Metadata Database Path", value="./data/metadata/metadata.db", help="Path to the SQLite metadata database file.")
        # TODO: Add logic to save/load these paths

        st.subheader("Model Configuration")
        # Placeholder for model selection or parameters if needed later
        st.write("Model settings will be added here.")

        # Button to save settings (placeholder)
        if st.button("Save Settings"):
            # TODO: Implement saving settings to a config file or other persistent storage
            st.success("Settings saved (placeholder).")

        st.subheader("Uploaded Documents")
        if st.session_state.get('document_metadata'): # Use .get for safer access
            st.write("Select a document to work with:")
            # Create a list of document names/IDs for the radio button
            doc_options = list(st.session_state['document_metadata'].keys())
            
            # Ensure a document is selected if there are documents
            if doc_options:
                 # Set a default selected document if none is currently selected
                if st.session_state['current_document_id'] is None or st.session_state['current_document_id'] not in doc_options:
                     st.session_state['current_document_id'] = doc_options[0] # Select the first document by default

                selected_doc_id = st.radio("Documents", doc_options, index=doc_options.index(st.session_state['current_document_id']))

                # Update current_document_id in session state when a document is selected
                if selected_doc_id != st.session_state['current_document_id']:
                    st.session_state['current_document_id'] = selected_doc_id
                    st.info(f"Selected document: {selected_doc_id}")
                    # TODO: Load the selected document into the WordEditor and potentially the conversation history
                    st.session_state['word_editor'] = None # Placeholder: Replace with actual loading
                    st.session_state['current_workflow'] = None # Reset workflow for new document
                    st.session_state['conversation_history'] = [] # Reset conversation history
    
                # Display metadata for the selected document
                if st.session_state['current_document_id']:
                    st.subheader("Document Metadata")
                    metadata = st.session_state['document_metadata'].get(st.session_state['current_document_id'])
                    if metadata:
                        st.json(metadata) # Display metadata as JSON for now
                        # TODO: Add a more user-friendly metadata editor interface
                    else:
                        st.write("Metadata not found for this document.")
            else:
                 st.write("No documents uploaded yet.")
                 st.session_state['current_document_id'] = None # No documents, no current document

        else:
            st.write("No documents uploaded yet.")
            st.session_state['current_document_id'] = None # No documents, no current document


        st.subheader("Document Search")
        search_query = st.text_input("Enter search query", help="Search within the uploaded documents.")

        if search_query:
            # TODO: Implement document search using the RAG retrieval system
            st.info(f"Searching for: '{search_query}' (Search functionality not yet implemented)")
            # Placeholder for displaying search results
            st.write("Search results will appear here.")

        st.subheader("Export Document")
        if st.session_state['current_document_id']:
            st.write(f"Export options for: {st.session_state['current_document_id']}")
            col1, col2 = st.columns(2)
            with col1:
                # TODO: Implement export of original document
                st.button("Export Original Document", help="Download the original uploaded document.")
            with col2:
                # TODO: Implement export of edited document (applying workflow changes)
                st.button("Export Edited Document", help="Download the document with accepted changes applied.")
        else:
            st.write("Select a document to enable export options.")

        st.subheader("Document Comparison")
        if st.session_state['current_document_id']:
            # TODO: Implement logic to compare original and edited documents
            if st.button("Compare Documents", help="Compare the original and edited versions of the document."):
                 st.info("Document comparison functionality not yet implemented.")
                 # Placeholder for displaying comparison results
                 st.write("Comparison results will appear here.")
        else:
            st.write("Select a document to enable comparison.")


if __name__ == "__main__":
    main()