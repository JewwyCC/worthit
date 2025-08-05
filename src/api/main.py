from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os

from src.core.models import UserQuery, RecommendationResponse, Playstyle
from src.core.router import QueryRouter
from src.rag.vector_db import VectorDatabase
from src.web.search import WebSearch
from src.llm.reasoning import LLMReasoning

# Initialize FastAPI app
app = FastAPI(
    title="Basketball Shoe Recommendation System",
    description="AI-powered basketball shoe recommendations using RAG and web search",
    version="2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
router = QueryRouter()
vector_db = VectorDatabase()
web_search = WebSearch()
llm_reasoning = LLMReasoning()

class QueryRequest(BaseModel):
    query: str
    playstyle: Optional[str] = None
    budget: Optional[float] = None
    foot_type: Optional[str] = None
    injury_concerns: Optional[List[str]] = None

class QueryResponse(BaseModel):
    recommendations: List[dict]
    reasoning: str
    sources: List[str]
    confidence_score: float
    search_used: bool
    processing_time: float

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Basketball Shoe Recommendation System v2.0",
        "status": "healthy",
        "components": {
            "router": "active",
            "vector_db": "active",
            "web_search": "active",
            "llm_reasoning": "active"
        }
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "vector_db": vector_db.get_stats(),
        "web_search": web_search.get_cache_stats(),
        "router": {
            "known_models": len(router.known_models)
        }
    }

@app.post("/recommend", response_model=QueryResponse)
async def recommend_shoes(request: QueryRequest):
    """
    Get basketball shoe recommendations based on user query
    
    This endpoint:
    1. Routes the query to appropriate processing method
    2. Retrieves relevant data from RAG database
    3. Performs web search if needed
    4. Generates recommendations using LLM reasoning
    """
    import time
    start_time = time.time()
    
    try:
        # Convert request to UserQuery
        user_query = UserQuery(
            query=request.query,
            playstyle=Playstyle(request.playstyle) if request.playstyle else None,
            budget=request.budget,
            foot_type=request.foot_type,
            injury_concerns=request.injury_concerns
        )
        
        # Step 1: Route query
        route_type = router.route_query(user_query)
        print(f"🔍 Query routed to: {route_type}")
        
        # Step 2: Get RAG documents
        filters = router.get_search_filters(user_query)
        rag_documents = vector_db.similarity_search(
            query=user_query.query,
            k=5,
            filters=filters
        )
        print(f"📚 Retrieved {len(rag_documents)} documents from RAG")
        
        # Step 3: Web search if needed
        search_results = None
        if route_type in ["web_search", "hybrid"]:
            # Determine search type based on query
            if any(keyword in user_query.query.lower() for keyword in ['$', 'price', 'cost']):
                search_type = "price"
            elif any(keyword in user_query.query.lower() for keyword in ['review', 'opinion', 'thoughts']):
                search_type = "review"
            else:
                search_type = "general"
            
            search_results = web_search.search(user_query.query, search_type)
            print(f"🌐 Retrieved {len(search_results)} web search results")
        
        # Step 4: Generate recommendation
        response = llm_reasoning.generate_recommendation(
            query=user_query,
            rag_documents=rag_documents,
            search_results=search_results
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Convert to response format
        recommendations = []
        for rec in response.recommendations:
            recommendations.append({
                "shoe_model": rec.shoe_model,
                "source": rec.source.value,
                "title": rec.title,
                "pros": rec.pros,
                "cons": rec.cons,
                "score": rec.score,
                "playstyle": [p.value for p in rec.playstyle],
                "price_range": rec.price_range,
                "features": rec.features,
                "url": rec.url
            })
        
        return QueryResponse(
            recommendations=recommendations,
            reasoning=response.reasoning,
            sources=response.sources,
            confidence_score=response.confidence_score,
            search_used=response.search_used,
            processing_time=processing_time
        )
    
    except Exception as e:
        print(f"❌ Error processing recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_review")
async def add_review(review_data: dict):
    """Add a new shoe review to the RAG database"""
    try:
        from src.core.models import ShoeReview, Source, Playstyle, WeightClass
        
        # Convert dict to ShoeReview object
        review = ShoeReview(
            shoe_model=review_data["shoe_model"],
            source=Source(review_data["source"]),
            title=review_data["title"],
            text=review_data["text"],
            pros=review_data.get("pros", []),
            cons=review_data.get("cons", []),
            score=review_data.get("score"),
            playstyle=[Playstyle(p) for p in review_data.get("playstyle", [])],
            weight_class=WeightClass(review_data["weight_class"]) if review_data.get("weight_class") else None,
            price_range=review_data.get("price_range"),
            features=review_data.get("features", []),
            url=review_data.get("url")
        )
        
        # Add to vector database
        vector_db.add_from_reviews([review])
        
        return {"message": "Review added successfully", "shoe_model": review.shoe_model}
    
    except Exception as e:
        print(f"❌ Error adding review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_database(query: str, k: int = 5):
    """Search the RAG database directly"""
    try:
        documents = vector_db.similarity_search(query, k)
        
        results = []
        for doc in documents:
            results.append({
                "id": doc.id,
                "text": doc.text[:200] + "..." if len(doc.text) > 200 else doc.text,
                "metadata": doc.metadata
            })
        
        return {"query": query, "results": results}
    
    except Exception as e:
        print(f"❌ Error searching database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 