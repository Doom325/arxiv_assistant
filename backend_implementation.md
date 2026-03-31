# Backend Implementation Summary

This document outlines the technical implementation of the arXiv AI Assistant backend.

## 1. Technology Stack

*   **Framework**: FastAPI (Python 3.10+)
*   **Database**: PostgreSQL with `pgvector` extension
*   **ORM**: SQLAlchemy
*   **AI/LLM**: 
    *   **Cloud**: Google Gemini Pro (via `google-generativeai`)
    *   **Local**: Ollama (Llama 3, Nomic Embed Text)
*   **Scheduler**: APScheduler
*   **PDF Processing**: `pypdf`
*   **API Client**: `arxiv` (Python wrapper)
*   **Email**: `smtplib` with Jinja2 templates

## 2. Architecture Overview

The backend follows a service-oriented architecture within a modular monolith structure.

*   **Routers**: Handle HTTP requests and define API endpoints.
*   **Services**: Encapsulate business logic and external API interactions (arXiv, LLM, Email).
*   **Models**: Define database schema and relationships.
*   **Schemas**: Pydantic models for request/response validation.
*   **Scheduler**: Manages background tasks (daily ingestion).
*   **Ingestion**: Reusable logic for processing papers.

## 3. Database Schema

### `papers` Table
Stores metadata and vector embeddings for research papers.
*   `id`: Primary Key
*   `arxiv_id`: Unique arXiv identifier (e.g., "1706.03762")
*   `title`: Paper title
*   `authors`: List of authors (JSON)
*   `summary`: AI-generated summary
*   `published_date`: Date of publication
*   `category`: Primary arXiv category (e.g., "cs.AI")
*   `pdf_url`: Link to the PDF
*   `embedding`: Vector (768 dim for Gemini / Nomic)

### `user_configs` Table
Stores user preferences for personalization.
*   `id`: Primary Key
*   `email`: User email (Unique)
*   `keywords`: List of interest keywords (JSON)
*   `categories`: List of subscribed categories (JSON)
*   `schedule_time`: Preferred time for daily digest (default "06:00")

## 4. API Endpoints

### Papers (`/papers`)
*   `GET /`: List recent papers with pagination. Returns `List[PaperResponse]`.
*   `POST /search`: Semantic search using vector similarity (L2 distance).
*   `POST /chat`: RAG-based chat interface. Retrieves relevant papers and uses LLM to answer user questions.

### Users (`/users`)
*   `GET /config/{email}`: Retrieve user configuration.
*   `POST /config`: Update user configuration (keywords, categories).

### Static Files
*   `/pdfs/{arxiv_id}.pdf`: Serves locally saved PDFs.

## 5. Core Services

### LLMService (`services/llm_service.py`)
Abstracts the AI provider.
*   **GeminiProvider**: Uses `gemini-1.5-pro-latest` and `text-embedding-004`.
*   **OllamaProvider**: Uses local `llama3` and `nomic-embed-text`.
*   **Factory**: `get_llm_service()` instantiates the correct provider based on `AI_PROVIDER` env var.

### ArxivService (`services/arxiv_service.py`)
*   **Fetching**: Queries arXiv API for papers.
*   **Rate Limiting**: Enforces a 3-second delay.
*   **PDF Handling**: Downloads PDFs to `data/pdfs` and extracts text.

### EmailService (`services/email_service.py`)
*   **SMTP**: Sends emails using configured SMTP server (e.g., Gmail).
*   **Templates**: Uses Jinja2 to generate HTML daily digests.

## 6. Ingestion & Background Tasks

### Ingestion Module (`ingestion.py`)
*   Reusable function `process_paper_entry` that handles:
    1.  PDF Download & Text Extraction.
    2.  Summarization & Embedding (via `LLMService`).
    3.  Database Persistence.

### Scheduler (`scheduler.py`)
*   Runs daily at 6:00 AM.
*   Fetches new papers for user-subscribed categories.
*   Processes papers using `ingestion.py`.
*   Sends email digests via `EmailService`.

### Batch Ingestion (`batch_ingest.py`)
*   CLI script for backfilling papers.
*   Usage: `python3 batch_ingest.py --days 7` or `--years 1`.

## 7. Configuration
Environment variables are managed via `.env` and `config.py`:
*   `DATABASE_URL`: Connection string for PostgreSQL.
*   `AI_PROVIDER`: `local` or `gemini`.
*   `OLLAMA_BASE_URL`: URL for local Ollama instance.
*   `EMAIL_SENDER` / `EMAIL_PASSWORD`: SMTP credentials.
