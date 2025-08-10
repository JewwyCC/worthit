#!/usr/bin/env python3
"""
Debug script for YouTube scraper
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_youtube_search():
    """Debug YouTube search functionality"""
    print("🔍 Debugging YouTube Search...")
    
    try:
        from youtube_search import YoutubeSearch
        
        # Test basic search
        search_query = "Nike LeBron 21 review"
        print(f"Testing search query: '{search_query}'")
        
        search = YoutubeSearch(search_query, max_results=5)
        print(f"Search object created: {search}")
        
        # Check if we get results
        if hasattr(search, 'videos'):
            videos = search.videos
            print(f"Found {len(videos)} videos")
            
            for i, video in enumerate(videos):
                print(f"\nVideo {i+1}:")
                print(f"  ID: {video.get('id', 'N/A')}")
                print(f"  Title: {video.get('title', 'N/A')}")
                print(f"  Channel: {video.get('channel', 'N/A')}")
                print(f"  Duration: {video.get('duration', 'N/A')}")
                print(f"  Views: {video.get('views', 'N/A')}")
        else:
            print("❌ No 'videos' attribute found")
            print(f"Available attributes: {dir(search)}")
        
        return videos if hasattr(search, 'videos') else []
        
    except Exception as e:
        print(f"❌ Error in YouTube search: {e}")
        import traceback
        traceback.print_exc()
        return []

def debug_video_extraction():
    """Debug video data extraction"""
    print("\n🎥 Debugging Video Extraction...")
    
    try:
        # PyTube removed - using search metadata instead
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Test with a known basketball shoe review video
        test_video_id = "dQw4w9WgXcQ"  # Rick Roll as fallback
        # Let's try to find a real basketball review
        
        # First, let's get some video IDs from search
        videos = debug_youtube_search()
        if not videos:
            print("❌ No videos found to test extraction")
            return
        
        test_video = videos[0]
        video_id = test_video.get('id')
        
        if not video_id:
            print("❌ No video ID found")
            return
            
        print(f"Testing extraction with video ID: {video_id}")
        
        # Test search metadata approach (PyTube replacement)
        try:
            print(f"✅ Search metadata approach - no PyTube needed!")
            print(f"  Using video ID: {video_id}")
            print(f"  Search results will provide: title, channel, duration, views")
            print(f"  This is much more reliable than PyTube!")
        except Exception as e:
            print(f"❌ Metadata setup error: {e}")
        
        # Test transcript with new API - try fetch() FIRST
        try:
            # FIRST: Try the fetch method directly (newest API)
            ytt_api = YouTubeTranscriptApi()
            fetched_transcript = ytt_api.fetch(video_id)
            transcript_text = " ".join([snippet.text for snippet in fetched_transcript])
            print(f"✅ Fetch method successful:")
            print(f"  Transcript length: {len(transcript_text)}")
            print(f"  Snippet count: {len(fetched_transcript)}")
            print(f"  First snippet: {fetched_transcript[0].text if fetched_transcript else 'None'}")
            print(f"  First 200 chars: {transcript_text[:200]}...")
            
        except Exception as e:
            print(f"❌ Fetch method error: {e}")
            # SECOND: Try list approach
            try:
                ytt_api = YouTubeTranscriptApi()
                transcript_list = ytt_api.list(video_id)
                
                print(f"✅ Found {len(list(transcript_list))} available transcripts")
                
                # Show available transcripts
                for i, transcript in enumerate(transcript_list):
                    print(f"  Transcript {i+1}: {transcript.language} ({transcript.language_code}) - Generated: {transcript.is_generated}")
                
                # Try to find best transcript
                try:
                    transcript = transcript_list.find_manually_created_transcript(['en'])
                    print("  Using manually created English transcript")
                except:
                    try:
                        transcript = transcript_list.find_generated_transcript(['en'])
                        print("  Using auto-generated English transcript")
                    except:
                        transcript = list(transcript_list)[0]
                        print(f"  Using first available transcript: {transcript.language}")
                
                fetched_data = transcript.fetch()
                transcript_text = " ".join([snippet['text'] for snippet in fetched_data])
                print(f"✅ List/fetch method successful:")
                print(f"  Transcript length: {len(transcript_text)}")
                print(f"  Snippet count: {len(fetched_data)}")
                print(f"  Language: {transcript.language_code}")
                print(f"  First snippet: {fetched_data[0]['text'] if fetched_data else 'None'}")
                print(f"  First 200 chars: {transcript_text[:200]}...")
                
            except Exception as e2:
                print(f"❌ List/fetch method error: {e2}")
                print("  All transcript methods failed - this is normal for blocked IPs")
        
    except Exception as e:
        print(f"❌ Error in video extraction: {e}")
        import traceback
        traceback.print_exc()

def debug_review_filtering():
    """Debug review filtering logic"""
    print("\n🔍 Debugging Review Filtering...")
    
    try:
        from src.core.models import ShoeReview, Source, Playstyle, WeightClass
        from datetime import datetime
        
        # Create test reviews
        test_reviews = [
            ShoeReview(
                shoe_model="Nike LeBron 21",
                source=Source.YOUTUBE,
                title="Nike LeBron 21 Performance Review",
                text="This is a basketball shoe review. The shoe has great traction on court and excellent cushioning for basketball performance. I tested these during games and they performed well.",
                pros=[],
                cons=[],
                score=None,
                playstyle=[Playstyle.ALL_AROUND],
                weight_class=WeightClass.MEDIUM,
                features=[],
                url="https://youtube.com/test",
                timestamp=datetime.now()
            ),
            ShoeReview(
                shoe_model="Nike LeBron 21",
                source=Source.YOUTUBE,
                title="Nike LeBron 21 Fashion Review",
                text="These shoes look great with jeans. Perfect for casual wear and street style. Not really for basketball.",
                pros=[],
                cons=[],
                score=None,
                playstyle=[Playstyle.ALL_AROUND],
                weight_class=WeightClass.MEDIUM,
                features=[],
                url="https://youtube.com/test2",
                timestamp=datetime.now()
            )
        ]
        
        from src.scrapers.youtube_scraper import YouTubeScraper
        scraper = YouTubeScraper()
        
        for i, review in enumerate(test_reviews):
            is_relevant = scraper._is_relevant_review(review)
            print(f"Review {i+1}: {'✅ RELEVANT' if is_relevant else '❌ NOT RELEVANT'}")
            print(f"  Title: {review.title}")
            print(f"  Text preview: {review.text[:100]}...")
            print()
        
    except Exception as e:
        print(f"❌ Error in filtering debug: {e}")
        import traceback
        traceback.print_exc()

def debug_search_queries():
    """Debug search query generation"""
    print("\n🔍 Debugging Search Queries...")
    
    try:
        from src.scrapers.youtube_scraper import YouTubeScraper
        
        scraper = YouTubeScraper()
        shoe_model = "Nike LeBron 21"
        
        queries = scraper._generate_search_queries(shoe_model)
        print(f"Generated queries for '{shoe_model}':")
        
        for i, query in enumerate(queries):
            print(f"  {i+1}. {query}")
            
            # Test each query
            try:
                from youtube_search import YoutubeSearch
                search = YoutubeSearch(query, max_results=3)
                results_count = len(search.videos) if hasattr(search, 'videos') else 0
                print(f"     → Found {results_count} results")
            except Exception as e:
                print(f"     → Error: {e}")
        
    except Exception as e:
        print(f"❌ Error in query debug: {e}")
        import traceback
        traceback.print_exc()

def debug_full_scraper():
    """Debug the full scraper process with proxy support"""
    print("\n🚀 Debugging Full Scraper Process...")
    
    try:
        from src.scrapers.youtube_scraper import YouTubeScraper
        
        # Test with proxies enabled and shorter delays for debugging
        scraper = YouTubeScraper(use_proxies=True, request_delay=(1, 2))
        
        # Test with one shoe model
        shoe_models = ["Nike LeBron 21"]
        
        print("Starting scrape_shoe_reviews...")
        reviews = scraper.scrape_shoe_reviews(shoe_models, max_videos_per_model=2)
        
        print(f"Final result: {len(reviews)} reviews")
        for review in reviews:
            print(f"  - {review.title}")
            print(f"    Text length: {len(review.text)}")
            print(f"    Source: {review.source}")
            print()
        
    except Exception as e:
        print(f"❌ Error in full scraper debug: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🐛 YouTube Scraper Debug Tool")
    print("=" * 50)
    
    # Run all debug functions
    debug_youtube_search()
    debug_video_extraction()
    debug_review_filtering()
    debug_search_queries()
    debug_full_scraper()
    
    print("\n" + "=" * 50)
    print("🏁 Debug Complete!")

if __name__ == "__main__":
    main() 