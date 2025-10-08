"""
Book Recommender System - Core Module
Provides semantic search functionality for book recommendations
"""

import pandas as pd
import logging
from typing import List, Optional
from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

from utils import (
    validate_query,
    validate_top_k,
    validate_rating,
    safe_isbn_parse,
    handle_errors,
    RecommenderError
)

# Configure logging
logger = logging.getLogger(__name__)


class BookRecommender:
    """
    Professional book recommendation system using semantic search
    
    Features:
    - CPU-optimized embeddings (no GPU required)
    - Vector database for fast similarity search
    - Quality filtering and ranking
    """
    
    def __init__(
        self,
        books_csv: str = "books_cleaned.csv",
        documents_path: str = "tagged_description.txt",
        persist_dir: str = "./chroma_db",
        use_existing_db: bool = True
    ):
        """
        Initialize the book recommender system

        Args:
            books_csv: Path to the books CSV file
            documents_path: Path to the tagged descriptions file
            persist_dir: Directory to persist the vector database
            use_existing_db: Whether to load existing DB or create new one

        Raises:
            RecommenderError: If initialization fails
        """
        try:
            logger.info("Initializing Book Recommender System...")

            # Validate paths
            books_path = Path(books_csv)
            if not books_path.exists():
                raise RecommenderError(f"Books CSV not found: {books_csv}")

            # Load books data
            self.books = pd.read_csv(books_csv)
            logger.info(f"Loaded {len(self.books)} books from {books_csv}")

            # Validate required columns
            required_cols = ['isbn13', 'title', 'authors', 'average_rating']
            missing_cols = [col for col in required_cols if col not in self.books.columns]
            if missing_cols:
                raise RecommenderError(f"Missing required columns: {missing_cols}")

            self.persist_dir = persist_dir

            # Initialize embeddings model
            logger.info("Loading embedding model...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

            # Load or create vector database
            if use_existing_db:
                self.db = self._load_database()
            else:
                if not Path(documents_path).exists():
                    raise RecommenderError(f"Documents file not found: {documents_path}")
                self.db = self._create_database(documents_path)

            logger.info("Recommender system ready!")

        except Exception as e:
            logger.error(f"Failed to initialize recommender: {e}", exc_info=True)
            raise RecommenderError(f"Initialization failed: {str(e)}")
    
    def _load_database(self) -> Chroma:
        """
        Load existing vector database

        Raises:
            RecommenderError: If database loading fails
        """
        try:
            logger.info(f"Loading vector database from {self.persist_dir}")
            db = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name="book_recommendations"
            )
            logger.info("Vector database loaded successfully")
            return db
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            raise RecommenderError(f"Database loading failed: {str(e)}")
    
    def _create_database(self, documents_path: str) -> Chroma:
        """
        Create new vector database from documents

        Raises:
            RecommenderError: If database creation fails
        """
        try:
            logger.info(f"Creating vector database from {documents_path}")
            raw_documents = TextLoader(documents_path).load()

            text_splitter = CharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=0,
                separator="\n"
            )
            documents = text_splitter.split_documents(raw_documents)
            logger.info(f"Split into {len(documents)} documents")

            db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name="book_recommendations",
                persist_directory=self.persist_dir
            )
            logger.info("Vector database created successfully")
            return db
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise RecommenderError(f"Database creation failed: {str(e)}")
    
    @handle_errors
    def get_recommendations(
        self,
        query: str,
        top_k: int = 10,
        min_rating: Optional[float] = 3.5
    ) -> pd.DataFrame:
        """
        Get book recommendations based on semantic search

        Args:
            query: Natural language search query
            top_k: Number of recommendations to return
            min_rating: Minimum average rating filter (None to disable)

        Returns:
            DataFrame with recommended books

        Raises:
            ValidationError: If input parameters are invalid
            RecommenderError: If search fails
        """
        # Validate inputs
        query = validate_query(query)
        top_k = validate_top_k(top_k)
        min_rating = validate_rating(min_rating)

        logger.info(f"Searching for: '{query[:50]}...' (top_k={top_k}, min_rating={min_rating})")

        try:
            # Semantic search with higher initial results for filtering
            search_k = top_k * 5 if min_rating else top_k
            recs = self.db.similarity_search(query, k=search_k)

            if not recs:
                logger.warning(f"No results found for query: {query}")
                return pd.DataFrame()

            # Extract ISBNs safely
            books_isbns = []
            for rec in recs:
                isbn = safe_isbn_parse(rec.page_content)
                if isbn:
                    books_isbns.append(isbn)

            if not books_isbns:
                logger.warning("No valid ISBNs found in search results")
                return pd.DataFrame()

            logger.debug(f"Found {len(books_isbns)} ISBNs")

            # Filter and rank
            results = self.books[self.books["isbn13"].isin(books_isbns)].copy()

            # Quality filter
            if min_rating:
                results = results[results["average_rating"] >= min_rating]

            # Sort by relevance (order from vector search) and limit
            isbn_order = {isbn: i for i, isbn in enumerate(books_isbns)}
            results['search_rank'] = results['isbn13'].map(isbn_order)
            results = results.sort_values('search_rank').head(top_k)

            logger.info(f"Returning {len(results)} recommendations")

            return results[[
                'title', 'authors', 'average_rating',
                'num_pages', 'published_year', 'isbn13'
            ]]

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise RecommenderError(f"Failed to get recommendations: {str(e)}")
    
    @handle_errors
    def search(self, query: str, top_k: int = 10) -> List[dict]:
        """
        Simple search interface returning list of dictionaries

        Args:
            query: Natural language search query
            top_k: Number of results to return

        Returns:
            List of book dictionaries

        Raises:
            ValidationError: If input parameters are invalid
            RecommenderError: If search fails
        """
        results = self.get_recommendations(query, top_k)
        return results.to_dict('records')


if __name__ == "__main__":
    # Example usage
    recommender = BookRecommender()
    
    # Test query
    results = recommender.get_recommendations(
        "Science fiction about artificial intelligence",
        top_k=5
    )
    
    print("Book Recommendations:")
    print(results)
