import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from tqdm import tqdm

from src.scrapers.youtube_scraper import YouTubeScraper
from src.scrapers.runrepeat_scraper import RunRepeatScraper
from src.scrapers.reddit_scraper import RedditScraper
from src.rag.vector_db import VectorDatabase
from src.core.models import ShoeReview, Source


class MasterScraper:
    """Master scraper that coordinates all data sources and feeds RAG database"""
    
    def __init__(self, 
                 reddit_client_id: str = None,
                 reddit_client_secret: str = None,
                 reddit_user_agent: str = None):
        
        # Initialize scrapers
        self.youtube_scraper = YouTubeScraper()
        self.runrepeat_scraper = RunRepeatScraper()
        self.reddit_scraper = RedditScraper(
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            user_agent=reddit_user_agent
        )
        
        # Initialize vector database
        self.vector_db = VectorDatabase()
        
        # Popular basketball shoe models to scrape
        self.default_shoe_models = [
            "Nike LeBron 21",
            "Nike KD 16", 
            "Nike GT Jump 3",
            "Nike GT Cut 3",
            "Nike Zion 3",
            "Adidas Harden Vol 7",
            "Adidas Dame 8",
            "Adidas Trae Young 3",
            "Jordan Luka 2",
            "Jordan Zion 3",
            "Jordan Tatum 2",
            "Under Armour Curry 11",
            "Under Armour Embiid 2",
            "Puma MB.03",
            "Puma All-Pro Nitro",
            "New Balance Two WXY v4",
            "ANTA KT 9",
            "Peak Lou Williams",
            "Li-Ning Way of Wade 11",
            "Nike Ja 1"
        ]
    
    def scrape_all_sources(self, 
                          shoe_models: Optional[List[str]] = None,
                          youtube_videos_per_model: int = 8,
                          reddit_posts_per_model: int = 15,
                          include_youtube: bool = True,
                          include_runrepeat: bool = True,
                          include_reddit: bool = True) -> Dict[str, Any]:
        """
        Scrape all sources and populate RAG database
        
        Args:
            shoe_models: List of shoe models to scrape (uses default if None)
            youtube_videos_per_model: Max YouTube videos per model
            reddit_posts_per_model: Max Reddit posts per model
            include_youtube: Whether to scrape YouTube
            include_runrepeat: Whether to scrape RunRepeat
            include_reddit: Whether to scrape Reddit
            
        Returns:
            Dictionary with scraping results and statistics
        """
        if shoe_models is None:
            shoe_models = self.default_shoe_models
        
        print(f"🚀 Starting comprehensive scraping for {len(shoe_models)} shoe models...")
        print(f"📊 Sources: YouTube({include_youtube}), RunRepeat({include_runrepeat}), Reddit({include_reddit})")
        
        all_reviews = []
        source_stats = {}
        
        # 1. Scrape YouTube
        if include_youtube:
            print("\n" + "="*60)
            print("🎥 SCRAPING YOUTUBE REVIEWS")
            print("="*60)
            
            try:
                youtube_reviews = self.youtube_scraper.scrape_shoe_reviews(
                    shoe_models, 
                    max_videos_per_model=youtube_videos_per_model
                )
                all_reviews.extend(youtube_reviews)
                source_stats['youtube'] = {
                    'total_reviews': len(youtube_reviews),
                    'reviews_per_model': len(youtube_reviews) / len(shoe_models) if shoe_models else 0
                }
                print(f"✅ YouTube scraping completed: {len(youtube_reviews)} reviews")
                
            except Exception as e:
                print(f"❌ YouTube scraping failed: {e}")
                source_stats['youtube'] = {'error': str(e)}
        
        # 2. Scrape RunRepeat
        if include_runrepeat:
            print("\n" + "="*60)
            print("📊 SCRAPING RUNREPEAT REVIEWS")
            print("="*60)
            
            try:
                runrepeat_reviews = self.runrepeat_scraper.scrape_shoe_reviews(shoe_models)
                all_reviews.extend(runrepeat_reviews)
                source_stats['runrepeat'] = {
                    'total_reviews': len(runrepeat_reviews),
                    'reviews_per_model': len(runrepeat_reviews) / len(shoe_models) if shoe_models else 0
                }
                print(f"✅ RunRepeat scraping completed: {len(runrepeat_reviews)} reviews")
                
            except Exception as e:
                print(f"❌ RunRepeat scraping failed: {e}")
                source_stats['runrepeat'] = {'error': str(e)}
        
        # 3. Scrape Reddit
        if include_reddit:
            print("\n" + "="*60)
            print("💬 SCRAPING REDDIT DISCUSSIONS")
            print("="*60)
            
            try:
                reddit_reviews = self.reddit_scraper.scrape_shoe_discussions(
                    shoe_models,
                    posts_per_model=reddit_posts_per_model
                )
                all_reviews.extend(reddit_reviews)
                source_stats['reddit'] = {
                    'total_reviews': len(reddit_reviews),
                    'reviews_per_model': len(reddit_reviews) / len(shoe_models) if shoe_models else 0
                }
                print(f"✅ Reddit scraping completed: {len(reddit_reviews)} discussions")
                
            except Exception as e:
                print(f"❌ Reddit scraping failed: {e}")
                source_stats['reddit'] = {'error': str(e)}
        
        # 4. Add to RAG database
        print("\n" + "="*60)
        print("🧠 FEEDING DATA TO RAG DATABASE")
        print("="*60)
        
        if all_reviews:
            try:
                print(f"📝 Adding {len(all_reviews)} reviews to vector database...")
                self.vector_db.add_from_reviews(all_reviews)
                
                # Get database stats
                db_stats = self.vector_db.get_stats()
                print(f"✅ RAG database updated: {db_stats['total_documents']} total documents")
                
            except Exception as e:
                print(f"❌ Error adding to RAG database: {e}")
                db_stats = {'error': str(e)}
        else:
            print("⚠️ No reviews collected to add to database")
            db_stats = {'total_documents': 0}
        
        # 5. Generate summary report
        total_reviews = len(all_reviews)
        results = {
            'timestamp': datetime.now().isoformat(),
            'shoe_models_scraped': shoe_models,
            'total_reviews_collected': total_reviews,
            'source_breakdown': source_stats,
            'database_stats': db_stats,
            'reviews_by_source': self._analyze_reviews_by_source(all_reviews),
            'reviews_by_shoe': self._analyze_reviews_by_shoe(all_reviews)
        }
        
        self._print_summary_report(results)
        return results
    
    def scrape_specific_shoes(self, shoe_models: List[str], **kwargs) -> Dict[str, Any]:
        """Scrape specific shoe models"""
        return self.scrape_all_sources(shoe_models=shoe_models, **kwargs)
    
    def scrape_latest_releases(self, year: int = 2024) -> Dict[str, Any]:
        """Scrape latest basketball shoe releases for a given year"""
        latest_models = [
            f"Nike LeBron {year-2003}",  # LeBron series
            f"Nike KD {year-2009}",      # KD series 
            f"Adidas Dame {year-2015}",  # Dame series
            f"Jordan Luka {year-2021}",  # Luka series
            "Nike GT Jump 3",
            "Nike GT Cut 3",
            "Under Armour Curry 11",
            "Puma MB.03"
        ]
        
        print(f"🔥 Scraping latest {year} basketball shoe releases...")
        return self.scrape_all_sources(shoe_models=latest_models)
    
    def update_existing_shoes(self, days_old: int = 30) -> Dict[str, Any]:
        """Update reviews for shoes that haven't been updated recently"""
        # This would check database for shoes older than X days
        # For now, just scrape the default list
        print(f"🔄 Updating shoes older than {days_old} days...")
        return self.scrape_all_sources()
    
    def _analyze_reviews_by_source(self, reviews: List[ShoeReview]) -> Dict[str, int]:
        """Analyze reviews by source"""
        source_counts = {}
        for review in reviews:
            source = review.source.value
            source_counts[source] = source_counts.get(source, 0) + 1
        return source_counts
    
    def _analyze_reviews_by_shoe(self, reviews: List[ShoeReview]) -> Dict[str, int]:
        """Analyze reviews by shoe model"""
        shoe_counts = {}
        for review in reviews:
            shoe = review.shoe_model
            shoe_counts[shoe] = shoe_counts.get(shoe, 0) + 1
        return shoe_counts
    
    def _print_summary_report(self, results: Dict[str, Any]):
        """Print a comprehensive summary report"""
        print("\n" + "="*80)
        print("📊 SCRAPING SUMMARY REPORT")
        print("="*80)
        
        print(f"⏰ Completed at: {results['timestamp']}")
        print(f"👟 Shoe models scraped: {len(results['shoe_models_scraped'])}")
        print(f"📝 Total reviews collected: {results['total_reviews_collected']}")
        
        print("\n📋 Source Breakdown:")
        for source, stats in results['source_breakdown'].items():
            if 'error' in stats:
                print(f"  ❌ {source.upper()}: {stats['error']}")
            else:
                print(f"  ✅ {source.upper()}: {stats['total_reviews']} reviews "
                      f"({stats['reviews_per_model']:.1f} avg per model)")
        
        print("\n🧠 Database Status:")
        db_stats = results['database_stats']
        if 'error' in db_stats:
            print(f"  ❌ Error: {db_stats['error']}")
        else:
            print(f"  📚 Total documents: {db_stats.get('total_documents', 0)}")
            print(f"  🔍 Index size: {db_stats.get('index_size', 0)}")
            print(f"  📐 Embedding dimension: {db_stats.get('embedding_dimension', 0)}")
        
        print("\n🎯 Top Reviewed Shoes:")
        reviews_by_shoe = results['reviews_by_shoe']
        top_shoes = sorted(reviews_by_shoe.items(), key=lambda x: x[1], reverse=True)[:5]
        for shoe, count in top_shoes:
            print(f"  📈 {shoe}: {count} reviews")
        
        print("\n🚀 System Ready!")
        print("Next steps:")
        print("  1. Start API server: python main.py serve")
        print("  2. Test system: python main.py test 'Best shoes for guards?'")
        print("  3. View docs: http://localhost:8000/docs")
        print("="*80)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get current database statistics"""
        return self.vector_db.get_stats()
    
    def search_database(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the RAG database directly"""
        documents = self.vector_db.similarity_search(query, k)
        return [
            {
                'id': doc.id,
                'text': doc.text[:200] + "..." if len(doc.text) > 200 else doc.text,
                'metadata': doc.metadata
            }
            for doc in documents
        ]


# Convenience function for standalone usage
def scrape_basketball_shoes(shoe_models: Optional[List[str]] = None,
                          reddit_client_id: str = None,
                          reddit_client_secret: str = None,
                          **kwargs) -> Dict[str, Any]:
    """
    Convenience function to scrape basketball shoe data
    
    Usage:
        results = scrape_basketball_shoes(['Nike LeBron 21', 'Adidas Dame 8'])
    """
    scraper = MasterScraper(
        reddit_client_id=reddit_client_id,
        reddit_client_secret=reddit_client_secret
    )
    
    return scraper.scrape_all_sources(shoe_models=shoe_models, **kwargs) 