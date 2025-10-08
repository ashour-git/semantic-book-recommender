"""
Updated Gradio Dashboard using the BookRecommender class
Professional, modular implementation
"""

import pandas as pd
import numpy as np
import gradio as gr
from recommender import BookRecommender
import config


# Initialize recommender
print("Initializing Book Recommender System...")
recommender = BookRecommender(
    books_csv=str(config.BOOKS_CSV),
    documents_path=str(config.TAGGED_DESCRIPTIONS),
    persist_dir=str(config.VECTOR_DB_DIR),
    use_existing_db=True
)
print("System ready!")

# Load books with emotions if available
try:
    books = pd.read_csv(config.DATA_DIR / "books_with_emotions.csv")
    has_emotions = True
    print("✓ Loaded books with emotion data")
except FileNotFoundError:
    try:
        books = pd.read_csv(config.DATA_DIR / "books_with_categories.csv")
        has_emotions = False
        print("✓ Loaded books with categories (emotions not available)")
    except FileNotFoundError:
        books = recommender.books
        has_emotions = False
        print("⚠ Warning: Using base dataset, category/emotion filtering disabled")

# Prepare thumbnail images
if "thumbnail" in books.columns:
    books["large_thumbnail"] = books["thumbnail"] + "&fife=w800"
    books["large_thumbnail"] = np.where(
        books["large_thumbnail"].isna(),
        "cover-not-found.jpg",
        books["large_thumbnail"],
    )
else:
    books["large_thumbnail"] = "cover-not-found.jpg"


def retrieve_semantic_recommendations(
    query: str,
    category: str = None,
    tone: str = None,
    initial_top_k: int = 50,
    final_top_k: int = 16,
) -> pd.DataFrame:
    """
    Retrieve book recommendations with optional filtering
    
    Args:
        query: Natural language search query
        category: Book category filter
        tone: Emotional tone filter
        initial_top_k: Initial number of results to fetch
        final_top_k: Final number of results to return
    
    Returns:
        DataFrame with recommended books
    """
    # Get semantic recommendations
    results = recommender.get_recommendations(
        query, 
        top_k=initial_top_k,
        min_rating=None  # Don't filter by rating here
    )
    
    # Merge with full book data for additional fields
    book_recs = books[books["isbn13"].isin(results["isbn13"])].head(initial_top_k)
    
    # Category filtering
    if category != "All" and "simple_categories" in book_recs.columns:
        book_recs = book_recs[book_recs["simple_categories"] == category].head(final_top_k)
    else:
        book_recs = book_recs.head(final_top_k)
    
    # Emotion-based sorting
    if has_emotions and tone != "All":
        emotion_mapping = {
            "Happy": "joy",
            "Surprising": "surprise",
            "Angry": "anger",
            "Suspenseful": "fear",
            "Sad": "sadness"
        }
        if tone in emotion_mapping and emotion_mapping[tone] in book_recs.columns:
            book_recs = book_recs.sort_values(
                by=emotion_mapping[tone], 
                ascending=False
            )
    
    return book_recs


def recommend_books(query: str, category: str, tone: str):
    """
    Generate book recommendations for Gradio interface
    
    Args:
        query: User search query
        category: Selected category
        tone: Selected emotional tone
    
    Returns:
        List of (image, caption) tuples for gallery display
    """
    if not query.strip():
        return []
    
    recommendations = retrieve_semantic_recommendations(query, category, tone)
    results = []

    for _, row in recommendations.iterrows():
        # Truncate description
        description = row.get("description", "No description available")
        truncated_desc_split = description.split()
        truncated_description = " ".join(truncated_desc_split[:30]) + "..."

        # Format authors
        authors = row.get("authors", "Unknown")
        authors_split = authors.split(";")
        if len(authors_split) == 2:
            authors_str = f"{authors_split[0]} and {authors_split[1]}"
        elif len(authors_split) > 2:
            authors_str = f"{', '.join(authors_split[:-1])}, and {authors_split[-1]}"
        else:
            authors_str = authors

        # Create caption
        title = row.get("title", "Unknown Title")
        caption = f"{title} by {authors_str}: {truncated_description}"
        
        # Add to results
        image = row.get("large_thumbnail", "cover-not-found.jpg")
        results.append((image, caption))
    
    return results


# Prepare dropdown options
categories = ["All"]
if "simple_categories" in books.columns:
    categories += sorted(books["simple_categories"].dropna().unique())

tones = ["All"]
if has_emotions:
    tones += ["Happy", "Surprising", "Angry", "Suspenseful", "Sad"]

# Build Gradio interface
with gr.Blocks(theme=gr.themes.Soft()) as dashboard:
    gr.Markdown(f"# {config.APP_TITLE}")
    gr.Markdown(f"*{config.APP_DESCRIPTION}*")
    
    with gr.Row():
        user_query = gr.Textbox(
            label="Describe the book you're looking for:",
            placeholder="e.g., A story about forgiveness and redemption",
            scale=3
        )
        category_dropdown = gr.Dropdown(
            choices=categories,
            label="Category:",
            value="All",
            scale=1
        )
        tone_dropdown = gr.Dropdown(
            choices=tones,
            label="Emotional Tone:",
            value="All",
            scale=1
        )
        submit_button = gr.Button("Search", variant="primary")
    
    gr.Markdown("## Recommendations")
    output = gr.Gallery(
        label="Recommended Books",
        columns=8,
        rows=2,
        height="auto"
    )
    
    # Examples
    gr.Examples(
        examples=[
            ["A thrilling mystery with unexpected twists", "All", "All"],
            ["Epic fantasy adventure with magic", "All", "All"],
            ["Self-improvement and productivity", "All", "All"],
        ],
        inputs=[user_query, category_dropdown, tone_dropdown],
        label="Try these examples:"
    )
    
    submit_button.click(
        fn=recommend_books,
        inputs=[user_query, category_dropdown, tone_dropdown],
        outputs=output
    )

if __name__ == "__main__":
    dashboard.launch(
        server_name=config.API_HOST,
        server_port=config.API_PORT,
        share=False
    )
