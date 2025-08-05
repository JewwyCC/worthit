import openai
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

from src.core.models import (
    UserQuery, RecommendationResponse, ShoeReview, 
    ShoeDocument, SearchResult, Source
)

class LLMReasoning:
    """LLM-based reasoning engine for basketball shoe recommendations"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if self.api_key:
            openai.api_key = self.api_key
        
        # System prompt for basketball shoe expertise
        self.system_prompt = """You are a basketball shoe expert assistant with deep knowledge of performance, fit, and value. 

Your expertise includes:
- Performance characteristics (cushioning, traction, support)
- Fit considerations (wide feet, narrow feet, sizing)
- Injury prevention and support features
- Price-to-performance ratios
- Brand comparisons and alternatives

Always:
1. Cite specific sources for claims
2. Warn about potential fit issues
3. Consider the user's specific needs (playstyle, budget, injuries)
4. Provide actionable recommendations
5. Mention alternatives if the primary recommendation doesn't fit

Response format:
[Summary of recommendation]
- [Shoe Model] (Score: X/10)
  - Pros: [specific benefits]
  - Cons: [specific drawbacks] 
  - Best for: [playstyle/player type]
  - Price: [current price if available]
  - Source: [URL or source]
  - Warning: [fit/sizing notes if applicable]

[Additional recommendations if applicable]
"""
    
    def generate_recommendation(
        self, 
        query: UserQuery, 
        rag_documents: List[ShoeDocument],
        search_results: Optional[List[SearchResult]] = None
    ) -> RecommendationResponse:
        """
        Generate recommendation using RAG data and optional web search results
        
        Args:
            query: User query
            rag_documents: Retrieved documents from vector database
            search_results: Optional web search results
        
        Returns:
            RecommendationResponse with structured recommendations
        """
        # Prepare context from RAG documents
        rag_context = self._prepare_rag_context(rag_documents)
        
        # Prepare context from web search results
        web_context = ""
        if search_results:
            web_context = self._prepare_web_context(search_results)
        
        # Create user prompt
        user_prompt = self._create_user_prompt(query, rag_context, web_context)
        
        # Generate response
        try:
            response = self._call_llm(user_prompt)
            recommendations = self._parse_recommendations(response)
            
            return RecommendationResponse(
                recommendations=recommendations,
                reasoning=response,
                sources=self._extract_sources(rag_documents, search_results),
                confidence_score=self._calculate_confidence(rag_documents, search_results),
                search_used=bool(search_results)
            )
        
        except Exception as e:
            print(f"⚠️ Error generating recommendation: {e}")
            return self._fallback_recommendation(query, rag_documents)
    
    def _prepare_rag_context(self, documents: List[ShoeDocument]) -> str:
        """Prepare context from RAG documents"""
        if not documents:
            return "No relevant shoe reviews found in database."
        
        context_parts = []
        for i, doc in enumerate(documents[:5]):  # Limit to top 5 documents
            metadata = doc.metadata
            context_parts.append(f"""
Document {i+1}:
Shoe: {metadata.get('shoe_model', 'Unknown')}
Source: {metadata.get('source', 'Unknown')}
Score: {metadata.get('score', 'N/A')}/10
Playstyle: {', '.join(metadata.get('playstyle', []))}
Price Range: ${metadata.get('price_range', ['N/A'])[0] if metadata.get('price_range') else 'N/A'}
Content: {doc.text[:500]}...
""")
        
        return "\n".join(context_parts)
    
    def _prepare_web_context(self, search_results: List[SearchResult]) -> str:
        """Prepare context from web search results"""
        if not search_results:
            return ""
        
        context_parts = ["Recent web search results:"]
        for i, result in enumerate(search_results[:3]):  # Limit to top 3 results
            context_parts.append(f"""
Web Result {i+1}:
Title: {result.title}
Source: {result.source} (Trust Score: {result.trust_score}/5)
Content: {result.snippet}
URL: {result.url}
""")
        
        return "\n".join(context_parts)
    
    def _create_user_prompt(self, query: UserQuery, rag_context: str, web_context: str) -> str:
        """Create the user prompt for the LLM"""
        prompt_parts = [
            f"User Query: {query.query}",
        ]
        
        # Add user preferences
        if query.playstyle:
            prompt_parts.append(f"Playstyle: {query.playstyle.value}")
        if query.budget:
            prompt_parts.append(f"Budget: ${query.budget}")
        if query.foot_type:
            prompt_parts.append(f"Foot Type: {query.foot_type}")
        if query.injury_concerns:
            prompt_parts.append(f"Injury Concerns: {', '.join(query.injury_concerns)}")
        
        prompt_parts.append("\nDatabase Information:")
        prompt_parts.append(rag_context)
        
        if web_context:
            prompt_parts.append("\n" + web_context)
        
        prompt_parts.append("\nPlease provide a detailed recommendation based on the above information.")
        
        return "\n".join(prompt_parts)
    
    def _call_llm(self, user_prompt: str) -> str:
        """Call the LLM API"""
        if not self.api_key:
            # Fallback to mock response for testing
            return self._mock_response(user_prompt)
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Error calling LLM API: {e}")
            return self._mock_response(user_prompt)
    
    def _mock_response(self, user_prompt: str) -> str:
        """Mock response for testing without API key"""
        return """
