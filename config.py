"""
Configuration settings for the book recommender system
"""

import os
from pathlib import Path

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use defaults

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Data paths
DATA_DIR = BASE_DIR / "data"
BOOKS_CSV = BASE_DIR / "books_cleaned.csv"
BOOKS_WITH_EMOTIONS = BASE_DIR / "data" / "books_with_emotions.csv"
TAGGED_DESCRIPTIONS = DATA_DIR / "tagged_description.txt"

# Vector database
VECTOR_DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "book_recommendations"

# Model settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DEVICE = os.getenv("DEVICE", "cpu")  # Force CPU for compatibility

# Search settings
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "10"))
DEFAULT_MIN_RATING = float(os.getenv("DEFAULT_MIN_RATING", "3.5"))
SEARCH_MULTIPLIER = 5  # Fetch 5x results before filtering

# Query validation
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "500"))
MIN_QUERY_LENGTH = int(os.getenv("MIN_QUERY_LENGTH", "3"))

# UI settings
GALLERY_COLUMNS = 8
GALLERY_ROWS = 2
DESC_TRUNCATE_WORDS = 30

# Application settings
APP_TITLE = os.getenv("APP_TITLE", "Semantic Book Recommender")
APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION",
    "Find your next favorite book using AI-powered semantic search"
)

# API settings - Secure defaults
API_HOST = os.getenv("API_HOST", "127.0.0.1")  # Localhost by default for security
API_PORT = int(os.getenv("API_PORT", "7860"))

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
