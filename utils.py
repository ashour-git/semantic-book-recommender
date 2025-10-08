"""
Utility functions for validation, error handling, and common operations
"""

import logging
import re
from typing import Optional
from functools import wraps
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class RecommenderError(Exception):
    """Custom exception for recommender system errors"""
    pass


def validate_query(query: str) -> str:
    """
    Validate and sanitize search query

    Args:
        query: User input query string

    Returns:
        Sanitized query string

    Raises:
        ValidationError: If query is invalid
    """
    if not query or not isinstance(query, str):
        raise ValidationError("Query must be a non-empty string")

    # Strip whitespace
    query = query.strip()

    # Check length constraints
    if len(query) < config.MIN_QUERY_LENGTH:
        raise ValidationError(
            f"Query too short. Minimum {config.MIN_QUERY_LENGTH} characters required."
        )

    if len(query) > config.MAX_QUERY_LENGTH:
        raise ValidationError(
            f"Query too long. Maximum {config.MAX_QUERY_LENGTH} characters allowed."
        )

    # Remove potentially dangerous characters (basic sanitization)
    # Allow alphanumeric, spaces, and common punctuation
    sanitized = re.sub(r'[^\w\s\.,!?\-\'"]+', '', query)

    if not sanitized:
        raise ValidationError("Query contains only invalid characters")

    logger.debug(f"Validated query: {sanitized[:50]}...")
    return sanitized


def validate_top_k(top_k: int, max_value: int = 100) -> int:
    """
    Validate top_k parameter

    Args:
        top_k: Number of results to return
        max_value: Maximum allowed value

    Returns:
        Validated top_k value

    Raises:
        ValidationError: If top_k is invalid
    """
    if not isinstance(top_k, int):
        raise ValidationError("top_k must be an integer")

    if top_k < 1:
        raise ValidationError("top_k must be at least 1")

    if top_k > max_value:
        raise ValidationError(f"top_k cannot exceed {max_value}")

    return top_k


def validate_rating(rating: Optional[float]) -> Optional[float]:
    """
    Validate rating parameter

    Args:
        rating: Minimum rating filter

    Returns:
        Validated rating value

    Raises:
        ValidationError: If rating is invalid
    """
    if rating is None:
        return None

    if not isinstance(rating, (int, float)):
        raise ValidationError("Rating must be a number")

    if rating < 0 or rating > 5:
        raise ValidationError("Rating must be between 0 and 5")

    return float(rating)


def safe_int_parse(value: str, default: int = 0) -> int:
    """
    Safely parse integer from string

    Args:
        value: String to parse
        default: Default value if parsing fails

    Returns:
        Parsed integer or default value
    """
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse int from '{value}': {e}")
        return default


def safe_isbn_parse(content: str) -> Optional[int]:
    """
    Safely parse ISBN from page content

    Args:
        content: Page content string

    Returns:
        Parsed ISBN or None if parsing fails
    """
    try:
        # Expected format: "ISBN13 title description"
        cleaned = content.strip('"').strip()
        parts = cleaned.split(maxsplit=1)

        if not parts:
            return None

        isbn = int(parts[0])

        # Basic ISBN-13 validation (should be 13 digits)
        if len(str(isbn)) != 13:
            logger.warning(f"Invalid ISBN length: {isbn}")
            return None

        return isbn
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse ISBN from '{content[:50]}...': {e}")
        return None


def handle_errors(func):
    """
    Decorator for comprehensive error handling

    Usage:
        @handle_errors
        def my_function():
            # function code
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            raise
        except RecommenderError as e:
            logger.error(f"Recommender error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise RecommenderError(f"An unexpected error occurred: {str(e)}")

    return wrapper


def format_authors(authors: str) -> str:
    """
    Format author names for display

    Args:
        authors: Semicolon-separated author names

    Returns:
        Formatted author string
    """
    if not authors or authors == "Unknown":
        return "Unknown"

    authors_list = [a.strip() for a in authors.split(";")]

    if len(authors_list) == 1:
        return authors_list[0]
    elif len(authors_list) == 2:
        return f"{authors_list[0]} and {authors_list[1]}"
    else:
        return f"{', '.join(authors_list[:-1])}, and {authors_list[-1]}"


def truncate_description(description: str, max_words: int = None) -> str:
    """
    Truncate description to specified word count

    Args:
        description: Full description text
        max_words: Maximum number of words (uses config default if None)

    Returns:
        Truncated description with ellipsis
    """
    if not description:
        return "No description available"

    if max_words is None:
        max_words = config.DESC_TRUNCATE_WORDS

    words = description.split()
    if len(words) <= max_words:
        return description

    return " ".join(words[:max_words]) + "..."
