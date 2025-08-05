import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

from src.core.models import SearchResult, Source

class WebSearch:
    """Autonomous web search for basketball shoe information"""
    
    def __init__(self, serpapi_key: Optional[str] = None):
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_KEY")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Trusted sources with priority scores
        self.trusted_sources = {
            "runrepeat.com": 5,
            "reddit.com/r/BBallShoes": 4,
            "youtube.com": 3,
            "nike.com": 2,
            "adidas.com": 2,
            "footlocker.com": 2,
            "champssports.com": 2
        }
        
        # Cache for search results
        self.cache = {}
        self.cache_duration = timedelta(hours=24)
    
    def search(self, query: str, search_type: str = "general") -> List[SearchResult]:
        """
        Perform web search based on query type
        
        Args:
            query: Search query
            search_type: Type of search ("price", "review", "general")
        
        Returns:
            List of search results
        """
        # Check cache first
        cache_key = f"{query}_{search_type}"
        if cache_key in self.cache:
            cached_time, results = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return results
        
        if search_type == "price":
            results = self._search_prices(query)
        elif search_type == "review":
            results = self._search_reviews(query)
        else:
            results = self._search_general(query)
        
        # Cache results
        self.cache[cache_key] = (datetime.now(), results)
        
        return results
    
    def _search_prices(self, query: str) -> List[SearchResult]:
        """Search for current prices"""
        # Extract shoe model from query
        shoe_model = self._extract_shoe_model(query)
        if not shoe_model:
            return []
        
        search_queries = [
            f'"{shoe_model}" price site:nike.com OR site:adidas.com OR site:footlocker.com',
            f'"{shoe_model}" price site:champssports.com OR site:finishline.com',
            f'"{shoe_model}" price site:amazon.com'
        ]
        
        results = []
        for search_query in search_queries:
            try:
                if self.serpapi_key:
                    serp_results = self._serpapi_search(search_query)
                    results.extend(serp_results)
                else:
                    # Fallback to direct scraping
                    direct_results = self._direct_price_search(shoe_model)
                    results.extend(direct_results)
            except Exception as e:
                print(f"⚠️ Error searching prices: {e}")
        
        return self._filter_and_rank_results(results, "price")
    
    def _search_reviews(self, query: str) -> List[SearchResult]:
        """Search for reviews"""
        search_queries = [
            f'{query} site:reddit.com/r/BBallShoes',
            f'{query} site:runrepeat.com',
            f'{query} review site:youtube.com'
        ]
        
        results = []
        for search_query in search_queries:
            try:
                if self.serpapi_key:
                    serp_results = self._serpapi_search(search_query)
                    results.extend(serp_results)
                else:
                    # Fallback to direct scraping
                    direct_results = self._direct_review_search(query)
                    results.extend(direct_results)
            except Exception as e:
                print(f"⚠️ Error searching reviews: {e}")
        
        return self._filter_and_rank_results(results, "review")
    
    def _search_general(self, query: str) -> List[SearchResult]:
        """General search for any basketball shoe information"""
        search_query = f'{query} basketball shoes review price'
        
        try:
            if self.serpapi_key:
                return self._serpapi_search(search_query)
            else:
                return self._direct_general_search(query)
        except Exception as e:
            print(f"⚠️ Error in general search: {e}")
            return []
    
    def _serpapi_search(self, query: str) -> List[SearchResult]:
        """Search using SerpAPI"""
        if not self.serpapi_key:
            return []
        
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self.serpapi_key,
            "num": 10
        }
        
        response = self.session.get(url, params=params)
        data = response.json()
        
        results = []
        if "organic_results" in data:
            for result in data["organic_results"]:
                search_result = SearchResult(
                    title=result.get("title", ""),
                    snippet=result.get("snippet", ""),
                    url=result.get("link", ""),
                    source=self._extract_source(result.get("link", "")),
                    trust_score=self._calculate_trust_score(result.get("link", ""))
                )
                results.append(search_result)
        
        return results
    
    def _direct_price_search(self, shoe_model: str) -> List[SearchResult]:
        """Direct scraping for prices (fallback method)"""
        results = []
        
        # Try Nike.com
        try:
            nike_url = f"https://www.nike.com/search?q={shoe_model.replace(' ', '%20')}"
            response = self.session.get(nike_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract price information (this would need to be customized based on Nike's structure)
            price_elements = soup.find_all(class_=re.compile(r'price', re.I))
            for element in price_elements[:3]:
                results.append(SearchResult(
                    title=f"{shoe_model} - Nike.com",
                    snippet=f"Price: {element.get_text().strip()}",
                    url=nike_url,
                    source="nike.com",
                    trust_score=2.0
                ))
        except Exception as e:
            print(f"⚠️ Error scraping Nike: {e}")
        
        return results
    
    def _direct_review_search(self, query: str) -> List[SearchResult]:
        """Direct scraping for reviews (fallback method)"""
        results = []
        
        # Try Reddit
        try:
            reddit_url = f"https://www.reddit.com/r/BBallShoes/search.json?q={query}&restrict_sr=on&sort=relevance&t=year"
            response = self.session.get(reddit_url)
            data = response.json()
            
            if "data" in data and "children" in data["data"]:
                for post in data["data"]["children"][:5]:
                    post_data = post["data"]
                    results.append(SearchResult(
                        title=post_data.get("title", ""),
                        snippet=post_data.get("selftext", "")[:200] + "...",
                        url=f"https://reddit.com{post_data.get('permalink', '')}",
                        source="reddit.com/r/BBallShoes",
                        trust_score=4.0
                    ))
        except Exception as e:
            print(f"⚠️ Error scraping Reddit: {e}")
        
        return results
    
    def _direct_general_search(self, query: str) -> List[SearchResult]:
        """Direct general search (fallback method)"""
        # This would implement basic web scraping
        # For now, return empty list
        return []
    
    def _extract_shoe_model(self, query: str) -> Optional[str]:
        """Extract shoe model from query"""
        # Simple pattern matching
        patterns = [
            r'(Nike|Adidas|Jordan|Under Armour|Puma)\s+[\w\d\s]+?(?=\s|$)',
            r'([A-Z][a-z]+\s+\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_source(self, url: str) -> str:
        """Extract source domain from URL"""
        import urllib.parse
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    def _calculate_trust_score(self, url: str) -> float:
        """Calculate trust score based on source"""
        source = self._extract_source(url)
        
        for trusted_source, score in self.trusted_sources.items():
            if trusted_source in source:
                return float(score)
        
        return 1.0  # Default trust score
    
    def _filter_and_rank_results(self, results: List[SearchResult], search_type: str) -> List[SearchResult]:
        """Filter and rank search results"""
        # Remove duplicates
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # Sort by trust score
        unique_results.sort(key=lambda x: x.trust_score, reverse=True)
        
        # Return top results
        return unique_results[:10]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_duration_hours": self.cache_duration.total_seconds() / 3600
        } 