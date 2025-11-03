from dotenv import load_dotenv
import os
import warnings
import logging

# Suppress warnings globally BEFORE loading any other modules
# This must be done first to catch all warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("default", category=DeprecationWarning)  # Keep deprecation warnings visible

# More specific filters
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*")
warnings.filterwarnings("ignore", message=".*Pydantic.*")
warnings.filterwarnings("ignore", message=".*serializer.*")

# Also suppress warnings in logging
logging.captureWarnings(True)

# Load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import auth, chat, file_upload, analysis, location

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(file_upload.router, prefix="/files", tags=["files"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(location.router, prefix="/location", tags=["location"])

@app.get("/")
def root():
    return {"message": "DataGround AI Assistant with Google ADK Multi-Agent System running"}
