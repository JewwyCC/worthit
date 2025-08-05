#!/usr/bin/env python3
"""
Basketball Shoe Recommendation System
Version: 2.0
Last Updated: 2025-01-02

Main entry point for the hybrid AI system that:
1. Uses a pre-trained LLM/SLM as its reasoning core
2. Augments knowledge via RAG from a basketball shoe database
3. Performs autonomous web searches for missing/updated info
4. Self-improves by adding verified search results to RAG
"""

import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    parser = argparse.ArgumentParser(
        description="Basketball Shoe Recommendation System v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the API server
  python main.py serve

  # Migrate existing data to RAG format
  python main.py migrate

  # Test the system with a sample query
  python main.py test "Best shoes for a 6'2\" guard with knee pain under $150?"

  # Scrape all sources for comprehensive database
  python main.py scrape-all

  # Scrape specific shoe models
  python main.py scrape-specific --shoes "Nike LeBron 21" "Adidas Dame 8"

  # Scrape with custom limits (YouTube only)
  python main.py scrape-all --max-videos 5 --skip-reddit --skip-runrepeat

  # Run the original scraper and migrate data
  python main.py scrape
        """
    )
    
    parser.add_argument(
        'command',
        choices=['serve', 'migrate', 'test', 'scrape', 'scrape-all', 'scrape-specific'],
        help='Command to run'
    )
    
    parser.add_argument(
        '--query',
        type=str,
        help='Test query (for test command)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port for API server (default: 8000)'
    )
    
    parser.add_argument(
        '--shoes',
        type=str,
        nargs='+',
        help='Specific shoe models to scrape (for scrape-specific command)'
    )
    
    parser.add_argument(
        '--max-videos',
        type=int,
        default=8,
        help='Max YouTube videos per shoe model (default: 8)'
    )
    
    parser.add_argument(
        '--max-posts',
        type=int,
        default=15,
        help='Max Reddit posts per shoe model (default: 15)'
    )
    
    parser.add_argument(
        '--skip-youtube',
        action='store_true',
        help='Skip YouTube scraping'
    )
    
    parser.add_argument(
        '--skip-reddit',
        action='store_true',
        help='Skip Reddit scraping'
    )
    
    parser.add_argument(
        '--skip-runrepeat',
        action='store_true',
        help='Skip RunRepeat scraping'
    )
    
    args = parser.parse_args()
    
    if args.command == 'serve':
        serve_api(args.port)
    elif args.command == 'migrate':
        migrate_data()
    elif args.command == 'test':
        test_system(args.query)
    elif args.command == 'scrape':
        run_scraper()
    elif args.command == 'scrape-all':
        scrape_all_sources(args)
    elif args.command == 'scrape-specific':
        scrape_specific_shoes(args)

def serve_api(port: int):
    """Start the FastAPI server"""
    print("🚀 Starting Basketball Shoe Recommendation System API...")
    print(f"📡 Server will be available at http://localhost:{port}")
    print("📚 API documentation at http://localhost:{port}/docs")
    
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

def migrate_data():
    """Migrate existing data to RAG format"""
    print("🔄 Migrating existing data to RAG format...")
    
    try:
        from src.data.migrate_data import migrate_existing_data
        migrate_existing_data()
        print("✅ Data migration completed successfully!")
    except Exception as e:
        print(f"❌ Error during data migration: {e}")
        sys.exit(1)

def test_system(query: str):
    """Test the system with a sample query"""
    if not query:
        query = "Best basketball shoes for guards under $150"
    
    print(f"🧪 Testing system with query: '{query}'")
    
    try:
        from src.core.models import UserQuery, Playstyle
        from src.core.router import QueryRouter
        from src.rag.vector_db import VectorDatabase
        from src.web.search import WebSearch
        from src.llm.reasoning import LLMReasoning
        
        # Initialize components
        router = QueryRouter()
        vector_db = VectorDatabase()
        web_search = WebSearch()
        llm_reasoning = LLMReasoning()
        
        # Create user query
        user_query = UserQuery(query=query)
        
        # Route query
        route_type = router.route_query(user_query)
        print(f"🔍 Query routed to: {route_type}")
        
        # Get RAG documents
        filters = router.get_search_filters(user_query)
        rag_documents = vector_db.similarity_search(query, k=3, filters=filters)
        print(f"📚 Retrieved {len(rag_documents)} documents from RAG")
        
        # Web search if needed
        search_results = None
        if route_type in ["web_search", "hybrid"]:
            search_results = web_search.search(query)
            print(f"🌐 Retrieved {len(search_results)} web search results")
        
        # Generate recommendation
        response = llm_reasoning.generate_recommendation(
            query=user_query,
            rag_documents=rag_documents,
            search_results=search_results
        )
        
        # Display results
        print("\n" + "="*50)
        print("🎯 RECOMMENDATION RESULTS")
        print("="*50)
        print(f"Confidence Score: {response.confidence_score:.2f}")
        print(f"Search Used: {response.search_used}")
        print(f"Sources: {len(response.sources)}")
        
        print("\n📝 Reasoning:")
        print(response.reasoning)
        
        print(f"\n🔗 Sources:")
        for i, source in enumerate(response.sources[:3], 1):
            print(f"  {i}. {source}")
        
    except Exception as e:
        print(f"❌ Error testing system: {e}")
        sys.exit(1)

def run_scraper():
    """Run the original scraper and migrate data"""
    print("🕷️ Running original scraper...")
    
    try:
        # Import and run the original scraper
        import importlib.util
        
        # Try to import the original scraper
        if os.path.exists("import requests.py"):
            spec = importlib.util.spec_from_file_location("scraper", "import requests.py")
            scraper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(scraper)
            
            # Run the main execution
            if hasattr(scraper, '__main__'):
                print("✅ Original scraper completed")
            else:
                print("⚠️ Original scraper doesn't have main execution block")
        
        # Migrate the scraped data
        print("🔄 Migrating scraped data...")
        migrate_data()
        
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        sys.exit(1)

def scrape_all_sources(args):
    """Scrape all sources with comprehensive shoe list"""
    print("🚀 Starting comprehensive basketball shoe scraping...")
    
    try:
        from src.scrapers.master_scraper import MasterScraper
        import os
        
        # Initialize master scraper
        scraper = MasterScraper(
            reddit_client_id=os.getenv('REDDIT_CLIENT_ID'),
            reddit_client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            reddit_user_agent='BasketballShoeBot/2.0'
        )
        
        # Run scraping
        results = scraper.scrape_all_sources(
            youtube_videos_per_model=args.max_videos,
            reddit_posts_per_model=args.max_posts,
            include_youtube=not args.skip_youtube,
            include_reddit=not args.skip_reddit,
            include_runrepeat=not args.skip_runrepeat
        )
        
        print(f"✅ Scraping completed! Collected {results['total_reviews_collected']} reviews")
        
    except Exception as e:
        print(f"❌ Error in comprehensive scraping: {e}")
        sys.exit(1)

def scrape_specific_shoes(args):
    """Scrape specific shoe models"""
    if not args.shoes:
        print("❌ Error: --shoes argument required for scrape-specific command")
        print("Example: python main.py scrape-specific --shoes 'Nike LeBron 21' 'Adidas Dame 8'")
        sys.exit(1)
    
    print(f"🎯 Scraping specific shoes: {args.shoes}")
    
    try:
        from src.scrapers.master_scraper import MasterScraper
        import os
        
        # Initialize master scraper
        scraper = MasterScraper(
            reddit_client_id=os.getenv('REDDIT_CLIENT_ID'),
            reddit_client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            reddit_user_agent='BasketballShoeBot/2.0'
        )
        
        # Run scraping for specific shoes
        results = scraper.scrape_specific_shoes(
            shoe_models=args.shoes,
            youtube_videos_per_model=args.max_videos,
            reddit_posts_per_model=args.max_posts,
            include_youtube=not args.skip_youtube,
            include_reddit=not args.skip_reddit,
            include_runrepeat=not args.skip_runrepeat
        )
        
        print(f"✅ Specific scraping completed! Collected {results['total_reviews_collected']} reviews")
        
    except Exception as e:
        print(f"❌ Error in specific scraping: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 