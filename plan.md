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