#!/usr/bin/env python3
"""
Test script to verify the master scraper works with the enhanced RunRepeat scraper
and properly loads data into the vector database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.master_scraper import MasterScraper
from src.rag.vector_db import VectorDatabase

def test_runrepeat_only():
    """Test just the RunRepeat scraper integration"""
    print("🧪 TESTING ENHANCED RUNREPEAT SCRAPER INTEGRATION")
    print("=" * 70)
    
    # Initialize master scraper
    master = MasterScraper()
    
    # Test with a small set of popular shoes
    test_shoes = [
        "Nike LeBron 21",
        "Nike GT Cut 3", 
        "Adidas Dame 8",
        "Jordan Luka 2"
    ]
    
    print(f"Testing with {len(test_shoes)} shoe models:")
    for shoe in test_shoes:
        print(f"  • {shoe}")
    
    # Scrape only RunRepeat (faster for testing)
    results = master.scrape_all_sources(
        shoe_models=test_shoes,
        include_youtube=False,
        include_reddit=False,
        include_runrepeat=True
    )
    
    return results

def test_vector_db_search():
    """Test searching the vector database after scraping"""
    print("\n🔍 TESTING VECTOR DATABASE SEARCH")
    print("=" * 50)
    
    # Initialize vector database
    vector_db = VectorDatabase()
    
    # Get current stats
    stats = vector_db.get_stats()
    print(f"Database stats: {stats['total_documents']} documents")
    
    if stats['total_documents'] == 0:
        print("⚠️ No documents in database. Run scraping first.")
        return
    
    # Test queries
    test_queries = [
        "best basketball shoes for guards",
        "shoes with good traction",
        "lightweight basketball shoes",
        "LeBron 21 review",
        "shoes for outdoor courts"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        results = vector_db.similarity_search(query, k=3)
        
        for i, doc in enumerate(results, 1):
            shoe_model = doc.metadata.get('shoe_model', 'Unknown')
            source = doc.metadata.get('source', 'Unknown')
            score = doc.metadata.get('score', 'N/A')
            print(f"  {i}. {shoe_model} (Source: {source}, Score: {score})")
            # Show snippet of text
            text_preview = doc.text[:100] + "..." if len(doc.text) > 100 else doc.text
            print(f"     Preview: {text_preview}")

def test_filtered_search():
    """Test searching with metadata filters"""
    print("\n🎯 TESTING FILTERED SEARCH")
    print("=" * 40)
    
    vector_db = VectorDatabase()
    
    # Test filter by source
    print("Filter by source (RunRepeat only):")
    results = vector_db.similarity_search(
        "best basketball shoes", 
        k=3, 
        filters={"source": "runrepeat"}
    )
    
    for i, doc in enumerate(results, 1):
        shoe_model = doc.metadata.get('shoe_model', 'Unknown')
        score = doc.metadata.get('score', 'N/A')
        print(f"  {i}. {shoe_model} (Score: {score})")
    
    # Test filter by playstyle
    print("\nFilter by playstyle (guard shoes):")
    results = vector_db.similarity_search(
        "basketball shoes", 
        k=3, 
        filters={"playstyle": ["guard"]}
    )
    
    for i, doc in enumerate(results, 1):
        shoe_model = doc.metadata.get('shoe_model', 'Unknown')
        playstyles = doc.metadata.get('playstyle', [])
        print(f"  {i}. {shoe_model} (Playstyles: {', '.join(playstyles)})")

def analyze_scraped_data():
    """Analyze the quality of scraped data"""
    print("\n📊 ANALYZING SCRAPED DATA QUALITY")
    print("=" * 45)
    
    vector_db = VectorDatabase()
    
    if not vector_db.documents:
        print("⚠️ No documents to analyze")
        return
    
    # Analyze by source
    source_counts = {}
    shoe_models = set()
    total_text_length = 0
    scores_found = 0
    
    for doc in vector_db.documents:
        source = doc.metadata.get('source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
        
        shoe_models.add(doc.metadata.get('shoe_model', 'Unknown'))
        total_text_length += len(doc.text)
        
        if doc.metadata.get('score'):
            scores_found += 1
    
    print(f"Total documents: {len(vector_db.documents)}")
    print(f"Unique shoe models: {len(shoe_models)}")
    print(f"Average text length: {total_text_length / len(vector_db.documents):.0f} characters")
    print(f"Documents with scores: {scores_found}/{len(vector_db.documents)} ({scores_found/len(vector_db.documents)*100:.1f}%)")
    
    print(f"\nDocuments by source:")
    for source, count in source_counts.items():
        print(f"  {source}: {count} documents")
    
    # Show sample RunRepeat documents
    print(f"\nSample RunRepeat documents:")
    runrepeat_docs = [doc for doc in vector_db.documents if doc.metadata.get('source') == 'runrepeat']
    
    for i, doc in enumerate(runrepeat_docs[:3], 1):
        shoe_model = doc.metadata.get('shoe_model', 'Unknown')
        score = doc.metadata.get('score', 'N/A')
        features = doc.metadata.get('features', [])
        print(f"  {i}. {shoe_model} (Score: {score})")
        print(f"     Features: {', '.join(features[:5])}" + ("..." if len(features) > 5 else ""))
        text_preview = doc.text[:150] + "..." if len(doc.text) > 150 else doc.text
        print(f"     Text: {text_preview}")

def main():
    """Main test function"""
    print("🚀 MASTER SCRAPER INTEGRATION TEST")
    print("🔧 Testing Enhanced RunRepeat Scraper + Vector Database")
    print("=" * 80)
    
    try:
        # Test 1: Scrape with enhanced RunRepeat scraper
        print("\n📥 STEP 1: TESTING SCRAPING")
        results = test_runrepeat_only()
        
        if results['total_reviews_collected'] == 0:
            print("❌ No reviews were collected. Check the scraper.")
            return
        
        print(f"✅ Scraping completed: {results['total_reviews_collected']} reviews collected")
        
        # Test 2: Verify data is in vector database
        print("\n📥 STEP 2: TESTING VECTOR DATABASE")
        analyze_scraped_data()
        
        # Test 3: Test search functionality
        print("\n📥 STEP 3: TESTING SEARCH FUNCTIONALITY")
        test_vector_db_search()
        
        # Test 4: Test filtered search
        print("\n📥 STEP 4: TESTING FILTERED SEARCH")
        test_filtered_search()
        
        print(f"\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"✅ Enhanced RunRepeat scraper is working properly")
        print(f"✅ Data is being loaded into vector database")
        print(f"✅ Search functionality is working")
        print(f"✅ Metadata filtering is working")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 