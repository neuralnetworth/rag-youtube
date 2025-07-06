# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

RAG-YouTube is a Python-based RAG (Retrieval-Augmented Generation) application that builds a knowledge base from YouTube channel videos. It downloads captions, processes them with embeddings, and provides a web interface for asking questions about the content.

## Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
```

### Data Preparation
```bash
# List videos from a YouTube channel (requires GOOGLE_API_KEY)
GOOGLE_API_KEY=XXXX ./src/list_videos.py VIDEO_ID

# Download captions for all videos
./src/download_captions.py

# Load documents into vector database
./src/document_loader.py
```

### Running the Application
```bash
# Start the web server
./src/app.py

# Development with auto-reload
make run
```

### Database Operations
```bash
# Create monitoring database
make createdb

# Reset document loading (clears vector database)
make load
```

### Testing and Benchmarking
```bash
# Run benchmarks comparing different configurations
make compare
```

## Architecture

### Core Components

- **Agent System**: Modular agent architecture with base classes and specialized implementations
  - `AgentBase`: Base functionality for all agents
  - `AgentQA`: Question-answering agent with retrieval capabilities
  - `AgentEval`: Evaluation and benchmarking agent

- **Chain System**: LangChain-based processing chains for different conversation types
  - `ChainBase`: Base chain functionality and parameter management
  - `chain_qa_base.py`: Basic Q&A chain
  - `chain_qa_sources.py`: Q&A with source citations
  - `chain_qa_conversation.py`: Conversational memory-enabled chain

- **Data Pipeline**: Video processing and knowledge base construction
  - `list_videos.py`: YouTube API integration for channel video discovery
  - `download_captions.py`: Caption/subtitle downloading via yt-dlp
  - `document_loader.py`: Vector database ingestion and chunking

### Web Interface

- **Backend**: Bottle.py web framework (`src/app.py`)
- **Frontend**: Vue.js components for configuration and visualization
- **Database**: SQLite for monitoring and ChromaDB for vector storage

### Configuration System

- Configuration via `rag-youtube.conf` file (copy from `rag-youtube.sample.conf`)
- Supports multiple LLM providers: Ollama (default), OpenAI
- Configurable embeddings: HuggingFace Sentence Transformers (default), OpenAI, Nomic, Ollama
- Adjustable retrieval parameters: chunk size, search type, document count, score thresholds

### Key Features

- **Multi-LLM Support**: Seamless switching between Ollama and OpenAI models
- **Flexible Retrieval**: Multiple search types (similarity, MMR, score threshold)
- **Chain Types**: Basic, sources-enabled, and conversational modes
- **Memory Management**: Buffer, windowed buffer, and summary memory types
- **Custom Prompts**: Editable prompts in `prompts/` directory
- **Evaluation**: Built-in benchmarking and comparison tools
- **Monitoring**: Dashboard for analyzing processing chains and performance

## Development Notes

### File Structure
- `src/`: Core Python modules
- `public/`: Web interface assets (HTML, CSS, JS)
- `prompts/`: Customizable LLM prompts
- `test/`: Benchmarking and evaluation scripts
- `captions/`: Downloaded video captions (created during setup)
- `db/`: Vector database storage (created during setup)

### Dependencies
- Python 3.x with LangChain ecosystem
- ChromaDB for vector storage
- Bottle.py for web framework
- yt-dlp for video caption downloading
- Optional: Ollama for local LLM inference

### Configuration
The system uses a hierarchical configuration approach where runtime parameters can override config file settings, enabling dynamic experimentation through the web interface.