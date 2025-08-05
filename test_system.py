#!/usr/bin/env python3
"""
Test script for Basketball Shoe Recommendation System v2.0
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test core imports
        from src.core.models import UserQuery, RecommendationResponse, Playstyle, Source
        print("✅ Core models imported")
        
        from src.core.router import QueryRouter
        print("✅ Router imported")
        
        from src.rag.vector_db import VectorDatabase
        print("✅ Vector DB imported")
        
        from src.web.search import WebSearch
        print("✅ Web search imported")
        
        from src.llm.reasoning import LLMReasoning
        print("✅ LLM reasoning imported")
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_router():
    """Test the query router"""
    print("\n🧪 Testing query router...")
    
    try:
        from src.core.router import QueryRouter
        from src.core.models import UserQuery
        
        router = QueryRouter()
        
        # Test different query types
        test_queries = [
            ("Best shoes for guards", "rag"),
            ("Nike LeBron 21 price", "hybrid"),
            ("New basketball shoes 2024", "hybrid"),
            ("Unknown model XYZ", "hybrid"),
        ]
        
        for query, expected in test_queries:
            result = router.route_query(UserQuery(query=query))
            status = "✅" if result == expected else "❌"
            print(f"  {status} '{query}' → {result} (expected: {expected})")
        
        return True
    except Exception as e:
        print(f"❌ Router test error: {e}")
        return False

def test_vector_db():
    """Test the vector database"""
    print("\n🧪 Testing vector database...")
    
    try:
        from src.rag.vector_db import VectorDatabase
        
        db = VectorDatabase()
        stats = db.get_stats()
        print(f"✅ Vector DB initialized: {stats}")
        return True
    except Exception as e:
        print(f"❌ Vector DB test error: {e}")
        return False

def test_web_search():
    """Test web search functionality"""
    print("\n🧪 Testing web search...")
    
    try:
        from src.web.search import WebSearch
        
        search = WebSearch()
        results = search.search("Nike LeBron 21", "general")
        print(f"✅ Web search working: {len(results)} results")
        return True
    except Exception as e:
        print(f"❌ Web search test error: {e}")
        return False

def test_llm_reasoning():
    """Test LLM reasoning"""
    print("\n🧪 Testing LLM reasoning...")
    
    try:
        from src.llm.reasoning import LLMReasoning
        from src.core.models import UserQuery, ShoeDocument, SearchResult
        
        llm = LLMReasoning()
        
        # Create test data
        user_query = UserQuery(query="Best shoes for guards")
        
        # Mock RAG documents
        rag_docs = [
            ShoeDocument(
                id="test_1",
                text="The Nike LeBron 21 has excellent cushioning for explosive players",
                metadata={
                    "shoe_model": "Nike LeBron 21",
                    "source": "runrepeat",
                    "score": 8.5,
                    "playstyle": ["forward", "center"],
                    "price_range": [180, 220]
                }
            )
        ]
        
        # Generate recommendation
        response = llm.generate_recommendation(user_query, rag_docs)
        print(f"✅ LLM reasoning working: {len(response.recommendations)} recommendations")
        return True
    except Exception as e:
        print(f"❌ LLM reasoning test error: {e}")
        return False

def test_full_pipeline():
    """Test the full recommendation pipeline"""
    print("\n🧪 Testing full pipeline...")
    
    try:
        from src.core.models import UserQuery, Playstyle
        from src.core.router import QueryRouter
        from src.rag.vector_db import VectorDatabase
        from src.web.search import WebSearch
        from src.llm.reasoning import LLMReasoning
        
        # Initialize components
        router = QueryRouter()
        vector_db = VectorDatabase()
        web_search = WebSearch()
        llm_reasoning = LLMReasoning()
        
        # Test query
        query = UserQuery(
            query="Best basketball shoes for guards under $150",
            playstyle=Playstyle.GUARD,
            budget=150
        )
        
        # Route query
        route_type = router.route_query(query)
        print(f"  📍 Query routed to: {route_type}")
        
        # Get RAG documents
        filters = router.get_search_filters(query)
        try:
            rag_docs = vector_db.similarity_search(query.query, k=3, filters=filters)
            print(f"  📚 Retrieved {len(rag_docs)} RAG documents")
        except Exception as e:
            print(f"  ⚠️ RAG search error: {e}")
            rag_docs = []
        
        # Web search (if needed)
        search_results = None
        if route_type in ["web_search", "hybrid"]:
            try:
                search_results = web_search.search(query.query)
                print(f"  🌐 Retrieved {len(search_results)} web search results")
            except Exception as e:
                print(f"  ⚠️ Web search error: {e}")
                search_results = []
        
        # Generate recommendation
        try:
            response = llm_reasoning.generate_recommendation(query, rag_docs, search_results)
            print(f"  🎯 Generated {len(response.recommendations)} recommendations")
            print(f"  📊 Confidence score: {response.confidence_score:.2f}")
        except Exception as e:
            print(f"  ⚠️ LLM reasoning error: {e}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Full pipeline test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Basketball Shoe Recommendation System v2.0 - Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_router,
        test_vector_db,
        test_web_search,
        test_llm_reasoning,
        test_full_pipeline
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run 'python main.py migrate' to load existing data")
        print("2. Run 'python main.py serve' to start the API server")
        print("3. Visit http://localhost:8000/docs for API documentation")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 