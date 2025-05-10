# SOP RAG Update System - Project Plan
## Overview
This project aims to create a locally-run system that uses RAG (Retrieval-Augmented Generation) to help update Standard Operating Procedures (SOPs) by analyzing company documents. The system will provide a conversational interface to discuss document updates, with the AI offering suggestions that can be accepted or rejected.
## Hardware Constraints

RTX 3060 with 6GB VRAM (15GB shared VRAM)
32GB RAM
Must run locally on a laptop
No budget for paid services

## Core Technologies
### Base Technologies

Language Model: Google Gemini (using free API keys)
Vector Database: FAISS (open-source, runs locally)
Embedding Model: Sentence-Transformers (runs on GPU)
Document Processing: Unstructured-IO (open-source version)
Framework: LlamaIndex or LangChain
IDE: Visual Studio Code with Roocode
Version Control: Git

### VSCode Extensions

Roocode: Main assistant for working in the codebase
Python: For Python language support
Jupyter: For exploratory data analysis
GitLens: For enhanced Git functionality
Error Lens: For inline error highlighting
Auto-GPT: For AI-augmented coding (if available)
Material Icon Theme: For better file visualization
Path Intellisense: For path autocompletion
GitHub Copilot: If available/accessible

### MCP Servers

GitHub: For version control and code storage
Filesystem: For local data access
Brave Search: For web searches when needed
Local Terminal: For system commands

## System Architecture
### 1. Document Ingestion Layer

Document parsers for multiple formats (Word, PDF, PowerPoint)
Structure preservation and metadata extraction
Local storage with indexing

### 2. Knowledge Base Layer

Local vector storage using Chroma DB or FAISS
Metadata database using SQLite
Efficient document chunking strategy

### 3. Retrieval Layer

Hybrid search combining BM25 and vector similarity
Caching for frequent queries
Progressive loading of context

### 4. Conversation Layer

Chat history storage in SQLite
Context management optimized for Gemini API
Memory system for consistent conversation

### 5. Document Editing Layer

Word document manipulation utilities
Change tracking system
Template preservation mechanics

## User Interface
A Streamlit application that provides:

Document upload and viewing
Chat interface for discussing changes
Document comparison view
Accept/reject workflow for changes
System settings and configuration

## Implementation Phases
### Phase 1: Document Processing & Storage

Set up project environment and dependencies
Create document processors for Word, PDF, PowerPoint
Implement embedding pipeline using Sentence-Transformers
Build local vector store with Chroma DB
Create metadata database with SQLite

### Phase 2: RAG & Conversation System

Implement retrieval system with local vector DB
Set up Gemini API integration
Create conversation management system
Develop memory mechanism
Build prompt engineering templates

### Phase 3: Document Editing

Create Word document manipulation utilities
Implement change tracking system
Build accept/reject workflow
Develop template preservation mechanism

### Phase 4: User Interface

Build Streamlit app for user interaction
Create document upload/view interface
Implement chat interface
Develop document comparison view
Add system settings and configuration

## Technology Details
### Document Processing

pypdf: Process PDF documents
python-docx: Process Word documents
python-pptx: Process PowerPoint documents
unstructured-io: Enhanced document parsing

### Embedding & Vector Search

Sentence-Transformers: all-MiniLM-L6-v2 (80MB model size)
FAISS: Facebook AI Similarity Search for vector storage

### Backend

SQLite: Lightweight database for metadata
LlamaIndex: For RAG implementation
Pydantic: For data validation

### Frontend

Streamlit: UI framework
Plotly: For visualizations if needed
streamlit-chat: Chat UI components

## Resource Optimization
### Embedding Optimization

Use smaller embedding models (MiniLM instead of larger models)
Implement batched embedding processing
Cache embeddings to avoid reprocessing

### Memory Management

Implement document chunking to process large files
Use streaming responses from Gemini API
Clean up RAM between operations

### API Usage Optimization

Compress and optimize prompts for Gemini
Implement caching for common queries
Use efficient retrieval to minimize API calls

