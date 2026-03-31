# arXiv Assistant Components Overview

This document describes the primary architectural components of the arXiv Assistant system.

## 1. Backend Core Services

### **Production Worker (`production_worker.py`)**
The "heart" of the background processing. It continuously monitors the database for papers that need attention.
*   **PDF Extraction**: Downloads PDFs from arXiv and extracts the Abstract and Introduction sections using a lightweight PDF processor.
*   **Live Embeddings**: Generates 768-dimensional embeddings for *recent* papers (published within the last 7 days) to ensure immediate searchability.
*   **Summarization**: Triggers LLM-based summarization for new papers.

### **Batch Embed Manager (`batch_embed_manager.py`)**
A high-throughput service designed to handle the massive backlog of historical papers.
*   **Bulk Preparation**: Groups papers into large JSONL batches (up to 20k-50k items).
*   **Async Batch API**: Interfaces with the Gemini Async Batch Embedding API to generate embeddings at scale without hitting live rate limits.
*   **Ingestion**: Monitors API job status and bulk-updates the database with the results.

### **Scheduler (`scheduler.py`)**
Orchestrates periodic tasks using `APScheduler`.
*   **Daily Crawl**: Automatically fetches the latest papers from arXiv every morning.
*   **Maintenance**: Triggers data integrity checks and cleanup scripts.

### **Backend API (`main.py` & Routers)**
A FastAPI-based web server that provides endpoints for the frontend.
*   **Search**: Handles semantic (vector) and keyword search results.
*   **Library Management**: Manages user bookmarks, paper status, and research deep-dives.

### **Database (PostgreSQL + pgvector)**
The persistent storage layer.
*   **Metadata**: Stores all paper details (authors, links, categories).
*   **Vector Store**: Uses `pgvector` for efficient similarity searching against paper embeddings.

## 2. Shared Services (`services/`)

*   **`arxiv_service.py`**: Handles all communication with the arXiv XML API.
*   **`llm_service.py`**: A unified interface for LLM interactions, supporting both Google Gemini and local Ollama instances.
*   **`summarization_service.py`**: Specialized logic for condensing long research papers into actionable summaries.

## 3. Frontend Application

*   **Next.js UI**: A modern, responsive web dashboard for researchers to browse daily digests, perform semantic searches, and interact with papers.
*   **RAG Interface**: Integrates with the backend to allow natural language "chatting" with research paper content.

## 4. Infrastructure

*   **Docker Compose**: The entire stack is containerized for consistent deployment across local development and the **Khadas Edge 2** production device.
*   **External Storage**: Large PDF files and database data are stored on high-capacity external drives to maintain device performance.
