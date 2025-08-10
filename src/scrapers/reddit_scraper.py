import praw
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from tqdm import tqdm
import time

from src.core.models import ShoeReview, Source, Playstyle, WeightClass


class RedditScraper:
    """Enhanced Reddit scraper for basketball shoe discussions"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None):
        self.client_id = client_id or "JdYlCavPJLyMBfA5_vtrbw"
        self.client_secret = client_secret or "Dl3cfMYcZ29kA4xhx8NVsE7jNZFqkA"
        self.user_agent = user_agent or "BasketballShoeBot/1.0"
        
        # Initialize Reddit instance
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
        except Exception as e:
            print(f"⚠️ Reddit API setup failed: {e}")
            self.reddit = None
        
        # Basketball shoe related subreddits
        self.target_subreddits = [
            'BBallShoes',
            'Basketball',
            'Sneakers',
            'basketballshoes',
            'NikeBasketball',
            'adidas',
            'Jordans'
        ]
        
        # Rate limiting
        self.delay_between_requests = 1
    
    def scrape_shoe_discussions(self, shoe_models: List[str], posts_per_model: int = 20) -> List[ShoeReview]:
        """
        Scrape Reddit discussions for specified shoe models
        
        Args:
            shoe_models: List of shoe model names to search for
            posts_per_model: Maximum posts to scrape per model
            
        Returns:
            List of ShoeReview objects
        """
        if not self.reddit:
            print("❌ Reddit API not available. Skipping Reddit scraping.")
            return []
        
        all_reviews = []
        
        for shoe_model in tqdm(shoe_models, desc="Scraping Reddit discussions"):
            print(f"\n🔍 Searching Reddit for '{shoe_model}' discussions...")
            
            try:
                reviews = self._scrape_shoe_model(shoe_model, posts_per_model)
                all_reviews.extend(reviews)
                print(f"✅ Found {len(reviews)} relevant discussions for {shoe_model}")
                
            except Exception as e:
                print(f"❌ Error scraping {shoe_model}: {e}")
            
            # Rate limiting
            time.sleep(self.delay_between_requests)
        
        return all_reviews
    
    def _scrape_shoe_model(self, shoe_model: str, max_posts: int) -> List[ShoeReview]:
        """Scrape discussions for a single shoe model"""
        reviews = []
        
        # Calculate posts per subreddit (ensure at least 1 per subreddit)
        posts_per_subreddit = max(1, max_posts // len(self.target_subreddits))
        if max_posts % len(self.target_subreddits) != 0:
            posts_per_subreddit += 1  # Round up to ensure we get enough posts
        
        # Search across multiple subreddits
        for subreddit_name in self.target_subreddits:
            try:
                subreddit_reviews = self._search_subreddit(subreddit_name, shoe_model, posts_per_subreddit)
                reviews.extend(subreddit_reviews)
                
                if len(reviews) >= max_posts:
                    break
                    
            except Exception as e:
                print(f"⚠️ Error searching r/{subreddit_name}: {e}")
                continue
        
        return reviews[:max_posts]
    
    def _search_subreddit(self, subreddit_name: str, shoe_model: str, max_posts: int) -> List[ShoeReview]:
        """Search a specific subreddit for shoe discussions"""
        reviews = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Search for the shoe model
            search_results = subreddit.search(
                query=shoe_model,
                sort='relevance',
                time_filter='all',
                limit=max_posts * 2  # Get extra to filter
            )
            
            for post in search_results:
                try:
                    review = self._extract_post_review(post, shoe_model)
                    if review and self._is_relevant_discussion(review):
                        reviews.append(review)
                        
                    if len(reviews) >= max_posts:
                        break
                        
                except Exception as e:
                    print(f"⚠️ Error processing post {post.id}: {e}")
                    continue
        
        except Exception as e:
            print(f"⚠️ Error accessing r/{subreddit_name}: {e}")
        
        return reviews
    
    def _extract_post_review(self, post, shoe_model: str) -> Optional[ShoeReview]:
        """Extract review data from a Reddit post"""
        try:
            # Combine title and text
            full_text = f"{post.title}\n\n{post.selftext}"
            
            # Get top comments for additional context
            post.comments.replace_more(limit=0)  # Remove "load more comments"
            top_comments = []
            for comment in post.comments[:5]:  # Top 5 comments
                if hasattr(comment, 'body') and len(comment.body) > 50:
                    top_comments.append(comment.body)
            
            if top_comments:
                full_text += "\n\nTop Comments:\n" + "\n".join(top_comments)
            
            # Extract pros and cons
            pros, cons = self._extract_pros_cons_from_text(full_text)
            
            # Determine characteristics
            playstyle = self._determine_playstyle_from_discussion(full_text)
            features = self._extract_features_from_discussion(full_text)
            weight_class = self._determine_weight_class_from_discussion(full_text)
            
            # Extract score if mentioned
            score = self._extract_score_from_discussion(full_text)
            
            review = ShoeReview(
                shoe_model=shoe_model,
                source=Source.REDDIT,
                title=post.title,
                text=full_text,
                pros=pros,
                cons=cons,
                score=score,
                playstyle=playstyle,
                weight_class=weight_class,
                features=features,
                url=f"https://reddit.com{post.permalink}",
                timestamp=datetime.fromtimestamp(post.created_utc)
            )
            
            return review
            
        except Exception as e:
            print(f"⚠️ Error extracting post: {e}")
            return None
    
    def _extract_pros_cons_from_text(self, text: str) -> tuple[List[str], List[str]]:
        """Extract pros and cons from discussion text"""
        text_lower = text.lower()
        
        pros = []
        cons = []
        
        # Look for explicit pros/cons sections
        pros_match = re.search(r'pros?:?\s*(.*?)(?=cons?:|$)', text_lower, re.DOTALL)
        cons_match = re.search(r'cons?:?\s*(.*?)(?=pros?:|$)', text_lower, re.DOTALL)
        
        if pros_match:
            pros_text = pros_match.group(1)
            # Extract bullet points or lines
            pros_lines = [line.strip() for line in pros_text.split('\n') if line.strip()]
            pros = [line.lstrip('•-* ') for line in pros_lines if len(line) > 10][:5]
        
        if cons_match:
            cons_text = cons_match.group(1)
            # Extract bullet points or lines
            cons_lines = [line.strip() for line in cons_text.split('\n') if line.strip()]
            cons = [line.lstrip('•-* ') for line in cons_lines if len(line) > 10][:5]
        
        # If no explicit pros/cons, look for sentiment patterns
        if not pros and not cons:
            pros, cons = self._extract_sentiment_based_opinions(text_lower)
        
        return pros, cons
    
    def _extract_sentiment_based_opinions(self, text: str) -> tuple[List[str], List[str]]:
        """Extract opinions based on sentiment indicators"""
        pros = []
        cons = []
        
        # Positive sentiment patterns
        positive_patterns = [
            r'love (?:the )?(\w+(?:\s+\w+)*)',
            r'great (\w+(?:\s+\w+)*)',
            r'amazing (\w+(?:\s+\w+)*)',
            r'excellent (\w+(?:\s+\w+)*)',
            r'really good (\w+(?:\s+\w+)*)',
        ]
        
        # Negative sentiment patterns
        negative_patterns = [
            r'hate (?:the )?(\w+(?:\s+\w+)*)',
            r'terrible (\w+(?:\s+\w+)*)',
            r'awful (\w+(?:\s+\w+)*)',
            r'disappointed (?:with )?(?:the )?(\w+(?:\s+\w+)*)',
            r'poor (\w+(?:\s+\w+)*)',
        ]
        
        # Extract positive opinions
        for pattern in positive_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match.split()) <= 4 and len(match) > 3:
                    pros.append(match.strip())
        
        # Extract negative opinions
        for pattern in negative_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match.split()) <= 4 and len(match) > 3:
                    cons.append(match.strip())
        
        # Remove duplicates and limit
        pros = list(set(pros))[:3]
        cons = list(set(cons))[:3]
        
        return pros, cons
    
    def _determine_playstyle_from_discussion(self, text: str) -> List[Playstyle]:
        """Determine playstyle from discussion content"""
        text_lower = text.lower()
        playstyles = []
        
        guard_keywords = [
            'guard', 'pg', 'point guard', 'quick', 'fast', 'speed', 'agility',
            'lightweight', 'court feel', 'low to ground', 'responsive'
        ]
        
        forward_keywords = [
            'forward', 'sf', 'pf', 'small forward', 'power forward',
            'versatile', 'all-around', 'balanced', 'transition'
        ]
        
        center_keywords = [
            'center', 'big man', 'heavy player', 'maximum cushion',
            'impact protection', 'post play', 'rebounding'
        ]
        
        if any(keyword in text_lower for keyword in guard_keywords):
            playstyles.append(Playstyle.GUARD)
        
        if any(keyword in text_lower for keyword in forward_keywords):
            playstyles.append(Playstyle.FORWARD)
        
        if any(keyword in text_lower for keyword in center_keywords):
            playstyles.append(Playstyle.CENTER)
        
        return playstyles if playstyles else [Playstyle.ALL_AROUND]
    
    def _extract_features_from_discussion(self, text: str) -> List[str]:
        """Extract features discussed in the text"""
        text_lower = text.lower()
        features = []
        
        feature_keywords = {
            'cushioning': ['cushion', 'cushioning', 'zoom', 'air', 'boost', 'react', 'soft landing'],
            'traction': ['traction', 'grip', 'slip', 'outsole', 'court grip', 'rubber'],
            'support': ['support', 'ankle support', 'lateral support', 'lockdown', 'stability'],
            'breathability': ['breathable', 'ventilation', 'mesh', 'airflow', 'hot feet'],
            'durability': ['durable', 'durability', 'wear', 'long-lasting', 'hold up'],
            'fit': ['fit', 'sizing', 'true to size', 'narrow', 'wide', 'runs small', 'runs large'],
            'comfort': ['comfort', 'comfortable', 'all day wear', 'break in'],
            'materials': ['materials', 'upper', 'leather', 'synthetic', 'knit', 'quality']
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                features.append(feature)
        
        return features
    
    def _determine_weight_class_from_discussion(self, text: str) -> WeightClass:
        """Determine weight class from discussion"""
        text_lower = text.lower()
        
        light_keywords = ['lightweight', 'light', 'minimal', 'barely feel them', 'not bulky']
        heavy_keywords = ['heavy', 'bulky', 'substantial', 'thick sole', 'chunky']
        
        if any(keyword in text_lower for keyword in light_keywords):
            return WeightClass.LIGHT
        elif any(keyword in text_lower for keyword in heavy_keywords):
            return WeightClass.HEAVY
        else:
            return WeightClass.MEDIUM
    
    def _extract_score_from_discussion(self, text: str) -> Optional[float]:
        """Extract score from discussion text with improved patterns and sentiment fallback"""
        
        # Expanded patterns for various rating formats
        score_patterns = [
            # Original patterns (improved)
            r'(\d+(?:\.\d+)?)\s*(?:out of|/)\s*10',
            r'(\d+(?:\.\d+)?)\s*/\s*10',
            r'rate (?:them )?(\d+(?:\.\d+)?)',
            r'score (?:of )?(\d+(?:\.\d+)?)',
            r'give (?:them )?(?:a )?(\d+(?:\.\d+)?)',
            
            # New explicit rating patterns
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*10',      # "8.5 out of 10"
            r'(\d+(?:\.\d+)?)\s*\/\s*10',            # "8/10"
            r'rating\s*:?\s*(\d+(?:\.\d+)?)',        # "rating: 8.5"
            r'(\d+(?:\.\d+)?)\s*stars?',             # "8.5 stars"
            r'overall\s*(\d+(?:\.\d+)?)',            # "overall 8"
            r'(\d)\s*/\s*10',                        # "8 / 10"
            r'(\d)\s*out\s*of\s*10',                 # "8 out of 10"
            r'i\'d\s*(?:give|rate)\s*(?:them|it|these)?\s*(?:a\s*)?(\d+(?:\.\d+)?)', # "I'd rate them 8"
            
            # 5-point scale patterns
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*5',       # "4 out of 5"
            r'(\d+(?:\.\d+)?)\s*\/\s*5',             # "4/5"
        ]
        
        # Try to find explicit numerical ratings first
        for pattern in score_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    score = float(matches[0])
                    
                    # Convert 5-point scale to 10-point scale
                    if any(scale_indicator in pattern for scale_indicator in ['out of 5', '/ 5', '/5']):
                        score = score * 2
                    
                    # Validate score range
                    if 0 <= score <= 10:
                        return score
                    elif 0 <= score <= 5:  # Handle missed 5-point scale
                        return score * 2
                except ValueError:
                    continue
        
        # Fallback: Sentiment-based scoring for Reddit discussions
        return self._extract_sentiment_score(text)
    
    def _extract_sentiment_score(self, text: str) -> Optional[float]:
        """Extract sentiment-based score when no explicit rating is found"""
        text_lower = text.lower()
        
        # Very positive indicators (8-10 range)
        very_positive = [
            'amazing', 'incredible', 'fantastic', 'perfect', 'outstanding', 'excellent',
            'best ever', 'love these', 'absolutely love', 'blown away', 'mind blown',
            'game changer', 'holy grail', 'dream shoe', 'obsessed', 'flawless'
        ]
        
        # Positive indicators (6-8 range)
        positive = [
            'great', 'good', 'solid', 'nice', 'pretty good', 'really good',
            'like them', 'impressed', 'satisfied', 'recommend', 'worth it',
            'happy with', 'pleased', 'decent', 'quality', 'comfortable'
        ]
        
        # Negative indicators (3-5 range)
        negative = [
            'bad', 'poor', 'terrible', 'awful', 'horrible', 'disappointed',
            'not good', 'not great', 'mediocre', 'average', 'meh', 'okay',
            'could be better', 'not impressed', 'underwhelmed'
        ]
        
        # Very negative indicators (1-3 range)
        very_negative = [
            'worst', 'hate', 'regret', 'waste of money', 'garbage', 'trash',
            'complete failure', 'avoid', 'don\'t buy', 'save your money'
        ]
        
        # Count sentiment indicators
        very_pos_count = sum(1 for phrase in very_positive if phrase in text_lower)
        pos_count = sum(1 for phrase in positive if phrase in text_lower)
        neg_count = sum(1 for phrase in negative if phrase in text_lower)
        very_neg_count = sum(1 for phrase in very_negative if phrase in text_lower)
        
        # Calculate sentiment score if we found indicators
        total_indicators = very_pos_count + pos_count + neg_count + very_neg_count
        
        if total_indicators > 0:
            # Weight the sentiment
            sentiment_score = (very_pos_count * 9 + pos_count * 7 + neg_count * 4 + very_neg_count * 2) / total_indicators
            
            # Only return sentiment score if it's based on multiple indicators or very strong single indicator
            if total_indicators >= 2 or very_pos_count > 0 or very_neg_count > 0:
                return round(sentiment_score, 1)
        
        # No clear sentiment indicators found
        return None
    
    def _is_relevant_discussion(self, review: ShoeReview) -> bool:
        """Check if the discussion is relevant for basketball shoes"""
        text_lower = review.text.lower()
        title_lower = review.title.lower()
        
        # Expanded basketball/performance-related keywords (more inclusive)
        basketball_keywords = [
            'basketball', 'hoops', 'court', 'game', 'performance', 'playing',
            'ball', 'hoop', 'on court', 'indoor', 'outdoor', 'gym',
            'cushioning', 'traction', 'support', 'ankle', 'jump', 'run',
            'comfort', 'fit', 'durability', 'grip', 'sole', 'midsole',
            'zoom', 'air', 'boost', 'react', 'responsive', 'lockdown'
        ]
        
        # Basketball shoe context (more lenient - includes performance terms)
        has_basketball_context = any(keyword in text_lower or keyword in title_lower 
                                   for keyword in basketball_keywords)
        
        # Also check if it's in basketball-focused subreddits (implicit context)
        basketball_subreddits = ['bballshoes', 'basketballshoes', 'basketball']
        is_basketball_subreddit = any(sub in review.url.lower() for sub in basketball_subreddits)
        
        # Filter out pure lifestyle discussions (only if no performance context)
        lifestyle_keywords = ['outfit', 'fashion', 'style only', 'looks', 'casual wear', 'streetwear']
        is_lifestyle_only = any(keyword in text_lower for keyword in lifestyle_keywords) and \
                           not has_basketball_context and not is_basketball_subreddit
        
        # Must be substantial enough (lowered threshold)
        is_substantial = len(review.text) > 50  # Reduced from 100
        
        # Check if it's actually about the shoe model (more flexible)
        shoe_keywords = review.shoe_model.lower().split()
        shoe_mentioned = any(word in text_lower or word in title_lower 
                           for word in shoe_keywords if len(word) > 2)  # Skip short words like "21"
        
        # More lenient criteria: pass if any of these conditions are met
        performance_context = has_basketball_context or is_basketball_subreddit
        
        return performance_context and not is_lifestyle_only and is_substantial and shoe_mentioned 