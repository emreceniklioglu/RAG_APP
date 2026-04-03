# AI RAGapp — Mini RAG Backend

A production-minded MVP backend for querying internal company documents using Retrieval-Augmented Generation (RAG). Built as a technical case study for an AI Engineering role.

## Project Overview

Employees can upload Turkish PDF manuals and query them in natural language. The system ingests PDFs, chunks the text, generates embeddings, stores them in a vector database, and uses an LLM to generate grounded Turkish answers with source page references.

**Sample use case:** A technician asks "E01 hata kodu ne anlama gelir?" and gets an answer grounded in the Beko combi boiler manual, citing specific pages.

## Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                       │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐  │
│  │ /ingest  │ │ /query   │ │/health │ │  /docs  │  │
│  └────┬─────┘ └────┬─────┘ └────────┘ └─────────┘  │
│       │             │                                │
│  ┌────▼─────────────▼──────────────────────────────┐│
│  │              Service Layer                       ││
│  │  PDF → Chunking → Embedding → VectorStore → LLM ││
│  └──────────────────────────────────────────────────┘│
│       │                     │              │         │
│  ┌────▼────┐  ┌─────────────▼──┐  ┌────────▼──────┐ │
│  │ PyMuPDF │  │   ChromaDB     │  │ Google Gemini │ │
│  └─────────┘  └────────────────┘  └───────────────┘ │
│                     │                                │
│  ┌──────────────────▼──────────────────────────────┐ │
│  │          Jina v3 Embeddings API                 │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Layers:**
- **API Layer** — thin FastAPI routes, input validation, error handling
- **Service Layer** — all business logic (ingestion pipeline, RAG query orchestration)
- **Repository Layer** — document metadata persistence (JSON files)
- **External Services** — Jina (embeddings), Gemini (LLM), ChromaDB (vector store)

## Tech Stack

| Component | Technology | Reason |
|-----------|-----------|--------|
| Framework | FastAPI | Async, auto-docs, Pydantic integration |
| PDF Parsing | PyMuPDF | Fast, reliable, page-level extraction |
| Embeddings | Jina v3 API | Free tier, multilingual, 1024-dim |
| Vector Store | ChromaDB | Embedded, zero-config, persistent |
| LLM | Google Gemini | Free tier, good Turkish support |
| Validation | Pydantic v2 | Type-safe request/response schemas |

## Setup Instructions

### Prerequisites
- Python 3.11+
- API keys for Jina and Google Gemini

### Installation

```bash
# Clone the repository
cd RAGapp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Get API Keys

1. **Jina Embeddings**: Sign up at [jina.ai](https://jina.ai/) → Get API key
2. **Google Gemini**: Get key at [aistudio.google.com](https://aistudio.google.com/apikey)

## Run Instructions

```bash
# Start the server
python run.py

# Server runs at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Run Tests

```bash
pytest tests/ -v
```

## API Examples

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Ingest a PDF
```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@manual.pdf" \
  -F "department=maintenance"
```

### Query Documents
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "E01 hata kodu ne anlama gelir?",
    "user_role": "technician"
  }'
```

### List Documents
```bash
curl http://localhost:8000/api/documents
```

## Design Decisions

1. **Chunking Strategy**: ~400 tokens with 50-token overlap. Balances context richness with retrieval precision. Sentences are kept intact where possible.

2. **RBAC via Metadata Filtering**: Rather than separate collections, documents are tagged with a department at upload time. ChromaDB's `where` filter enforces access at query time. Simple, auditable, and extensible.

3. **Content-Based Deduplication**: Document IDs are SHA-256 hashes of filename + content. Re-uploading the same file is idempotent.

4. **JSON Metadata Store**: For an MVP, JSON files on disk avoid database complexity. Each document's metadata is a separate file, enabling simple CRUD without migrations.

5. **Turkish Prompting**: System prompt and user prompts are in Turkish to improve answer quality. The LLM is explicitly instructed to only use provided context and cite page numbers.

6. **Error Handling**: Consistent JSON error responses. No raw stack traces exposed. Specific error types (400, 422, 502) for different failure modes.

## RBAC Configuration

| Role | Accessible Departments |
|------|----------------------|
| `technician` | maintenance |
| `engineer` | engineering, maintenance |
| `hr_staff` | hr |

## Limitations

- **No authentication**: RBAC is simulated with hardcoded roles — no JWT/OAuth
- **No async embedding**: Jina API calls are synchronous (acceptable for MVP)
- **Simple chunking**: Token estimation via word count — not a proper tokenizer
- **No OCR**: Scanned/image-based PDFs will fail gracefully with a clear error
- **Single-user**: No concurrent ingestion safety (acceptable for case study)
- **No chunk deduplication**: Same text on different pages creates separate chunks

## Future Improvements

- JWT-based authentication with a real user database
- Async embedding calls with batching for large documents
- Proper tokenizer (tiktoken or sentencepiece) for accurate chunking
- OCR fallback (Tesseract) for scanned PDFs
- Hybrid search (keyword + semantic) for better retrieval
- Streaming LLM responses via SSE
- PostgreSQL + pgvector for production-grade storage
- Docker containerization and CI/CD pipeline
- Rate limiting and request throttling
- Monitoring dashboard with Prometheus/Grafana

