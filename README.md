# Cybersecurity Threat Intelligence Assistant (Production RAG)

A production-grade **Retrieval-Augmented Generation (RAG)** platform for answering cybersecurity threat intelligence queries using trusted security sources such as CVE reports, security advisories, and technical documentation.

The system continuously ingests cybersecurity documents, builds a searchable knowledge base using semantic embeddings, retrieves the most relevant context for user queries, and generates grounded responses using Large Language Models (LLMs).

---

## Features

- Automated ingestion of cybersecurity threat intelligence sources
- Semantic search using vector embeddings
- Hybrid retrieval (Dense + BM25)
- Cross-encoder reranking
- Source-grounded responses with citations
- Continuous document ingestion and indexing
- FastAPI backend with REST APIs
- Streamlit web interface
- RAG evaluation using RAGAS
- Dockerized deployment
- GitHub Actions CI/CD

---

## Architecture

```text
                Security Data Sources
        (NVD, CISA, MITRE, Vendor Advisories,
          PDFs, HTML, RSS, JSON APIs)
                       │
                       ▼
             Document Ingestion Pipeline
                       │
                       ▼
          Cleaning & Text Normalization
                       │
                       ▼
              Intelligent Chunking
                       │
                       ▼
             Metadata Extraction
                       │
                       ▼
            Embedding Generation
          (Sentence Transformers)
                       │
                       ▼
                 Vector Database
              (FAISS / Qdrant)
                       │
             Metadata Database
                       │
                       ▼
                Retrieval Pipeline
        (Dense + BM25 + Reranker)
                       │
                       ▼
                Prompt Construction
                       │
                       ▼
                  LLM (Llama/Mistral)
                       │
                       ▼
             Answer + Source References
                       │
                       ▼
          FastAPI Backend + Streamlit UI
```

---

## Tech Stack

| Layer | Technology |
|--------|------------|
| Language | Python 3.11+ |
| Dependency Management | uv |
| Backend | FastAPI |
| Frontend | Streamlit |
| RAG Framework | LangChain |
| Embeddings | SentenceTransformers |
| Vector Database | FAISS |
| Sparse Retrieval | BM25 |
| Reranker | BAAI bge-reranker |
| LLM | Llama 3 / Mistral |
| Metadata Database | SQLite / PostgreSQL |
| Evaluation | RAGAS |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Testing | Pytest |
| Logging | Loguru |

---

## Project Structure

```text
cyber-threat-rag/

├── app/
│   ├── api/
│   ├── core/
│   ├── ingestion/
│   ├── retrieval/
│   ├── rag/
│   ├── evaluation/
│   ├── models/
│   ├── services/
│   └── utils/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── embeddings/
│
├── vectorstore/
├── streamlit/
├── scripts/
├── tests/
├── docs/
│
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── docker-compose.yml
├── README.md
└── .env.example
```

---

## Workflow

```text
Download Security Documents
            │
            ▼
Store Raw Documents
            │
            ▼
Clean & Normalize
            │
            ▼
Split into Chunks
            │
            ▼
Generate Embeddings
            │
            ▼
Store in FAISS
            │
            ▼
User Query
            │
            ▼
Hybrid Retrieval
(Dense + BM25)
            │
            ▼
Rerank Results
            │
            ▼
Build Prompt
            │
            ▼
LLM Generates Answer
            │
            ▼
Return Answer + References
```

---

## Development Roadmap

### Phase 1 – Data Ingestion

- Collect cybersecurity documents
- Parse and clean content
- Store raw and processed data

### Phase 2 – Knowledge Base

- Chunk documents
- Generate embeddings
- Build FAISS vector index

### Phase 3 – Retrieval Pipeline

- Dense retrieval
- BM25 retrieval
- Hybrid search
- Cross-encoder reranking

### Phase 4 – RAG

- Context building
- Prompt engineering
- LLM integration
- Source-grounded responses

### Phase 5 – Backend & UI

- FastAPI APIs
- Streamlit dashboard
- Query history
- Document management

### Phase 6 – Production Features

- Continuous ingestion
- Evaluation with RAGAS
- Docker deployment
- GitHub Actions CI/CD
- Monitoring & logging

---

## Data Sources

- NIST National Vulnerability Database (NVD)
- CISA Security Advisories
- MITRE ATT&CK
- Microsoft Security Response Center
- Cisco Security Advisories
- Red Hat Security Advisories
- Vendor Security Bulletins
- Technical Documentation
- PDF Reports
- RSS Feeds

---

## Goals

- Build a production-ready cybersecurity RAG platform
- Provide accurate and grounded threat intelligence
- Reduce hallucinations through retrieval augmentation
- Support scalable ingestion and indexing
- Demonstrate modern GenAI, backend, and MLOps practices

---

## Future Improvements

- Qdrant / Milvus vector database
- Metadata filtering
- Multi-agent workflows
- GraphRAG integration
- Knowledge graph support
- User authentication
- Role-based access control
- Redis caching
- Prometheus & Grafana monitoring
- Kubernetes deployment

---

## License

This project is intended for educational and portfolio purposes.