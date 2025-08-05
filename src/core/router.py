import re
from typing import List, Dict, Any
from src.core.models import UserQuery, Source

class QueryRouter:
    """Routes queries to appropriate processing method (RAG vs Web Search)"""
    
    def __init__(self):
        self.price_keywords = ['$', 'price', 'cost', 'cheap', 'expensive', 'budget', 'sale']
        self.temporal_keywords = ['2024', '2025', 'new', 'latest', 'recent', 'release']
        self.known_models = self._load_known_models()
    
    def _load_known_models(self) -> List[str]:
        """Load known shoe models from database"""
        # This would typically load from a database
        return [
            "Nike LeBron 21", "Nike KD 16", "Nike GT Jump 3", "Nike GT Cut 3",
            "Adidas Harden Vol 7", "Adidas Dame 8", "Adidas Trae Young 3",
            "Jordan Luka 2", "Jordan Zion 3", "Jordan Tatum 2",
            "Under Armour Curry 11", "Under Armour Embiid 2",
            "Puma MB.03", "Puma All-Pro Nitro"
        ]
    
    def route_query(self, query: UserQuery) -> str:
        """
        Route query to appropriate processing method
        
        Returns:
            - "rag": Use only RAG database
            - "web_search": Use only web search
            - "hybrid": Use both RAG and web search
        """
        query_text = query.query.lower()
        
        # Check for price-related queries
        if any(keyword in query_text for keyword in self.price_keywords):
            return "hybrid"
        
        # Check for temporal/new model queries
        if any(keyword in query_text for keyword in self.temporal_keywords):
            return "hybrid"
        
        # Check if specific models are mentioned
        mentioned_models = self._extract_shoe_models(query_text)
        
        if not mentioned_models:
            # No specific models mentioned, use RAG for general recommendations
            return "rag"
        
        # Check if all mentioned models are known
        unknown_models = [model for model in mentioned_models if not self._is_known_model(model)]
        
        if unknown_models:
            return "hybrid"
        
        # All models are known, use RAG
        return "rag"
    
    def _extract_shoe_models(self, query_text: str) -> List[str]:
        """Extract shoe model names from query text"""
        # Simple pattern matching - could be enhanced with NER
        patterns = [
            r'(Nike|Adidas|Jordan|Under Armour|Puma)\s+[\w\d\s]+?(?=\s|$)',
            r'([A-Z][a-z]+\s+\d+)',  # Generic pattern like "LeBron 21"
        ]
        
        models = []
        for pattern in patterns:
            matches = re.findall(pattern, query_text, re.IGNORECASE)
            models.extend(matches)
        
        return list(set(models))
    
    def _is_known_model(self, model: str) -> bool:
        """Check if a model exists in known models database"""
        model_lower = model.lower()
        return any(known.lower() in model_lower or model_lower in known.lower() 
                  for known in self.known_models)
    
    def get_search_filters(self, query: UserQuery) -> Dict[str, Any]:
        """Generate filters for RAG search based on query"""
        filters = {}
        
        if query.playstyle:
            filters["playstyle"] = query.playstyle.value
        
        if query.budget:
            filters["price_range"] = {"$lt": query.budget}
        
        if query.foot_type:
            filters["foot_type"] = query.foot_type
        
        if query.injury_concerns:
            filters["injury_support"] = query.injury_concerns
        
        return filters 