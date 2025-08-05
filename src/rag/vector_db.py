import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime

from src.core.models import ShoeDocument, ShoeReview, Source

class VectorDatabase:
    """FAISS-based vector database for shoe reviews"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.encoder = SentenceTransformer(model_name)
        self.index = None
        self.documents: List[ShoeDocument] = []
        self.index_path = "data/faiss_index"
        self.documents_path = "data/documents.json"
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index and documents"""
        if os.path.exists(self.index_path) and os.path.exists(self.documents_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.documents_path, 'r') as f:
                    docs_data = json.load(f)
                    self.documents = [ShoeDocument(**doc) for doc in docs_data]
                print(f"✅ Loaded {len(self.documents)} documents from existing index")
            except Exception as e:
                print(f"⚠️ Error loading index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        dimension = self.encoder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        print("✅ Created new FAISS index")
    
    def add_documents(self, documents: List[ShoeDocument]):
        """Add documents to the vector database"""
        if not documents:
            return
        
        # Generate embeddings
        texts = [doc.text for doc in documents]
        embeddings = self.encoder.encode(texts, show_progress_bar=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store documents
        self.documents.extend(documents)
        
        # Save index and documents
        self._save_index()
        print(f"✅ Added {len(documents)} documents to vector database")
    
    def similarity_search(self, query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[ShoeDocument]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            filters: Metadata filters to apply
        
        Returns:
            List of similar documents
        """
        # Check if we have any documents
        if len(self.documents) == 0:
            return []
        
        # Encode query
        query_embedding = self.encoder.encode([query])
        
        # Search in FAISS
        scores, indices = self.index.search(query_embedding.astype('float32'), k * 2)  # Get more results for filtering
        
        # Apply filters if provided
        if filters:
            filtered_docs = []
            for idx in indices[0]:
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    if self._apply_filters(doc, filters):
                        filtered_docs.append(doc)
                        if len(filtered_docs) >= k:
                            break
            return filtered_docs
        
        # Return top k documents
        results = []
        for idx in indices[0]:
            if idx < len(self.documents):
                results.append(self.documents[idx])
                if len(results) >= k:
                    break
        
        return results
    
    def _apply_filters(self, doc: ShoeDocument, filters: Dict[str, Any]) -> bool:
        """Apply metadata filters to a document"""
        metadata = doc.metadata
        
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            if isinstance(value, dict) and "$lt" in value:
                # Price range filter
                if not isinstance(metadata[key], (int, float)) or metadata[key] >= value["$lt"]:
                    return False
            elif isinstance(value, list):
                # List filter (e.g., playstyle)
                if not any(item in metadata[key] for item in value):
                    return False
            else:
                # Exact match filter
                if metadata[key] != value:
                    return False
        
        return True
    
    def _save_index(self):
        """Save FAISS index and documents to disk"""
        try:
            faiss.write_index(self.index, self.index_path)
            
            # Save documents as JSON
            docs_data = [doc.dict() for doc in self.documents]
            with open(self.documents_path, 'w') as f:
                json.dump(docs_data, f, indent=2, default=str)
            
            print(f"✅ Saved index with {len(self.documents)} documents")
        except Exception as e:
            print(f"⚠️ Error saving index: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.encoder.get_sentence_embedding_dimension()
        }
    
    def add_from_reviews(self, reviews: List[ShoeReview]):
        """Add documents from ShoeReview objects"""
        documents = []
        for review in reviews:
            # Create document text from review
            text_parts = [review.title, review.text]
            if review.pros:
                text_parts.append("Pros: " + ", ".join(review.pros))
            if review.cons:
                text_parts.append("Cons: " + ", ".join(review.cons))
            
            text = " ".join(text_parts)
            
            # Create metadata
            metadata = {
                "shoe_model": review.shoe_model,
                "source": review.source.value,
                "playstyle": [p.value for p in review.playstyle],
                "weight_class": review.weight_class.value if review.weight_class else None,
                "price_range": review.price_range,
                "features": review.features,
                "score": review.score,
                "url": review.url,
                "timestamp": review.timestamp.isoformat()
            }
            
            doc = ShoeDocument(
                id=f"{review.source.value}_{review.shoe_model}_{review.timestamp.timestamp()}",
                text=text,
                metadata=metadata
            )
            documents.append(doc)
        
        self.add_documents(documents) 