## Project Setup
# Create project directory
mkdir sop-assistant
cd sop-assistant

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install core dependencies
pip install sentence-transformers faiss-cpu pymupdf python-docx python-pptx
pip install streamlit chromadb llama-index google-generativeai pydantic

# Create project structure
mkdir -p data/documents data/vector_db src/processors src/rag src/ui

# Create main application file
touch src/app.py

# Create Gemini API key file (you'll need to add your key)
touch .env

## Project Structure
sop-assistant/
├── data/
│   ├── documents/     # Store original documents
│   ├── vector_db/     # Vector database storage
│   └── metadata/      # SQLite database
├── src/
│   ├── processors/    # Document processing modules
│   │   ├── __init__.py
│   │   ├── docx_processor.py
│   │   ├── pdf_processor.py
│   │   └── pptx_processor.py
│   ├── rag/           # RAG implementation
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   ├── llm/           # LLM integration
│   │   ├── __init__.py
│   │   ├── gemini.py
│   │   └── prompts.py
│   ├── ui/            # Streamlit UI components
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── document_view.py
│   │   └── settings.py
│   ├── utils/         # Utility functions
│   │   ├── __init__.py
│   │   ├── document_utils.py
│   │   └── memory.py
│   └── app.py         # Main application
├── tests/             # Unit tests
├── .env               # Environment variables
├── README.md          # Project documentation
└── requirements.txt   # Project dependencies

## System Requirements & Limitations

RTX 3060 with 6GB VRAM is sufficient for running the embedding models
32GB RAM allows for processing moderate document collections
Expect to handle ~1000 pages before performance degrades
Internet connection required for Gemini API
Gemini API may have context limitations affecting conversation depth

## Next Steps

Set up the development environment with all necessary extensions
Create a detailed implementation plan for each component
Develop proof-of-concept for document processing and embedding
Test RAG capabilities with a small document set
Implement conversation system and basic UI
Add document editing capabilities
Complete the UI and perform system testing

## Research Notes

### `python-docx` Formatting Preservation (2025-05-10)

**Objective:** Understand `python-docx` capabilities for preserving text formatting (bold, italic, font, styles, etc.) when reading, editing, and writing Word (.docx) documents. This is crucial for the "Document Editing Layer" of the SOP RAG Update System.

**Core Concepts:**
*   **Document Hierarchy:** `python-docx` models Word documents with a hierarchy:
    *   `Document`: The top-level object representing the entire file.
    *   `Paragraph`: A block of text, typically ending with a newline.
    *   `Run`: A contiguous sequence of characters within a paragraph that shares the same character-level formatting. A single paragraph can contain multiple runs (e.g., "This is **bold** and *italic*." would involve at least three runs).
*   **Formatting Application:**
    *   **Run-Level Formatting:** Most direct character formatting (bold, italic, underline, font name, font size, font color) is applied to `Run` objects. Examples: `run.bold = True`, `run.italic = True`, `run.font.name = 'Calibri'`, `run.font.size = Pt(12)`.
    *   **Paragraph-Level Formatting:** Alignment, indentation, spacing, and paragraph styles are applied to `Paragraph` objects. Example: `paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER`.
    *   **Styles:** Word documents use styles (e.g., "Normal", "Heading 1", "List Paragraph") to define sets of formatting attributes. `python-docx` can read and apply both paragraph styles (`paragraph.style`) and character styles (`run.style`). Explicit run formatting overrides character styles, which in turn override paragraph styles.

**Capabilities & Limitations for Preservation:**

1.  **Reading Formatting:**
    *   `python-docx` can reliably read most common formatting attributes from runs (e.g., `run.bold`, `run.italic`, `run.font.name`, `run.font.size`, `run.font.color.rgb`) and paragraphs (e.g., `paragraph.alignment`, `paragraph.style`).
    *   It can identify the names of applied styles.

2.  **Applying Formatting:**
    *   New or existing runs and paragraphs can have their formatting attributes set explicitly.
    *   Predefined or custom document styles can be applied.

