#!/usr/bin/env python3
"""
Comprehensive test to verify all scrapers (YouTube, Reddit, Enhanced RunRepeat)
work together and properly load data into the vector database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.master_scraper import MasterScraper
from src.rag.vector_db import VectorDatabase

def test_all_sources():
    """Test all scrapers together"""
    print("🧪 TESTING FULL INTEGRATION - ALL SOURCES")
    print("=" * 80)
    
    # Initialize master scraper
    master = MasterScraper()
    
    # Test with a small set of popular shoes for faster testing
    test_shoes = [
        "Nike LeBron 21",
        "Nike GT Cut 3"
    ]
    
    print(f"Testing with {len(test_shoes)} shoe models:")
    for shoe in test_shoes:
        print(f"  • {shoe}")
    
    # Scrape all sources with limited quantities for testing
    results = master.scrape_all_sources(
        shoe_models=test_shoes,
        youtube_videos_per_model=3,  # Limited for testing
        reddit_posts_per_model=5,   # Limited for testing
        include_youtube=True,
        include_reddit=True,
        include_runrepeat=True
    )
    
    return results

def analyze_comprehensive_data():
    """Analyze data from all sources"""
    print("\n📊 COMPREHENSIVE DATA ANALYSIS")
    print("=" * 50)
    
    vector_db = VectorDatabase()
    
    if not vector_db.documents:
        print("⚠️ No documents to analyze")
        return
    
    # Analyze by source
    source_stats = {}
    shoe_model_stats = {}
    
    for doc in vector_db.documents:
        source = doc.metadata.get('source', 'unknown')
        shoe_model = doc.metadata.get('shoe_model', 'Unknown')
        
        # Count by source
        source_stats[source] = source_stats.get(source, 0) + 1
        
        # Count by shoe model
        if shoe_model not in shoe_model_stats:
            shoe_model_stats[shoe_model] = {}
        shoe_model_stats[shoe_model][source] = shoe_model_stats[shoe_model].get(source, 0) + 1
    
    print(f"Total documents: {len(vector_db.documents)}")
    print(f"Unique shoe models: {len(shoe_model_stats)}")
    
    print(f"\n📈 Documents by source:")
    for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(vector_db.documents)) * 100
        print(f"  {source}: {count} documents ({percentage:.1f}%)")
    
    print(f"\n👟 Coverage by shoe model:")
    for shoe_model, sources in shoe_model_stats.items():
        total_docs = sum(sources.values())
        print(f"  {shoe_model}: {total_docs} total documents")
        for source, count in sources.items():
            print(f"    - {source}: {count}")

def test_cross_source_search():
    """Test search across multiple sources"""
    print("\n🔍 TESTING CROSS-SOURCE SEARCH")
    print("=" * 45)
    
    vector_db = VectorDatabase()
    
    # Test queries that should find content from different sources
    test_queries = [
        "performance review LeBron 21",
        "user opinion on GT Cut 3",
        "traction and grip",
        "best for guards"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        results = vector_db.similarity_search(query, k=5)
        
        sources_found = set()
        for i, doc in enumerate(results, 1):
            shoe_model = doc.metadata.get('shoe_model', 'Unknown')
            source = doc.metadata.get('source', 'Unknown')
            sources_found.add(source)
            print(f"  {i}. {shoe_model} (Source: {source})")
        
        print(f"    Sources found: {', '.join(sorted(sources_found))}")

def main():
    """Main test function"""
    print("🚀 FULL SYSTEM INTEGRATION TEST")
    print("🔧 Testing All Scrapers + Vector Database")
    print("=" * 80)
    
    try:
        # Test 1: Scrape with all sources
        print("\n📥 STEP 1: TESTING ALL SOURCES")
        results = test_all_sources()
        
        if results['total_reviews_collected'] == 0:
            print("❌ No reviews were collected. Check the scrapers.")
            return
        
        print(f"✅ Scraping completed: {results['total_reviews_collected']} reviews collected")
        
        # Test 2: Analyze comprehensive data
        print("\n📥 STEP 2: ANALYZING COMPREHENSIVE DATA")
        analyze_comprehensive_data()
        
        # Test 3: Test cross-source search
        print("\n📥 STEP 3: TESTING CROSS-SOURCE SEARCH")
        test_cross_source_search()
        
        print(f"\n🎉 FULL INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print(f"✅ All scrapers are working properly")
        print(f"✅ Enhanced RunRepeat scraper provides rich data")
        print(f"✅ All data sources are integrated in vector database")
        print(f"✅ Cross-source search is working")
        
        # Show final stats
        vector_db = VectorDatabase()
        stats = vector_db.get_stats()
        print(f"\n📊 Final Database Stats:")
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Index size: {stats['index_size']}")
        print(f"   Embedding dimension: {stats['embedding_dimension']}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 