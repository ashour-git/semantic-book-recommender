#!/usr/bin/env python3
"""
Test script to verify categories and emotions are properly loaded
"""

import sys
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from recommender import BookRecommender

def test_data_loading():
    """Test that data files load correctly with all required columns"""
    print("=" * 70)
    print("DATA LOADING TEST")
    print("=" * 70)
    
    # Test books_with_emotions.csv
    try:
        books = pd.read_csv(config.DATA_DIR / "books_with_emotions.csv")
        print(f"✓ Loaded books_with_emotions.csv: {len(books)} books")
        
        # Check for category column
        if "simple_categories" in books.columns:
            categories = sorted(books["simple_categories"].dropna().unique())
            print(f"\n✓ Categories found: {len(categories)}")
            for cat in categories:
                count = len(books[books["simple_categories"] == cat])
                print(f"  - {cat}: {count} books")
        else:
            print("✗ Missing 'simple_categories' column!")
            return False
        
        # Check for emotion columns
        emotion_cols = ["anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"]
        missing_emotions = [col for col in emotion_cols if col not in books.columns]
        
        if missing_emotions:
            print(f"\n✗ Missing emotion columns: {missing_emotions}")
            return False
        else:
            print(f"\n✓ All emotion columns present: {emotion_cols}")
            # Show sample emotion scores
            print("\nSample emotion scores (first book):")
            for col in emotion_cols:
                print(f"  {col}: {books[col].iloc[0]:.4f}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"✗ Error loading data: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_app_integration():
    """Test how the app loads and uses the data"""
    print("\n" + "=" * 70)
    print("APP INTEGRATION TEST")
    print("=" * 70)
    
    try:
        # Simulate app loading logic
        books = pd.read_csv(config.DATA_DIR / "books_with_emotions.csv")
        has_emotions = True
        print("✓ App successfully loaded books_with_emotions.csv")
        
        # Test category dropdown options
        categories = ["All"]
        if "simple_categories" in books.columns:
            categories += sorted(books["simple_categories"].dropna().unique())
        
        print(f"\n✓ Category dropdown options ({len(categories)} total):")
        for cat in categories:
            print(f"  - {cat}")
        
        # Test emotion dropdown options
        tones = ["All"]
        if has_emotions:
            tones += ["Happy", "Surprising", "Angry", "Suspenseful", "Sad"]
        
        print(f"\n✓ Emotion tone dropdown options ({len(tones)} total):")
        for tone in tones:
            emotion_map = {
                "Happy": "joy",
                "Surprising": "surprise",
                "Angry": "anger",
                "Suspenseful": "fear",
                "Sad": "sadness"
            }
            if tone in emotion_map:
                col = emotion_map[tone]
                print(f"  - {tone} (maps to '{col}' column)")
            else:
                print(f"  - {tone}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in app integration: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_filtering():
    """Test that filtering actually works"""
    print("\n" + "=" * 70)
    print("FILTERING TEST")
    print("=" * 70)
    
    try:
        books = pd.read_csv(config.DATA_DIR / "books_with_emotions.csv")
        
        # Test category filtering
        print("\n1. Category Filtering Test:")
        fiction_books = books[books["simple_categories"] == "Fiction"]
        print(f"   Fiction books: {len(fiction_books)} / {len(books)}")
        
        nonfiction_books = books[books["simple_categories"] == "Nonfiction"]
        print(f"   Nonfiction books: {len(nonfiction_books)} / {len(books)}")
        
        # Test emotion sorting
        print("\n2. Emotion Sorting Test:")
        top_joy = books.nlargest(5, "joy")[["title", "joy"]]
        print("   Top 5 'joyful' books:")
        for idx, row in top_joy.iterrows():
            print(f"     - {row['title']}: {row['joy']:.4f}")
        
        top_fear = books.nlargest(5, "fear")[["title", "fear"]]
        print("\n   Top 5 'suspenseful' books:")
        for idx, row in top_fear.iterrows():
            print(f"     - {row['title']}: {row['fear']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in filtering test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🔍 CATEGORY & EMOTION SYSTEM TEST\n")
    
    tests = [
        ("Data Loading", test_data_loading),
        ("App Integration", test_app_integration),
        ("Filtering Logic", test_filtering),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Categories and Emotions are working!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
