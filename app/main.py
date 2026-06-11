from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_all_tables


# ── Lifespan ──────────────────────────────────────────────────────────────────
# Runs startup logic before the first request and teardown after the last.
# Replaces the deprecated @app.on_event("startup") pattern.

@asynccontextmanager
async def lifespan(app: FastAPI):

    # ── Startup ───────────────────────────────────────────────
    print(f"\n  {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"  DEBUG = {settings.DEBUG}")

    # Create upload directory if it does not exist
    settings.ensure_upload_dir()
    print(f"  Upload directory: {settings.UPLOAD_DIR}")

    # Validate ESG weights sum to 1.0 — fail fast on misconfiguration
    if not settings.esg_weights_sum_to_one():
        raise ValueError(
            f"ESG weights must sum to 1.0 — got "
            f"E={settings.ENVIRONMENTAL_WEIGHT} "
            f"S={settings.SOCIAL_WEIGHT} "
            f"G={settings.GOVERNANCE_WEIGHT}"
        )

    # Auto-create tables in dev — use Alembic migrations in production
    if settings.DEBUG:
        try:
            create_all_tables()
            print("  Database tables: ready\n")
        except Exception as exc:
            print(f"  [WARNING] Could not connect to database: {exc}")
            print("  Make sure PostgreSQL is running and DATABASE_URL is correct.\n")

    yield

    # ── Shutdown ──────────────────────────────────────────────
    print("\n  Shutting down ESG platform...\n")


# ── App instance ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────
# Uncomment each router as its file is written.
# Each router is prefixed and tagged so it appears as its own section in /docs.

# from app.routers import upload
# app.include_router(
#     upload.router,
#     prefix=f"{settings.API_V1_PREFIX}/upload",
#     tags=["Data upload"],
# )

# from app.routers import environmental
# app.include_router(
#     environmental.router,
#     prefix=f"{settings.API_V1_PREFIX}/environmental",
#     tags=["Environmental"],
# )

# from app.routers import social
# app.include_router(
#     social.router,
#     prefix=f"{settings.API_V1_PREFIX}/social",
#     tags=["Social"],
# )

# from app.routers import governance
# app.include_router(
#     governance.router,
#     prefix=f"{settings.API_V1_PREFIX}/governance",
#     tags=["Governance"],
# )

# from app.routers import scoring
# app.include_router(
#     scoring.router,
#     prefix=f"{settings.API_V1_PREFIX}/scoring",
#     tags=["ESG scoring"],
# )


# ── Core endpoints ────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    """Landing — confirms the API is reachable."""
    return {
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs":    "/docs",
        "health":  "/health",
    }


@app.get("/health", tags=["Root"])
def health_check():
    """
    Lightweight liveness probe.
    Returns 200 as long as the process is running.
    Does not check the database — use /health/db for that.
    """
    return {
        "status":  "ok",
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug":   settings.DEBUG,
    }


@app.get("/health/db", tags=["Root"])
def health_check_db():
    """
    Database connectivity probe.
    Executes a lightweight query to verify the connection is live.
    """
    from sqlalchemy import text
    from app.database import SessionLocal

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unreachable", "detail": str(exc)},
        )


@app.get("/config", tags=["Root"])
def show_config():
    """
    Returns non-sensitive configuration values.
    Useful for verifying that weights and thresholds are loaded correctly.
    Only available when DEBUG=True.
    """
    if not settings.DEBUG:
        return JSONResponse(status_code=403, content={"detail": "Not available in production."})

    return {
        "esg_weights": {
            "environmental": settings.ENVIRONMENTAL_WEIGHT,
            "social":        settings.SOCIAL_WEIGHT,
            "governance":    settings.GOVERNANCE_WEIGHT,
            "sum":           round(
                settings.ENVIRONMENTAL_WEIGHT +
                settings.SOCIAL_WEIGHT +
                settings.GOVERNANCE_WEIGHT, 10
            ),
        },
        "score_thresholds": {
            "excellent": settings.SCORE_EXCELLENT_THRESHOLD,
            "good":      settings.SCORE_GOOD_THRESHOLD,
            "average":   settings.SCORE_AVERAGE_THRESHOLD,
        },
        "upload": {
            "dir":               settings.UPLOAD_DIR,
            "max_size_mb":       settings.MAX_UPLOAD_SIZE_MB,
            "allowed_extensions": settings.ALLOWED_EXTENSIONS,
        },
    }