"""
Document Intelligence API — Application Entry Point.

A scalable RESTful API for AI-powered document analysis.
Upload PDFs or text files and get intelligent summaries
powered by Groq (Llama 3), processed asynchronously via Celery.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging, get_logger
from app.core.middleware import RequestIdMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.core.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api import auth, documents, health

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    setup_logging(level="DEBUG" if settings.DEBUG else "INFO")
    logger.info("🚀 Starting %s v%s", settings.PROJECT_NAME, settings.VERSION)
    logger.info("📋 Run `alembic upgrade head` to apply database migrations")

    yield

    logger.info("👋 Shutting down %s", settings.PROJECT_NAME)
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    license_info={"name": "MIT License"},
    contact={"name": "API Support"},
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware (order matters: last added = first executed) ────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# ── Exception Handlers ────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────
app.include_router(
    health.router,
    prefix="/health",
    tags=["system"],
)
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"],
)
app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["documents"],
)


@app.get("/", tags=["root"], response_class=HTMLResponse)
def root():
    """Returns a beautiful landing page for the API."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{settings.PROJECT_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: #6366f1;
                --primary-dark: #4f46e5;
                --bg: #0f172a;
                --text: #f8fafc;
                --text-muted: #94a3b8;
                --card-bg: #1e293b;
            }}
            body {{
                margin: 0;
                font-family: 'Inter', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                text-align: center;
                padding: 2rem;
            }}
            .container {{
                max-width: 800px;
            }}
            h1 {{
                font-size: 3.5rem;
                font-weight: 800;
                margin-bottom: 1rem;
                background: linear-gradient(to right, #818cf8, #c084fc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -0.05em;
            }}
            p {{
                font-size: 1.25rem;
                color: var(--text-muted);
                margin-bottom: 2.5rem;
                line-height: 1.6;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin-bottom: 3rem;
            }}
            .card {{
                background: var(--card-bg);
                padding: 1.5rem;
                border-radius: 1rem;
                border: 1px solid #334155;
                transition: transform 0.2s, border-color 0.2s;
            }}
            .card:hover {{
                transform: translateY(-5px);
                border-color: var(--primary);
            }}
            .card h3 {{
                margin: 0 0 0.5rem 0;
                color: #818cf8;
            }}
            .card p {{
                font-size: 0.9rem;
                margin: 0;
            }}
            .buttons {{
                display: flex;
                gap: 1rem;
                justify-content: center;
            }}
            .btn {{
                padding: 0.75rem 2rem;
                border-radius: 0.5rem;
                font-weight: 600;
                text-decoration: none;
                transition: all 0.2s;
            }}
            .btn-primary {{
                background-color: var(--primary);
                color: white;
            }}
            .btn-primary:hover {{
                background-color: var(--primary-dark);
                box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
            }}
            .btn-outline {{
                border: 1px solid #334155;
                color: var(--text);
            }}
            .btn-outline:hover {{
                background-color: #1e293b;
            }}
            .version {{
                margin-top: 4rem;
                font-size: 0.8rem;
                color: #475569;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{settings.PROJECT_NAME}</h1>
            <p>{settings.PROJECT_DESCRIPTION}</p>
            
            <div class="grid">
                <div class="card">
                    <h3>⚡ Async AI</h3>
                    <p>Background processing via Celery & Llama 3.</p>
                </div>
                <div class="card">
                    <h3>🔐 Secure Auth</h3>
                    <p>JWT tokens & industry-standard encryption.</p>
                </div>
                <div class="card">
                    <h3>📊 Deep Insights</h3>
                    <p>Word counts, page counts, and smart summaries.</p>
                </div>
            </div>

            <div class="buttons">
                <a href="/docs" class="btn btn-primary">Explore Swagger UI</a>
                <a href="/redoc" class="btn btn-outline">Read ReDoc</a>
                <a href="http://localhost:5555" class="btn btn-outline" target="_blank">Monitor Workers</a>
            </div>

            <div class="version">
                Running v{settings.VERSION} • MIT License
            </div>
        </div>
    </body>
    </html>
    """
