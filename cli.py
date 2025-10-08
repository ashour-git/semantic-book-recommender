#!/usr/bin/env python3
"""
Command-line interface for the book recommender system
Professional CLI with argument parsing
"""

import argparse
import sys
from recommender import BookRecommender
from tabulate import tabulate


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Semantic Book Recommender - Find books using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "science fiction about AI"
  python cli.py "romantic comedy" --top 5 --min-rating 4.0
  python cli.py "mystery thriller" --format json
        """
    )
    
    parser.add_argument(
        "query",
        type=str,
        help="Natural language search query"
    )
    
    parser.add_argument(
        "-k", "--top",
        type=int,
        default=10,
        help="Number of recommendations (default: 10)"
    )
    
    parser.add_argument(
        "-r", "--min-rating",
        type=float,
        default=3.5,
        help="Minimum average rating (default: 3.5)"
    )
    
    parser.add_argument(
        "-f", "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)"
    )
    
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Rebuild vector database from scratch"
    )
    
    args = parser.parse_args()
    
    # Initialize recommender
    print("Initializing recommender system...", file=sys.stderr)
    recommender = BookRecommender(use_existing_db=not args.no_db)
    print("Ready!\n", file=sys.stderr)
    
    # Get recommendations
    results = recommender.get_recommendations(
        query=args.query,
        top_k=args.top,
        min_rating=args.min_rating
    )
    
    # Output results
    if args.format == "json":
        print(results.to_json(orient="records", indent=2))
    elif args.format == "csv":
        print(results.to_csv(index=False))
    else:  # table
        print(f"\nQuery: '{args.query}'\n")
        print(tabulate(
            results,
            headers='keys',
            tablefmt='grid',
            showindex=False
        ))
        print(f"\nFound {len(results)} recommendations")


if __name__ == "__main__":
    main()
