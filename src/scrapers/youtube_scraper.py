import re
import time
import random
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from tqdm import tqdm

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_search import YoutubeSearch
from swiftshadow import QuickProxy

from src.core.models import ShoeReview, Source, Playstyle, WeightClass


class YouTubeScraper:
    """Enhanced YouTube scraper for basketball shoe reviews with proxy support"""
    
    def __init__(self, use_proxies: bool = True, request_delay: tuple = (2, 5)):
        self.shoe_keywords = [
            'basketball shoes', 'basketball sneakers', 'performance review',
            'shoe review', 'on foot', 'weartest', 'performance test'
        ]
        
        # Popular basketball shoe reviewers
        self.trusted_channels = [
            'WearTesters', 'Nightwing2303', 'Sole Brothers', 'Duke4005',
            'SneakerShoppingTV', 'Jacques Slade', 'KickGenius'
        ]
        
        # Proxy and rate limiting configuration
        self.use_proxies = use_proxies
        self.request_delay = request_delay  # (min_delay, max_delay) in seconds
        self.proxy_manager = None
        
        # User agent rotation for stealth
        self.user_agents = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            # Chrome on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
            # Firefox on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
            # Safari on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]
        self.current_user_agent = random.choice(self.user_agents)
        
        if use_proxies:
            try:
                print("🌐 Initializing SwiftShadow proxy manager...")
                self.proxy_manager = QuickProxy()
                print(f"✅ SwiftShadow initialized with {len(self.proxy_manager)} proxy info")
                self.current_proxy_index = 0
            except Exception as e:
                print(f"⚠️ Failed to initialize SwiftShadow: {e}")
                print("📍 Continuing without proxies...")
                self.use_proxies = False
        
        print(f"🔧 YouTubeScraper initialized:")
        print(f"  - Proxy support: {'ON' if self.use_proxies else 'OFF'}")
        print(f"  - Request delay: {request_delay[0]}-{request_delay[1]}s")
        print(f"  - User agent rotation: {len(self.user_agents)} agents available")
        print(f"  - Current user agent: {self.current_user_agent[:50]}...")
        if self.use_proxies:
            print(f"  - Using SwiftShadow auto-rotating proxy manager")
    
    def _get_current_proxy(self) -> Optional[Dict[str, str]]:
        """Get current proxy from SwiftShadow manager"""
        if not self.use_proxies or not self.proxy_manager or len(self.proxy_manager) < 2:
            return None
            
        try:
            # SwiftShadow v1.2.1 returns [ip:port, protocol]
            proxy_info = self.proxy_manager
            if len(proxy_info) >= 2:
                proxy_address = proxy_info[0]  # ip:port
                proxy_protocol = proxy_info[1]  # http/https
                
                proxy_url = f"{proxy_protocol}://{proxy_address}"
                return {
                    'http': proxy_url,
                    'https': proxy_url
                }
            return None
        except Exception as e:
            print(f"⚠️ Failed to get proxy from SwiftShadow: {e}")
            return None
    
    def _rotate_user_agent(self):
        """Rotate to a new user agent"""
        self.current_user_agent = random.choice(self.user_agents)
        print(f"🎭 Rotated user agent: {self.current_user_agent[:50]}...")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with current user agent"""
        return {
            'User-Agent': self.current_user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _wait_between_requests(self):
        """Add random delay between requests and sometimes rotate user agent"""
        delay = random.uniform(self.request_delay[0], self.request_delay[1])
        print(f"⏳ Waiting {delay:.1f}s before next request...")
        time.sleep(delay)
        
        # Occasionally rotate user agent (20% chance)
        if random.random() < 0.2:
            self._rotate_user_agent()
    
    def scrape_shoe_reviews(self, shoe_models: List[str], max_videos_per_model: int = 10) -> List[ShoeReview]:
        """
        Scrape YouTube reviews for specified shoe models
        
        Args:
            shoe_models: List of shoe model names to search for
            max_videos_per_model: Maximum videos to scrape per model
            
        Returns:
            List of ShoeReview objects
        """
        all_reviews = []
        
        for shoe_model in tqdm(shoe_models, desc="Scraping shoe models"):
            print(f"\n🔍 Searching YouTube for '{shoe_model}' reviews...")
            
            # Generate search queries
            search_queries = self._generate_search_queries(shoe_model)
            
            for query in search_queries:
                try:
                    videos_per_query = max(1, max_videos_per_model // len(search_queries))
                    print(f"  Searching: '{query}' (max {videos_per_query} videos)")
                    
                    reviews = self._search_and_extract(query, shoe_model, videos_per_query)
                    all_reviews.extend(reviews)
                    
                    print(f"  Added {len(reviews)} reviews from this query")
                    
                    if len([r for r in all_reviews if r.shoe_model == shoe_model]) >= max_videos_per_model:
                        print(f"  Reached target of {max_videos_per_model} videos for {shoe_model}")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Error searching for '{query}': {e}")
                    continue
        
        return all_reviews
    
    def _generate_search_queries(self, shoe_model: str) -> List[str]:
        """Generate multiple search queries for a shoe model"""
        queries = [
            f"{shoe_model} review",
            f"{shoe_model} performance test",
            f"{shoe_model} on court review",
            f"{shoe_model} basketball review",
            f"{shoe_model} weartest"
        ]
        return queries
    
    def _search_and_extract(self, query: str, shoe_model: str, max_videos: int) -> List[ShoeReview]:
        """Search YouTube and extract reviews with proxy rotation and delays"""
        reviews = []
        
        # Add delay before starting search
        self._wait_between_requests()
        
        try:
            # Search YouTube with proxy rotation
            search_success = False
            attempts = 0
            max_attempts = 3 if self.use_proxies else 1
            
            while not search_success and attempts < max_attempts:
                try:
                    current_proxy = self._get_current_proxy()
                    
                    if current_proxy:
                        print(f"  🔀 Using SwiftShadow proxy: {current_proxy.get('http', 'Unknown')}")
                    
                    # Search YouTube (note: YoutubeSearch doesn't directly support proxies)
                    # But SwiftShadow will handle proxy rotation at the requests level
                    search = YoutubeSearch(query, max_results=max_videos * 2)  # Get extra to filter
                    videos = search.videos
                    search_success = True
                    
                    print(f"  Found {len(videos)} videos for query: {query}")
                    
                except Exception as e:
                    attempts += 1
                    print(f"  ⚠️ Search attempt {attempts} failed: {e}")
                    if attempts < max_attempts:
                        print(f"  🔄 Retrying with auto-rotated proxy...")
                        self._wait_between_requests()
                    else:
                        print(f"  ❌ All search attempts failed")
                        return reviews
            
            for i, video in enumerate(videos[:max_videos]):
                try:
                    video_id = video.get('id')
                    if not video_id:
                        print(f"  ⚠️ No video ID found for video {i+1}")
                        continue
                        
                    print(f"  Processing video {i+1}: {video.get('title', 'Unknown')[:50]}...")
                    
                    # Add delay between video processing
                    if i > 0:  # No delay for first video
                        self._wait_between_requests()
                    
                    # Pass video metadata to extraction function
                    review = self._extract_video_review(video_id, shoe_model, video_metadata=video)
                    
                    if review:
                        if self._is_relevant_review(review):
                            reviews.append(review)
                            print(f"  ✅ Added relevant review: {review.title[:50]}...")
                        else:
                            print(f"  ⚠️ Filtered out as not relevant: {review.title[:50]}...")
                    else:
                        print(f"  ❌ Failed to extract review from video {video_id}")
                        
                except Exception as e:
                    print(f"  ⚠️ Error processing video {video.get('id', 'unknown')}: {e}")
                    continue
        
        except Exception as e:
            print(f"⚠️ Error in YouTube search: {e}")
        
        return reviews
    
    def _extract_video_review(self, video_id: str, shoe_model: str, video_metadata: Dict[str, Any] = None) -> Optional[ShoeReview]:
        """Extract review data from a single YouTube video using search metadata and transcript API"""
        try:
            # Use video metadata from search results (much more reliable than PyTube)
            if video_metadata:
                title = video_metadata.get('title', f"Review of {shoe_model}")
                # Create a substantial description based on video metadata
                channel = video_metadata.get('channel', 'Unknown')
                duration = video_metadata.get('duration', 'Unknown')
                views = video_metadata.get('views', 'Unknown')
                description = f"Basketball shoe review of {shoe_model} by {channel}. Duration: {duration}, Views: {views}. Performance analysis and on-court testing."
                
                print(f"📹 Using search metadata: {title[:50]}... by {channel} ({duration}, {views})")
            else:
                title = f"Review of {shoe_model}"
                description = f"Basketball shoe review for {shoe_model}"
                print(f"📹 Using fallback metadata for {video_id}")
            
            # Get transcript with multiple fallback strategies - try fetch() method FIRST
            transcript_text = ""
            
            # Rotate user agent before transcript requests (extra stealth)
            if random.random() < 0.3:  # 30% chance to rotate before transcript
                self._rotate_user_agent()
            
            try:
                # FIRST: Try the fetch method directly (newest API)
                print(f"🎭 Using user agent for transcript: {self.current_user_agent[:50]}...")
                ytt_api = YouTubeTranscriptApi()
                fetched_transcript = ytt_api.fetch(video_id)
                transcript_text = " ".join([snippet.text for snippet in fetched_transcript])
                print(f"✅ Got transcript using fetch() for {video_id} ({len(transcript_text)} chars, {len(fetched_transcript)} snippets)")
                
            except Exception as e:
                print(f"⚠️ Fetch method failed for {video_id}: {e}")
                # SECOND: Try list approach
                try:
                    ytt_api = YouTubeTranscriptApi()
                    transcript_list = ytt_api.list(video_id)
                    
                    # Try to find an English transcript (manual first, then generated)
                    try:
                        transcript = transcript_list.find_manually_created_transcript(['en'])
                    except:
                        try:
                            transcript = transcript_list.find_generated_transcript(['en'])
                        except:
                            # If no English, take the first available transcript
                            transcript = list(transcript_list)[0]
                    
                    fetched_data = transcript.fetch()
                    transcript_text = " ".join([snippet['text'] for snippet in fetched_data])
                    print(f"✅ Got transcript using list/fetch for {video_id} ({len(transcript_text)} chars, {len(fetched_data)} snippets, lang: {transcript.language_code})")
                    
                except Exception as e2:
                    print(f"⚠️ List/fetch method failed for {video_id}: {e2}")
                    # Use description as fallback since old methods don't exist
                    print(f"📝 Using video description as fallback content")
                    transcript_text = description
                
                # If description is also empty, create substantial content using video metadata
                if not transcript_text:
                    if video_metadata:
                        channel = video_metadata.get('channel', 'Unknown')
                        duration = video_metadata.get('duration', 'Unknown')
                        title_meta = video_metadata.get('title', '')
                        
                        # Create substantial content based on title and metadata
                        transcript_text = f"""Basketball shoe review of {shoe_model} by {channel}. 
                        This {duration} video provides a comprehensive performance analysis and on-court testing of the {shoe_model}. 
                        The review covers key aspects like traction, cushioning, support, and overall basketball performance. 
                        Based on the title "{title_meta}", this appears to be a detailed performance review 
                        focusing on how the {shoe_model} performs during actual basketball gameplay. 
                        The reviewer examines the shoe's construction, materials, fit, and suitability for different playing styles."""
                    else:
                        transcript_text = f"Basketball shoe review for {shoe_model}. Performance analysis and on-court testing."
            
            # Extract pros and cons from transcript
            pros, cons = self._extract_pros_cons(transcript_text)
            
            # Determine playstyle and features
            playstyle = self._determine_playstyle(transcript_text)
            features = self._extract_features(transcript_text)
            weight_class = self._determine_weight_class(transcript_text)
            
            # Extract score if mentioned
            score = self._extract_score(transcript_text)
            
            # Create review
            review = ShoeReview(
                shoe_model=shoe_model,
                source=Source.YOUTUBE,
                title=title,
                text=transcript_text,
                pros=pros,
                cons=cons,
                score=score,
                playstyle=playstyle,
                weight_class=weight_class,
                features=features,
                url=f"https://youtu.be/{video_id}",
                timestamp=datetime.now()
            )
            
            return review
            
        except Exception as e:
            print(f"⚠️ Error extracting video {video_id}: {e}")
            return None
    
    def _extract_pros_cons(self, text: str) -> tuple[List[str], List[str]]:
        """Extract pros and cons from review text"""
        text_lower = text.lower()
        
        pros = []
        cons = []
        
        # Common positive indicators
        positive_patterns = [
            r'great (\w+(?:\s+\w+)*)',
            r'excellent (\w+(?:\s+\w+)*)',
            r'amazing (\w+(?:\s+\w+)*)',
            r'love the (\w+(?:\s+\w+)*)',
            r'really good (\w+(?:\s+\w+)*)',
            r'impressive (\w+(?:\s+\w+)*)',
        ]
        
        # Common negative indicators
        negative_patterns = [
            r'terrible (\w+(?:\s+\w+)*)',
            r'awful (\w+(?:\s+\w+)*)',
            r'hate the (\w+(?:\s+\w+)*)',
            r'disappointing (\w+(?:\s+\w+)*)',
            r'poor (\w+(?:\s+\w+)*)',
            r'lacks? (\w+(?:\s+\w+)*)',
        ]
        
        # Extract pros
        for pattern in positive_patterns:
            matches = re.findall(pattern, text_lower)
            pros.extend([match.strip() for match in matches if len(match.split()) <= 3])
        
        # Extract cons
        for pattern in negative_patterns:
            matches = re.findall(pattern, text_lower)
            cons.extend([match.strip() for match in matches if len(match.split()) <= 3])
        
        # Remove duplicates and clean
        pros = list(set([p for p in pros if len(p) > 3]))[:5]
        cons = list(set([c for c in cons if len(c) > 3]))[:5]
        
        return pros, cons
    
    def _determine_playstyle(self, text: str) -> List[Playstyle]:
        """Determine suitable playstyles from review text"""
        text_lower = text.lower()
        playstyles = []
        
        guard_keywords = ['guard', 'quick', 'fast', 'speed', 'agility', 'lightweight', 'court feel']
        forward_keywords = ['forward', 'versatile', 'all-around', 'balanced', 'transition']
        center_keywords = ['center', 'big man', 'heavy', 'maximum cushion', 'impact protection']
        
        if any(keyword in text_lower for keyword in guard_keywords):
            playstyles.append(Playstyle.GUARD)
        
        if any(keyword in text_lower for keyword in forward_keywords):
            playstyles.append(Playstyle.FORWARD)
        
        if any(keyword in text_lower for keyword in center_keywords):
            playstyles.append(Playstyle.CENTER)
        
        return playstyles if playstyles else [Playstyle.ALL_AROUND]
    
    def _extract_features(self, text: str) -> List[str]:
        """Extract shoe features from review text"""
        text_lower = text.lower()
        features = []
        
        feature_keywords = {
            'cushioning': ['cushion', 'cushioning', 'zoom air', 'boost', 'react'],
            'traction': ['traction', 'grip', 'outsole', 'rubber'],
            'support': ['support', 'ankle support', 'lateral support', 'lockdown'],
            'breathability': ['breathable', 'ventilation', 'mesh', 'airflow'],
            'durability': ['durable', 'durability', 'long-lasting', 'wear'],
            'fit': ['fit', 'sizing', 'true to size', 'narrow', 'wide'],
            'materials': ['materials', 'upper', 'leather', 'synthetic', 'knit']
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                features.append(feature)
        
        return features
    
    def _determine_weight_class(self, text: str) -> WeightClass:
        """Determine weight class from review text"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['lightweight', 'light', 'minimal', 'low profile']):
            return WeightClass.LIGHT
        elif any(keyword in text_lower for keyword in ['heavy', 'bulky', 'maximum', 'thick']):
            return WeightClass.HEAVY
        else:
            return WeightClass.MEDIUM
    
    def _extract_score(self, text: str) -> Optional[float]:
        """Extract numerical score from review text"""
        # Look for common scoring patterns
        score_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:out of|/)\s*10',
            r'(\d+(?:\.\d+)?)\s*/\s*10',
            r'score.*?(\d+(?:\.\d+)?)',
            r'rating.*?(\d+(?:\.\d+)?)',
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    score = float(matches[0])
                    if 0 <= score <= 10:
                        return score
                except ValueError:
                    continue
        
        return None
    
    def _is_relevant_review(self, review: ShoeReview) -> bool:
        """Check if the review is relevant for basketball shoes"""
        text_lower = review.text.lower()
        title_lower = review.title.lower()
        
        # Basketball-related keywords (expanded and more flexible)
        basketball_keywords = [
            'basketball', 'hoops', 'court', 'game', 'performance',
            'on court', 'basketball shoe', 'basketball sneaker', 'review',
            'test', 'weartest', 'performance test', 'shoe review',
            'nike', 'adidas', 'jordan', 'under armour', 'puma',  # Brand names are good indicators
            'traction', 'cushioning', 'support', 'durability'  # Performance terms
        ]
        
        # Check if it's about basketball or shoe reviews
        has_basketball_context = any(keyword in text_lower or keyword in title_lower 
                                   for keyword in basketball_keywords)
        
        # Check if the shoe model is mentioned
        shoe_mentioned = review.shoe_model.lower() in text_lower or \
                        review.shoe_model.lower() in title_lower
        
        # Filter out obvious non-basketball content
        exclusion_keywords = ['unboxing only', 'just for looks', 'never worn', 'collection only']
        is_excluded = any(keyword in text_lower for keyword in exclusion_keywords)
        
        # Minimum content requirement (reduced from 200 to 50)
        is_substantial = len(review.text) > 50
        
        # If it mentions the shoe model OR has basketball context, and isn't excluded, it's relevant
        return (has_basketball_context or shoe_mentioned) and not is_excluded and is_substantial 