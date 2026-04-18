# 🔍 Document Intelligence API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)

**A production-ready, scalable RESTful API for AI-powered document analysis.**

Upload PDFs or plain text files, extract content automatically, and get intelligent summaries powered by **Groq (Llama 3)** — all processed asynchronously in the background.

[Quick Start](#-quick-start) · [API Docs](#-api-endpoints) · [Architecture](#-architecture) · [Contributing](#-development)

</div>

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔐 **JWT Authentication** | Secure registration/login with bcrypt password hashing and strength validation |
| 📄 **Document Upload** | PDF and plain text support with file size validation (configurable limit) |
| 🤖 **AI Summarization** | Automatic text extraction + intelligent summarization via Groq (Llama 3) |
| ⚡ **Async Processing** | Celery workers handle AI tasks in the background — API never blocks |
| 📊 **Document Analytics** | Word count, page count, processing time metrics per document |
| 📈 **Stats Dashboard** | Aggregated statistics endpoint for all your documents |
| 📄 **Pagination** | All list endpoints support pagination with metadata |
| 🗑️ **Full CRUD** | Upload, list, view, and delete documents |
| 🏥 **Health Checks** | `/health` endpoint verifying DB + Redis connectivity |
| 🔍 **Request Tracing** | Unique `X-Request-ID` on every request for distributed tracing |
| 📝 **Structured Logging** | Formatted logs with request IDs, timing, and severity levels |
| 🐳 **Fully Dockerized** | Multi-stage build, non-root user, one-command startup |
| 🌸 **Worker Monitoring** | Celery Flower dashboard for real-time task monitoring |
| 🧪 **CI/CD Pipeline** | GitHub Actions with lint, test, and Docker build stages |
| ⚙️ **Error Handling** | Standardized error responses with consistent JSON format |

## 🏗️ Architecture

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────┐
│   Client     │──────▶│  FastAPI Server   │──────▶│ PostgreSQL  │
│  (Browser)   │◀──────│  + Middleware     │◀──────│  Database   │
└─────────────┘       │  + Error Handlers │       └─────────────┘
                      │  + Request IDs    │
                      └────────┬─────────┘
                               │
                        ┌──────▼──────┐
                        │    Redis     │
                        │  (Broker)    │
                        └──────┬──────┘
                               │
      ┌─────────────┐  ┌──────▼──────┐  ┌─────────────┐
      │   Flower     │  │   Celery     │──▶│  Groq API   │
      │  Dashboard   │──│   Worker     │◀──│  (Llama 3)  │
      │  :5555       │  └─────────────┘  └─────────────┘
      └─────────────┘
```

### Processing Pipeline

```
Upload → Validate → Save → Queue Task → Extract Text → Count Words/Pages → AI Summary → Done
  │         │         │        │              │                │                │          │
 API       API       Disk    Redis          Worker          Worker           Groq       DB
```

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A free [Groq API Key](https://console.groq.com) (for AI features)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/document-intelligence-api.git
cd document-intelligence-api
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Run with Docker Compose

```bash
docker-compose up -d --build
```

This starts **5 services** automatically:

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **API** | `8000` | http://localhost:8000 | FastAPI application server |
| **Swagger Docs** | `8000` | http://localhost:8000/docs | Interactive API documentation |
| **Flower** | `5555` | http://localhost:5555 | Celery task monitoring dashboard |
| **PostgreSQL** | `5432` | — | Relational database |
| **Redis** | `6379` | — | Message broker + cache |

### 4. Explore the API

👉 **http://localhost:8000/docs** — Interactive Swagger UI  
👉 **http://localhost:8000/redoc** — ReDoc documentation  
👉 **http://localhost:5555** — Flower worker monitoring  
👉 **http://localhost:8000/health** — Health check  

## 📡 API Endpoints

### 🏥 System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information and links |
| `GET` | `/health` | Health check (DB + Redis status) |

### 🔐 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Create a new user account |
| `POST` | `/api/v1/auth/login` | Get a JWT access token |
| `GET` | `/api/v1/auth/me` | Get current user profile |

### 📄 Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload a PDF or TXT file |
| `GET` | `/api/v1/documents/` | List documents (paginated) |
| `GET` | `/api/v1/documents/stats` | Get aggregate statistics |
| `GET` | `/api/v1/documents/{id}` | Get document details + AI summary |
| `DELETE` | `/api/v1/documents/{id}` | Delete a document |

## 🧪 Usage Example

### Register → Login → Upload → Get Summary

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "SecurePass1", "full_name": "Demo User"}'

# 2. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=demo@example.com&password=SecurePass1" | jq -r '.access_token')

# 3. Upload a document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# 4. Check the AI-generated summary
curl http://localhost:8000/api/v1/documents/1 \
  -H "Authorization: Bearer $TOKEN" | jq '.summary'

# 5. Get your stats
curl http://localhost:8000/api/v1/documents/stats \
  -H "Authorization: Bearer $TOKEN"
```

## 📁 Project Structure

```
document-intelligence-api/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD pipeline
├── app/
│   ├── api/                       # Route handlers (controllers)
│   │   ├── auth.py                # JWT auth (register, login, me)
│   │   ├── documents.py           # Document CRUD + pagination
│   │   └── health.py              # Health check endpoint
│   ├── core/                      # Core infrastructure
│   │   ├── config.py              # Pydantic Settings (all config)
│   │   ├── database.py            # Async SQLAlchemy engine
│   │   ├── exceptions.py          # Global error handlers
│   │   ├── logging.py             # Structured logging setup
│   │   └── middleware.py          # Request ID + timing middleware
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── user.py                # User table
│   │   └── document.py            # Document table + analytics
│   ├── schemas/                   # Pydantic validation schemas
│   │   ├── user.py                # User schemas + password validation
│   │   └── document.py            # Document + pagination schemas
│   ├── services/                  # Business logic layer
│   │   └── ai_service.py          # Groq integration (retry + logging)
│   ├── worker/                    # Background processing
│   │   ├── celery_app.py          # Celery configuration
│   │   └── tasks.py               # Document processing pipeline
│   └── main.py                    # FastAPI app factory
├── tests/                         # Test suite
│   ├── conftest.py                # Shared fixtures
│   ├── test_auth.py               # Auth endpoint tests
│   └── test_documents.py          # Document endpoint tests
├── .env.example                   # Environment variable template
├── .gitignore
├── docker-compose.yml             # Multi-service orchestration
├── Dockerfile                     # Multi-stage production build
├── LICENSE                        # MIT License
├── Makefile                       # Development shortcuts
├── pyproject.toml                 # Modern Python project config
├── README.md
└── requirements.txt               # Pinned dependencies
```

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API Framework** | FastAPI | High-performance async web framework |
| **ORM** | SQLAlchemy 2.0 | Async database operations (asyncpg driver) |
| **Validation** | Pydantic v2 | Request/response data validation |
| **Auth** | python-jose + passlib | JWT tokens + bcrypt password hashing |
| **Task Queue** | Celery | Distributed background job processing |
| **Broker** | Redis | Message broker + result backend |
| **Database** | PostgreSQL 15 | Persistent relational storage |
| **AI** | Groq (Llama 3) | Free, ultra-fast text summarization |
| **PDF Processing** | PyMuPDF (fitz) | PDF text extraction |
| **Monitoring** | Flower | Real-time Celery task dashboard |
| **Containerization** | Docker Compose | Multi-service orchestration |
| **CI/CD** | GitHub Actions | Automated lint, test, build pipeline |
| **Linting** | Ruff | Fast Python linter |
| **Testing** | pytest | Test framework with async support |

## 🔧 Development

### Common commands (with Makefile)

```bash
make dev          # Build and start everything
make logs         # Follow API logs
make logs-worker  # Follow worker logs
make test         # Run test suite
make lint         # Run code linter
make down         # Stop all services
make clean        # Remove everything (containers + volumes)
```

### Without Make

```bash
docker-compose up -d --build      # Start
docker-compose logs -f api        # API logs
docker-compose exec api pytest -v # Tests
docker-compose down               # Stop
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *required* | PostgreSQL connection string |
| `REDIS_URL` | *required* | Redis connection string |
| `GROQ_API_KEY` | `""` | Groq API key for AI features |
| `SECRET_KEY` | `"super_secret..."` | JWT signing key |
| `MAX_UPLOAD_SIZE_MB` | `20` | Maximum upload file size |
| `GROQ_MODEL` | `"llama3-8b-8192"` | AI model to use |
| `DEBUG` | `false` | Enable debug logging |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |

## 📝 License

This project is licensed under the [MIT License](LICENSE).
