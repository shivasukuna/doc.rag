<!-- omit in toc -->

<p align="center">
  <img src="readme-files/Doc.RAG.svg" alt="Doc.RAG" width="600">
</p>

<p align="center">
  A full-stack Retrieval-Augmented Generation application for chatting with PDF documents using hybrid search (BM25 + vector search), reranking, and grounded LLM responses.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#project-structure">Project Structure</a> •
  <a href="#api-endpoints">API Endpoints</a> •
  <a href="#credits">Credits</a>
</p>

<br>

<p align="center">
  <img src="https://skillicons.dev/icons?i=nextjs,ts,python,fastapi,sqlite&perline=8" />
</p>

<p align="center">
  FAISS • BM25 • Ollama • Sentence-Transformers
</p>

---

## Features

- **PDF Upload & Parsing** — Extract text from documents with OCR fallback (Tesseract)
- **Text Chunking** — Split documents into semantically meaningful chunks
- **Hybrid Retrieval (BM25 + FAISS)** — Combines keyword-based BM25 with dense vector search
- **Embedding Generation** — Sentence-transformers for semantic understanding
- **Cross-Encoder Reranking** — Improves retrieval quality using neural reranking
- **Context-Aware Chat** — Maintains conversation history
- **Streaming Responses** — Token-level streaming from LLM
- **Document Management** — Upload, list, and delete documents
- **System Monitoring** — CPU, RAM, GPU stats
- **Modern UI** — Built with Next.js + shadcn/ui

---

## Tech Stack

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion

### Backend

- FastAPI
- SQLite + SQLAlchemy
- FAISS (vector search)
- BM25 (sparse retrieval)
- Sentence-Transformers (embeddings)
- Cross-Encoder (reranking)
- Ollama (Gemma 2B)
- PyPDF / pdf2image / Tesseract (document processing)

---

## Getting Started

> [!WARNING]
> ⚠️ Important Notice
>
> This project is a college project created primarily for learning purposes. It is not production-grade software.
>
> • Code may not be optimized or efficient  
> • Some functions/APIs may be hardcoded  
> • Error handling may be incomplete  
> • Not suitable for real-world deployment  
>
> This was built to learn and experiment with RAG, LLMs, and full-stack development.

### Screenshot

<p align="center">
  <img src="readme-files/screenshot.png" alt="Doc.RAG Interface" width="900">
</p>

---

### Prerequisites

- Node.js 18+
- Python 3.11+
- Ollama
- Tesseract OCR

---

### Installation

```bash
# Frontend
cd rag-frontend
npm install

# Backend dependencies
pip install fastapi uvicorn sqlalchemy pypdf pdf2image pytesseract faiss-cpu numpy sentence-transformers ollama requests psutil GPUtil pydantic rank-bm25

# Pull LLM
ollama pull gemma2:2b