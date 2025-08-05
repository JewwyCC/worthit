import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from tqdm import tqdm
import time

from src.core.models import ShoeReview, Source, Playstyle, WeightClass


class RunRepeatScraper:
    """Enhanced RunRepeat scraper for basketball shoe reviews"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://runrepeat.com"
        
        # Rate limiting
        self.delay_between_requests = 2
    
    def scrape_shoe_reviews(self, shoe_models: List[str]) -> List[ShoeReview]:
        """
        Scrape RunRepeat reviews for specified shoe models
        
        Args:
            shoe_models: List of shoe model names to search for
            
        Returns:
            List of ShoeReview objects
        """
        all_reviews = []
        
        for shoe_model in tqdm(shoe_models, desc="Scraping RunRepeat reviews"):
            print(f"\n🔍 Searching RunRepeat for '{shoe_model}'...")
            
            try:
                review = self._scrape_single_shoe(shoe_model)
                if review:
                    all_reviews.append(review)
                    print(f"✅ Successfully scraped {shoe_model}")
                else:
                    print(f"⚠️ No review found for {shoe_model}")
                    
            except Exception as e:
                print(f"❌ Error scraping {shoe_model}: {e}")
            
            # Rate limiting
            time.sleep(self.delay_between_requests)
        
        return all_reviews
    
    def _scrape_single_shoe(self, shoe_model: str) -> Optional[ShoeReview]:
        """Scrape a single shoe review from RunRepeat"""
        # Generate potential URLs
        urls = self._generate_urls(shoe_model)
        
        for url in urls:
            try:
                review = self._extract_review_from_url(url, shoe_model)
                if review:
                    return review
            except Exception as e:
                print(f"⚠️ Error with URL {url}: {e}")
                continue
        
        return None
    
    def _generate_urls(self, shoe_model: str) -> List[str]:
        """Generate potential RunRepeat URLs for a shoe model"""
        # Clean and format shoe model name
        clean_name = self._clean_shoe_name(shoe_model)
        
        urls = [
            f"{self.base_url}/{clean_name}-review",
            f"{self.base_url}/{clean_name}-running-shoes-review",
            f"{self.base_url}/{clean_name}-basketball-shoes-review",
            f"{self.base_url}/{clean_name}",
        ]
        
        return urls
    
    def _clean_shoe_name(self, shoe_name: str) -> str:
        """Clean shoe name for URL formatting"""
        # Convert to lowercase and replace spaces/special chars with hyphens
        clean = re.sub(r'[^\w\s-]', '', shoe_name.lower())
        clean = re.sub(r'\s+', '-', clean)
        clean = re.sub(r'-+', '-', clean)
        return clean.strip('-')
    
    def _extract_review_from_url(self, url: str, shoe_model: str) -> Optional[ShoeReview]:
        """Extract review data from a RunRepeat URL"""
        response = self.session.get(url)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if this is actually a shoe review page
        if not self._is_shoe_review_page(soup):
            return None
        
        # Extract review components
        pros = self._extract_pros(soup)
        cons = self._extract_cons(soup)
        expert_verdict = self._extract_expert_verdict(soup)
        specs = self._extract_specs(soup)
        score = self._extract_score(soup)
        
        # Determine characteristics
        playstyle = self._determine_playstyle_from_content(expert_verdict, specs)
        weight_class = self._determine_weight_class_from_specs(specs)
        features = self._extract_features_from_specs(specs)
        price_range = self._extract_price_range(soup)
        
        # Combine all text
        full_text = f"{expert_verdict}\n\nPros: {', '.join(pros)}\n\nCons: {', '.join(cons)}"
        
        review = ShoeReview(
            shoe_model=shoe_model,
            source=Source.RUNREPEAT,
            title=f"RunRepeat Review: {shoe_model}",
            text=full_text,
            pros=pros,
            cons=cons,
            score=score,
            playstyle=playstyle,
            weight_class=weight_class,
            features=features,
            price_range=price_range,
            url=url,
            timestamp=datetime.now()
        )
        
        return review
    
    def _is_shoe_review_page(self, soup: BeautifulSoup) -> bool:
        """Check if the page is actually a shoe review"""
        # Look for review-specific elements
        indicators = [
            soup.find('div', class_='pros-cons'),
            soup.find('section', class_='pros-cons'),
            soup.find('div', string=re.compile(r'pros', re.I)),
            soup.find('div', string=re.compile(r'cons', re.I)),
            soup.find('div', string=re.compile(r'verdict', re.I)),
        ]
        
        return any(indicator is not None for indicator in indicators)
    
    def _extract_pros(self, soup: BeautifulSoup) -> List[str]:
        """Extract pros from the review"""
        pros = []
        
        # Multiple selectors for pros
        selectors = [
            '.pros li',
            '.pros-list li',
            '.positive-points li',
            '[data-testid="pros"] li',
            '.review-pros li'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                pros = [elem.get_text().strip() for elem in elements]
                break
        
        # Fallback: look for text patterns
        if not pros:
            pros_section = soup.find(string=re.compile(r'pros', re.I))
            if pros_section:
                parent = pros_section.find_parent()
                if parent:
                    list_items = parent.find_all('li')
                    pros = [li.get_text().strip() for li in list_items]
        
        return [p for p in pros if len(p) > 5][:5]  # Limit to 5 pros
    
    def _extract_cons(self, soup: BeautifulSoup) -> List[str]:
        """Extract cons from the review"""
        cons = []
        
        # Multiple selectors for cons
        selectors = [
            '.cons li',
            '.cons-list li',
            '.negative-points li',
            '[data-testid="cons"] li',
            '.review-cons li'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                cons = [elem.get_text().strip() for elem in elements]
                break
        
        # Fallback: look for text patterns
        if not cons:
            cons_section = soup.find(string=re.compile(r'cons', re.I))
            if cons_section:
                parent = cons_section.find_parent()
                if parent:
                    list_items = parent.find_all('li')
                    cons = [li.get_text().strip() for li in list_items]
        
        return [c for c in cons if len(c) > 5][:5]  # Limit to 5 cons
    
    def _extract_expert_verdict(self, soup: BeautifulSoup) -> str:
        """Extract expert verdict or review summary"""
        verdict = ""
        
        # Look for verdict section
        verdict_selectors = [
            '.verdict',
            '.expert-verdict',
            '.review-summary',
            '[data-testid="verdict"]',
            '.bottom-line'
        ]
        
        for selector in verdict_selectors:
            element = soup.select_one(selector)
            if element:
                verdict = element.get_text().strip()
                break
        
        # Fallback: look for text patterns
        if not verdict:
            verdict_header = soup.find(string=re.compile(r'verdict|summary|bottom line', re.I))
            if verdict_header:
                parent = verdict_header.find_parent()
                if parent:
                    # Get the next paragraph or div
                    next_elem = parent.find_next(['p', 'div'])
                    if next_elem:
                        verdict = next_elem.get_text().strip()
        
        return verdict
    
    def _extract_specs(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract technical specifications"""
        specs = {}
        
        # Look for specs table
        specs_table = soup.find('table', class_=re.compile(r'specs|specifications', re.I))
        if specs_table:
            rows = specs_table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) == 2:
                    key = cols[0].get_text().strip()
                    value = cols[1].get_text().strip()
                    specs[key] = value
        
        # Alternative: look for definition lists
        if not specs:
            dt_elements = soup.find_all('dt')
            for dt in dt_elements:
                dd = dt.find_next_sibling('dd')
                if dd:
                    key = dt.get_text().strip()
                    value = dd.get_text().strip()
                    specs[key] = value
        
        return specs
    
    def _extract_score(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract numerical score"""
        # Look for score elements
        score_selectors = [
            '.score',
            '.rating',
            '.overall-score',
            '[data-testid="score"]'
        ]
        
        for selector in score_selectors:
            element = soup.select_one(selector)
            if element:
                score_text = element.get_text().strip()
                # Extract number from text
                score_match = re.search(r'(\d+(?:\.\d+)?)', score_text)
                if score_match:
                    score = float(score_match.group(1))
                    # Normalize to 10-point scale if needed
                    if score > 10:
                        score = score / 10
                    return score
        
        return None
    
    def _determine_playstyle_from_content(self, verdict: str, specs: Dict[str, str]) -> List[Playstyle]:
        """Determine playstyle from review content"""
        content = (verdict + " " + " ".join(specs.values())).lower()
        playstyles = []
        
        guard_keywords = ['guard', 'quick', 'speed', 'agility', 'lightweight', 'responsive']
        forward_keywords = ['forward', 'versatile', 'all-around', 'balanced']
        center_keywords = ['center', 'big man', 'heavy', 'maximum cushion', 'impact']
        
        if any(keyword in content for keyword in guard_keywords):
            playstyles.append(Playstyle.GUARD)
        
        if any(keyword in content for keyword in forward_keywords):
            playstyles.append(Playstyle.FORWARD)
        
        if any(keyword in content for keyword in center_keywords):
            playstyles.append(Playstyle.CENTER)
        
        return playstyles if playstyles else [Playstyle.ALL_AROUND]
    
    def _determine_weight_class_from_specs(self, specs: Dict[str, str]) -> WeightClass:
        """Determine weight class from specs"""
        weight_info = " ".join(specs.values()).lower()
        
        if any(keyword in weight_info for keyword in ['lightweight', 'light', 'minimal']):
            return WeightClass.LIGHT
        elif any(keyword in weight_info for keyword in ['heavy', 'maximum', 'bulky']):
            return WeightClass.HEAVY
        else:
            return WeightClass.MEDIUM
    
    def _extract_features_from_specs(self, specs: Dict[str, str]) -> List[str]:
        """Extract features from specifications"""
        features = []
        
        feature_mapping = {
            'cushioning': ['cushion', 'zoom', 'air', 'boost', 'react'],
            'support': ['support', 'stability', 'lockdown'],
            'traction': ['traction', 'outsole', 'rubber', 'grip'],
            'breathability': ['breathable', 'mesh', 'ventilation'],
            'durability': ['durable', 'wear', 'long-lasting']
        }
        
        specs_text = " ".join(specs.values()).lower()
        
        for feature, keywords in feature_mapping.items():
            if any(keyword in specs_text for keyword in keywords):
                features.append(feature)
        
        return features
    
    def _extract_price_range(self, soup: BeautifulSoup) -> Optional[List[float]]:
        """Extract price information"""
        price_selectors = [
            '.price',
            '.cost',
            '.msrp',
            '[data-testid="price"]'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                # Extract price numbers
                price_matches = re.findall(r'\$(\d+(?:\.\d+)?)', price_text)
                if price_matches:
                    prices = [float(p) for p in price_matches]
                    if len(prices) == 1:
                        # Single price - create range
                        price = prices[0]
                        return [price * 0.9, price * 1.1]
                    elif len(prices) == 2:
                        # Price range
                        return sorted(prices)
        
        return None 