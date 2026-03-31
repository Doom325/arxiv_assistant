from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routers import papers, search, integrations, users, library, batch, citations, patterns, analytics, queue, timeline
from scheduler import start_scheduler
from database import SessionLocal
from models import User
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError, ResponseValidationError
import traceback
import logging
import json

# Configure uvicorn loggers
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

# models.Base.metadata.create_all(bind=engine) # Moved to lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Successfully initialized database tables.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        # We don't raise here to allow uvicorn to finish starting and serve the 500/traceback
    
    # Ensure default user exists for bookmarks
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.id == 1).first():
            db.add(User(id=1, email="default@example.com", hashed_password="nopassword"))
            db.commit()
    except Exception as e:
        print(f"Error creating default user: {e}")
    finally:
        db.close()

    # Start the scheduler on startup
    start_scheduler()
    yield
    # Shutdown logic if needed

app = FastAPI(title="Arxiv AI Assistant", lifespan=lifespan)

@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request: Request, exc: ResponseValidationError):
    err_msg = f"SCHEMA VALIDATION ERROR: {exc}\n{traceback.format_exc()}"
    # Log specific details about which part of the response failed
    logger.error(err_msg)
    return Response(
        content=json.dumps({"detail": exc.errors(), "body": str(exc)}),
        status_code=500,
        media_type="application/json"
    )

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        err_msg = f"CRITICAL 500 ERROR: {exc}\n{traceback.format_exc()}"
        logger.error(err_msg)
        return Response(content=err_msg, status_code=500, media_type="text/plain")

# Create data/pdfs directory if it doesn't exist
os.makedirs("data/pdfs", exist_ok=True)

# Mount static files
app.mount("/pdfs", StaticFiles(directory="data/pdfs"), name="pdfs")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for mobile testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers.router)
app.include_router(search.router)
app.include_router(integrations.router)
app.include_router(users.router)
app.include_router(library.router)
app.include_router(batch.router)
app.include_router(citations.router)
app.include_router(patterns.router)
app.include_router(analytics.router)
app.include_router(queue.router)
app.include_router(timeline.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to arXiv AI Assistant API"}