3.  **Preserving Formatting During Edits:**
    *   **Simple Text Replacement within a Single Run:** If you modify `run.text` directly (e.g., `run.text = new_text`), the existing formatting of that *specific run* is generally preserved. This is the most straightforward scenario.
    *   **Replacing Text Spanning Multiple Runs or Paragraphs:** This is significantly more complex. `python-docx` does not have a high-level "find and replace with formatting" function that spans across run boundaries intelligently.
        *   If you delete an old run and add a new one, all formatting from the old run must be explicitly copied to the new run.
        *   If a replacement operation needs to split an existing run or merge parts of different runs, new `Run` objects must be created, and their formatting must be meticulously managed by copying attributes from the original run(s).
    *   **Inserting New Content:** When inserting new paragraphs or runs, their formatting must be set explicitly or by applying a style. They do not automatically inherit all nuanced formatting from surrounding content unless explicitly coded.
    *   **Copying/Moving Content:** There isn't a direct "copy_paragraph_with_formatting" or "move_run_with_formatting" method. To achieve this, one must:
        1.  Iterate through the source paragraph(s)/run(s).
        2.  Create new paragraph(s)/run(s) at the target location.
        3.  For each new element, copy all relevant text and formatting attributes (bold, italic, font properties, style name, paragraph properties, etc.) from the corresponding source element. This can be verbose.

4.  **Working with Complex Elements:**
    *   **Tables:** Tables, rows, and cells are distinct objects. Text within cells is managed via paragraphs and runs, following the same formatting principles. Table-level formatting (borders, shading) can also be manipulated.
    *   **Lists:** List formatting (bullets, numbering) is primarily controlled by paragraph styles.
    *   **Headers/Footers:** Accessible and editable, containing paragraphs and runs.
    *   **Images/Shapes:** Basic image insertion is supported. Complex manipulation or preservation of existing embedded objects can be limited.

5.  **Unsupported Features:**
    *   `python-docx` does not support every feature available in Microsoft Word. Advanced layout features, some complex drawing objects (SmartArt, Charts beyond basic image representation), macros, and certain XML-level constructs might not be fully understood or preserved.
    *   Editing a document with `python-docx` and re-saving it can sometimes lead to the loss or alteration of features the library doesn't handle.

**Strategies for Maximizing Formatting Preservation:**

*   **Granular Operations:** Perform changes at the most granular level possible (i.e., within runs if feasible).
*   **Read-Modify-Write Attributes:** When changing a run, read its existing formatting, make text changes, then ensure the formatting attributes are still correctly set or reapply them.
*   **Style-Based Formatting:** Rely on applying predefined document styles as much as possible, as this is generally more robust than direct run-level formatting for consistency.
*   **Careful Iteration:** For complex replacements or insertions, iterate carefully through paragraphs and runs. Be prepared to split runs or create new ones, ensuring formatting is copied.
*   **Consider `docxtpl` for Generation, `python-docx` for Fine-grained Edits:** `docxtpl` is excellent for generating documents from templates with initial formatting. For subsequent, precise edits while preserving existing, potentially arbitrary formatting, `python-docx`'s direct manipulation of the document structure is necessary.
*   **Testing:** Thoroughly test editing operations on diverse documents to identify formatting loss scenarios.

**Implications for the SOP Project:**
*   Simple text corrections suggested by the LLM, if they fall within a single run, should be relatively easy to apply while preserving formatting.
*   Suggestions involving adding/deleting entire sentences or paragraphs, or rephrasing text that spans multiple formatting types, will require careful implementation to clone/reapply formatting from the original or surrounding text.
*   The system should aim to preserve common formatting attributes like bold, italic, underline, font properties, basic paragraph alignment, and list structures. Perfect preservation of highly complex or obscure Word formatting might be out of scope for initial versions due to the complexity involved.
*   A "document comparison" utility will be essential to highlight what `python-docx` *thinks* it has changed versus the original, helping to identify unintended formatting loss.