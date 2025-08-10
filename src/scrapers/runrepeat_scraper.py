import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm

from src.core.models import ShoeReview, Source, Playstyle, WeightClass

# For sentiment analysis
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

class RunRepeatScraper:
    """Enhanced RunRepeat scraper with sentiment analysis and keyword extraction"""
    
    def __init__(self):
        self.base_url = "https://runrepeat.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Basketball-specific keywords for extraction
        self.basketball_keywords = {
            'performance': ['traction', 'grip', 'cushioning', 'support', 'responsiveness', 'stability', 
                          'lockdown', 'court feel', 'energy return', 'impact protection', 'bounce'],
            'playstyle': ['guard', 'forward', 'center', 'quick', 'explosive', 'agile', 'powerful', 
                         'cutting', 'jumping', 'lateral movement', 'speed', 'acceleration'],
            'features': ['zoom air', 'air max', 'boost', 'react', 'fresh foam', 'gel', 'carbon fiber',
                        'knit upper', 'leather', 'synthetic', 'mesh', 'flyknit', 'primeknit'],
            'court_type': ['indoor', 'outdoor', 'hardwood', 'concrete', 'asphalt', 'gym', 'street'],
            'comfort': ['comfortable', 'break-in', 'true to size', 'narrow', 'wide', 'snug', 'roomy',
                       'padding', 'heel slip', 'toe box', 'arch support', 'breathable'],
            'durability': ['durable', 'wear', 'lasting', 'sole separation', 'upper tear', 'outsole',
                          'rubber compound', 'heel drag', 'toe wear', 'construction quality']
        }
        
        # Sentiment keywords
        self.sentiment_keywords = {
            'very_positive': ['excellent', 'amazing', 'outstanding', 'fantastic', 'incredible', 'perfect',
                             'love', 'best', 'exceptional', 'superb', 'phenomenal', 'flawless'],
            'positive': ['good', 'great', 'nice', 'solid', 'decent', 'recommend', 'happy', 'satisfied',
                        'pleased', 'impressed', 'quality', 'worth it', 'reliable', 'comfortable'],
            'negative': ['bad', 'poor', 'disappointing', 'uncomfortable', 'issues', 'problems', 
                        'regret', 'waste', 'cheap', 'flimsy', 'thin', 'slippery', 'tight'],
            'very_negative': ['terrible', 'awful', 'horrible', 'worst', 'hate', 'useless', 'garbage',
                             'broke', 'fell apart', 'destroyed', 'dangerous', 'painful']
        }
        
        # Cache for scraped data to avoid re-scraping
        self._scraped_shoes = {}

    def scrape_shoe_reviews(self, shoe_models: List[str]) -> List[ShoeReview]:
        """
        Scrape RunRepeat reviews for specified shoe models
        
        Args:
            shoe_models: List of shoe model names to search for
            
        Returns:
            List of ShoeReview objects
        """
        all_reviews = []
        
        # First, get all available shoes from catalog
        available_shoes = self._get_catalog_shoes()
        
        print(f"🔍 Found {len(available_shoes)} shoes in RunRepeat catalog")
        
        for shoe_model in tqdm(shoe_models, desc="Scraping RunRepeat reviews"):
            print(f"\n🔍 Searching RunRepeat for '{shoe_model}'...")
            
            try:
                # Find matching shoes in catalog
                matching_shoes = self._find_matching_shoes(shoe_model, available_shoes)
                
                if not matching_shoes:
                    print(f"⚠️ No exact match found for '{shoe_model}' in catalog")
                    continue
                
                # Scrape the best matching shoe
                best_match = matching_shoes[0]
                review = self._scrape_single_shoe_review(best_match)
                
                if review:
                    all_reviews.append(review)
                    print(f"✅ Successfully scraped {review.shoe_model}")
                else:
                    print(f"⚠️ No review data found for {shoe_model}")
                    
            except Exception as e:
                print(f"❌ Error scraping {shoe_model}: {e}")
                continue
            
            # Be respectful to the server
            time.sleep(2)
        
        print(f"\n✅ Successfully scraped {len(all_reviews)} RunRepeat reviews")
        return all_reviews

    def _get_catalog_shoes(self) -> List[Dict]:
        """Get all basketball shoes from RunRepeat catalog."""
        url = f"{self.base_url}/catalog/basketball-shoes"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract shoes from JSON-LD structured data
            shoes = self._extract_json_ld_data(soup)
            return shoes
            
        except Exception as e:
            print(f"Error fetching catalog: {e}")
            return []

    def _extract_json_ld_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract structured data from JSON-LD scripts."""
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        shoes_data = []
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                
                # Look for ItemList with shoe data
                if (data.get('@type') == 'ItemList' and 
                    'itemListElement' in data and
                    len(data['itemListElement']) > 5):  # Likely shoe list
                    
                    for item in data['itemListElement']:
                        if item.get('@type') == 'ListItem':
                            shoe_data = {
                                'name': item.get('name', ''),
                                'url': item.get('url', ''),
                                'image': item.get('image', ''),
                                'position': item.get('position', 0)
                            }
                            if shoe_data['name'] and shoe_data['url']:
                                shoes_data.append(shoe_data)
                                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                continue
                
        return shoes_data

    def _find_matching_shoes(self, target_model: str, available_shoes: List[Dict]) -> List[Dict]:
        """Find shoes that match the target model name."""
        target_lower = target_model.lower()
        
        # Try exact match first
        exact_matches = [shoe for shoe in available_shoes 
                        if target_lower in shoe['name'].lower()]
        
        if exact_matches:
            return exact_matches
        
        # Try partial matching on key terms
        target_terms = target_lower.replace('-', ' ').split()
        scored_matches = []
        
        for shoe in available_shoes:
            shoe_name_lower = shoe['name'].lower()
            score = sum(1 for term in target_terms if term in shoe_name_lower)
            
            if score >= 2:  # At least 2 matching terms
                scored_matches.append((score, shoe))
        
        # Return shoes sorted by match score
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        return [shoe for score, shoe in scored_matches]

    def _scrape_single_shoe_review(self, shoe_data: Dict) -> Optional[ShoeReview]:
        """Scrape detailed review data for a single shoe."""
        url = shoe_data['url']
        
        # Check cache first
        if url in self._scraped_shoes:
            return self._scraped_shoes[url]
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all content
            extracted_data = self._extract_all_content(soup)
            
            # Create ShoeReview object
            review = self._create_shoe_review(shoe_data, extracted_data, url)
            
            # Cache the result
            self._scraped_shoes[url] = review
            
            return review
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    def _extract_all_content(self, soup: BeautifulSoup) -> Dict:
        """Extract all relevant content from shoe page."""
        content = {}
        
        # Extract page title
        title_tag = soup.find('title')
        content['title'] = title_tag.text.strip() if title_tag else ""
        
        # Extract RunRepeat score
        score_elements = soup.find_all('div', class_=['score_green', 'score_light_green', 'corescore-big__score'])
        content['score'] = None
        for elem in score_elements:
            score_text = elem.get_text(strip=True)
            if score_text.isdigit() and 50 <= int(score_text) <= 100:
                content['score'] = int(score_text)
                break
        
        # Extract price information
        price_elements = soup.find_all('span', string=re.compile(r'\$\d+'))
        prices = []
        for elem in price_elements:
            price_text = elem.get_text(strip=True)
            price_match = re.search(r'\$(\d+)', price_text)
            if price_match:
                prices.append(int(price_match.group(1)))
        
        content['prices'] = prices
        
        # Extract all text content
        full_text = soup.get_text(separator=' ', strip=True)
        content['full_text'] = full_text
        
        # Extract structured content
        content['description'] = self._extract_description(soup)
        content['pros_cons'] = self._extract_pros_cons(full_text)
        
        return content

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description."""
        # Look for meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        # Look for description sections
        desc_selectors = ['.product-description', '.shoe-description', '.description']
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return ""

    def _extract_pros_cons(self, text: str) -> Dict[str, List[str]]:
        """Extract pros and cons from text."""
        pros = []
        cons = []
        
        text_lower = text.lower()
        
        # Look for explicit pros/cons sections
        pros_patterns = [
            r'pros?\s*:(.+?)(?:cons?\s*:|$)',
            r'advantages?\s*:(.+?)(?:disadvantages?\s*:|$)',
            r'positives?\s*:(.+?)(?:negatives?\s*:|$)'
        ]
        
        cons_patterns = [
            r'cons?\s*:(.+?)(?:pros?\s*:|$)',
            r'disadvantages?\s*:(.+?)(?:advantages?\s*:|$)',
            r'negatives?\s*:(.+?)(?:positives?\s*:|$)'
        ]
        
        for pattern in pros_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                sentences = [s.strip() for s in match.split('.') if len(s.strip()) > 10]
                pros.extend(sentences[:3])  # Limit to 3 pros
        
        for pattern in cons_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                sentences = [s.strip() for s in match.split('.') if len(s.strip()) > 10]
                cons.extend(sentences[:3])  # Limit to 3 cons
        
        return {'pros': pros, 'cons': cons}

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract basketball-specific keywords from text."""
        if not text:
            return []
        
        text_lower = text.lower()
        found_keywords = []
        
        for category, keywords in self.basketball_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))  # Remove duplicates

    def _determine_playstyle(self, text: str, keywords: List[str]) -> List[Playstyle]:
        """Determine playstyle from text and keywords."""
        text_lower = text.lower()
        playstyles = []
        
        # Check for explicit playstyle mentions
        if any(word in text_lower for word in ['guard', 'point guard', 'shooting guard']):
            playstyles.append(Playstyle.GUARD)
        
        if any(word in text_lower for word in ['forward', 'small forward', 'power forward']):
            playstyles.append(Playstyle.FORWARD)
        
        if any(word in text_lower for word in ['center', 'big man', 'post']):
            playstyles.append(Playstyle.CENTER)
        
        # If no specific playstyle found, default to all-around
        if not playstyles:
            playstyles.append(Playstyle.ALL_AROUND)
        
        return playstyles

    def _determine_weight_class(self, text: str) -> Optional[WeightClass]:
        """Determine weight class from text."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['light', 'lightweight', 'fast', 'quick']):
            return WeightClass.LIGHT
        elif any(word in text_lower for word in ['heavy', 'heavyweight', 'solid', 'substantial']):
            return WeightClass.HEAVY
        else:
            return WeightClass.MEDIUM

    def _perform_sentiment_analysis(self, text: str) -> float:
        """Perform sentiment analysis on text content."""
        if not text or len(text.strip()) < 10:
            return 5.0  # Neutral score
        
        # Method 1: TextBlob (if available)
        textblob_score = 0.0
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                textblob_score = blob.sentiment.polarity  # -1 to 1
            except Exception:
                pass
        
        # Method 2: Keyword-based sentiment
        keyword_score = self._calculate_keyword_sentiment(text)
        
        # Combine both methods (prefer TextBlob if available)
        if TEXTBLOB_AVAILABLE and abs(textblob_score) > 0.1:
            final_score = textblob_score
        else:
            final_score = keyword_score
        
        # Convert to 0-10 scale
        sentiment_score = (final_score + 1) * 5
        return max(0.0, min(10.0, sentiment_score))

    def _calculate_keyword_sentiment(self, text: str) -> float:
        """Calculate sentiment based on keyword matching."""
        text_lower = text.lower()
        
        # Count sentiment keywords
        very_positive_count = sum(1 for word in self.sentiment_keywords['very_positive'] 
                                 if word in text_lower)
        positive_count = sum(1 for word in self.sentiment_keywords['positive'] 
                           if word in text_lower)
        negative_count = sum(1 for word in self.sentiment_keywords['negative'] 
                           if word in text_lower)
        very_negative_count = sum(1 for word in self.sentiment_keywords['very_negative'] 
                                if word in text_lower)
        
        # Calculate weighted score
        total_positive = very_positive_count * 2 + positive_count * 1
        total_negative = very_negative_count * 2 + negative_count * 1
        
        if total_positive + total_negative == 0:
            return 0.0
        
        # Score ranges from -1 to 1
        return (total_positive - total_negative) / (total_positive + total_negative)

    def _create_shoe_review(self, shoe_data: Dict, extracted_data: Dict, url: str) -> ShoeReview:
        """Create a ShoeReview object from extracted data."""
        
        # Extract basic info
        shoe_name = shoe_data['name']
        title = extracted_data.get('title', shoe_name)
        full_text = extracted_data.get('full_text', '')
        description = extracted_data.get('description', '')
        
        # Combine text for analysis
        analysis_text = ' '.join([description, full_text])
        
        # Extract structured data
        pros_cons = extracted_data.get('pros_cons', {'pros': [], 'cons': []})
        keywords = self._extract_keywords(analysis_text)
        playstyles = self._determine_playstyle(analysis_text, keywords)
        weight_class = self._determine_weight_class(analysis_text)
        
        # Sentiment analysis
        sentiment_score = self._perform_sentiment_analysis(analysis_text)
        
        # Price range
        prices = extracted_data.get('prices', [])
        price_range = [min(prices), max(prices)] if prices else None
        
        # Score (convert to 10-point scale if needed)
        score = extracted_data.get('score')
        if score and score > 10:
            score = score / 10.0  # Convert 100-point to 10-point scale
        
        return ShoeReview(
            shoe_model=shoe_name,
            source=Source.RUNREPEAT,
            title=title,
            text=description if description else analysis_text[:500],  # Limit text length
            pros=pros_cons['pros'][:5],  # Limit to 5 pros
            cons=pros_cons['cons'][:5],  # Limit to 5 cons
            score=score,
            playstyle=playstyles,
            weight_class=weight_class,
            price_range=price_range,
            features=keywords[:10],  # Limit to 10 features
            url=url,
            timestamp=datetime.now()
        ) 