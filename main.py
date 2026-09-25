from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine
from backend.models import Complaint  # registers ORM model
from backend.database import Base
from backend.api.complaints import router as complaints_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NagrikAI",
    description="AI-powered civic complaint intelligence system for municipal teams.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints_router)


@app.get("/", tags=["health"])
def root():
    return {
        "service": "NagrikAI",
        "description": "Civic complaint intelligence system",
        "docs": "/docs",
    }