Based on your query, here are my recommendations:

- Nike LeBron 21 (Score: 8.5/10)
  - Pros: Excellent cushioning, great for explosive players, durable construction
  - Cons: Heavy, expensive, runs slightly large
  - Best for: Forwards and centers who need maximum cushioning
  - Price: $200
  - Source: RunRepeat.com
  - Warning: Consider going 0.5 size down

- Adidas Harden Vol 7 (Score: 8/10)
  - Pros: Great traction, lightweight, good for guards
  - Cons: Cushioning could be better for heavier players
  - Best for: Guards and quick players
  - Price: $130
  - Source: Reddit/r/BBallShoes
  - Warning: Runs true to size
"""
    
    def _parse_recommendations(self, response: str) -> List[ShoeReview]:
        """Parse LLM response into structured ShoeReview objects"""
        # This is a simplified parser - in production, you'd want more robust parsing
        recommendations = []
        
        # Simple pattern matching to extract recommendations
        import re
        pattern = r'- ([^(]+) \(Score: ([\d.]+)/10\)'
        matches = re.findall(pattern, response)
        
        for shoe_model, score in matches:
            # Extract pros and cons using regex
            pros_match = re.search(r'Pros: ([^C]+)', response)
            cons_match = re.search(r'Cons: ([^B]+)', response)
            
            pros = pros_match.group(1).strip().split(', ') if pros_match else []
            cons = cons_match.group(1).strip().split(', ') if cons_match else []
            
            review = ShoeReview(
                shoe_model=shoe_model.strip(),
                source=Source.WEB_SEARCH,
                title=f"Recommendation for {shoe_model.strip()}",
                text=response,
                pros=pros,
                cons=cons,
                score=float(score),
                timestamp=datetime.now()
            )
            recommendations.append(review)
        
        return recommendations
    
    def _extract_sources(self, rag_documents: List[ShoeDocument], search_results: Optional[List[SearchResult]]) -> List[str]:
        """Extract source URLs from documents and search results"""
        sources = []
        
        # Add RAG document sources
        for doc in rag_documents:
            if doc.metadata.get('url'):
                sources.append(doc.metadata['url'])
        
        # Add web search sources
        if search_results:
            for result in search_results:
                sources.append(result.url)
        
        return list(set(sources))  # Remove duplicates
    
    def _calculate_confidence(self, rag_documents: List[ShoeDocument], search_results: Optional[List[SearchResult]]) -> float:
        """Calculate confidence score based on available data"""
        confidence = 0.0
        
        # Base confidence from RAG documents
        if rag_documents:
            confidence += min(len(rag_documents) * 0.2, 0.6)  # Max 0.6 from RAG
        
        # Additional confidence from web search
        if search_results:
            avg_trust = sum(r.trust_score for r in search_results) / len(search_results)
            confidence += min(avg_trust * 0.1, 0.4)  # Max 0.4 from web search
        
        return min(confidence, 1.0)
    
    def _fallback_recommendation(self, query: UserQuery, rag_documents: List[ShoeDocument]) -> RecommendationResponse:
        """Fallback recommendation when LLM fails"""
        # Create basic recommendation from RAG documents
        recommendations = []
        
        for doc in rag_documents[:3]:
            metadata = doc.metadata
            review = ShoeReview(
                shoe_model=metadata.get('shoe_model', 'Unknown'),
                source=Source(metadata.get('source', 'unknown')),
                title=f"Database recommendation for {metadata.get('shoe_model', 'Unknown')}",
                text=doc.text[:200] + "...",
                score=metadata.get('score', 7.0),
                timestamp=datetime.now()
            )
            recommendations.append(review)
        
        return RecommendationResponse(
            recommendations=recommendations,
            reasoning="Generated from database information due to LLM unavailability.",
            sources=[doc.metadata.get('url', '') for doc in rag_documents if doc.metadata.get('url')],
            confidence_score=0.5,
            search_used=False
        ) 