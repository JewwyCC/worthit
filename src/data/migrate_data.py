import json
import os
from typing import List, Dict, Any
from datetime import datetime

from src.core.models import ShoeReview, Source, Playstyle, WeightClass
from src.rag.vector_db import VectorDatabase

def migrate_existing_data():
    """Migrate existing basketball shoe data to the new RAG format"""
    
    # Initialize vector database
    vector_db = VectorDatabase()
    
    # Load existing data
    existing_data = load_existing_data()
    
    # Convert to ShoeReview objects
    reviews = convert_to_reviews(existing_data)
    
    # Add to vector database
    print(f"🔄 Adding {len(reviews)} reviews to vector database...")
    vector_db.add_from_reviews(reviews)
    
    print("✅ Data migration completed!")
    print(f"📊 Database stats: {vector_db.get_stats()}")

def load_existing_data() -> Dict[str, Any]:
    """Load existing basketball shoe data"""
    data_sources = []
    
    # Try to load basketball_shoes.json
    if os.path.exists("basketball_shoes.json"):
        try:
            with open("basketball_shoes.json", "r") as f:
                data = json.load(f)
                data_sources.append(("basketball_shoes.json", data))
                print(f"📁 Loaded basketball_shoes.json with {len(data)} entries")
        except Exception as e:
            print(f"⚠️ Error loading basketball_shoes.json: {e}")
    
    # Try to load from worthit_research_automation.py output
    if os.path.exists("sneaker_reviews.json"):
        try:
            with open("sneaker_reviews.json", "r") as f:
                data = json.load(f)
                data_sources.append(("sneaker_reviews.json", data))
                print(f"📁 Loaded sneaker_reviews.json")
        except Exception as e:
            print(f"⚠️ Error loading sneaker_reviews.json: {e}")
    
    return data_sources

def convert_to_reviews(data_sources: List[tuple]) -> List[ShoeReview]:
    """Convert existing data to ShoeReview objects"""
    reviews = []
    
    for source_name, data in data_sources:
        if source_name == "basketball_shoes.json":
            reviews.extend(convert_basketball_shoes_data(data))
        elif source_name == "sneaker_reviews.json":
            reviews.extend(convert_sneaker_reviews_data(data))
    
    return reviews

def convert_basketball_shoes_data(data: List[Dict[str, Any]]) -> List[ShoeReview]:
    """Convert basketball_shoes.json data to ShoeReview objects"""
    reviews = []
    
    for item in data:
        try:
            # Extract basic information
            shoe_model = item.get("name", item.get("model", "Unknown"))
            brand = item.get("brand", "Unknown")
            full_name = f"{brand} {shoe_model}" if brand != "Unknown" else shoe_model
            
            # Extract pros and cons
            pros = []
            cons = []
            
            if "pros" in item:
                pros = item["pros"] if isinstance(item["pros"], list) else [item["pros"]]
            
            if "cons" in item:
                cons = item["cons"] if isinstance(item["cons"], list) else [item["cons"]]
            
            # Extract score
            score = None
            if "rating" in item:
                score = float(item["rating"])
            elif "score" in item:
                score = float(item["score"])
            
            # Extract price range
            price_range = None
            if "price" in item:
                price = item["price"]
                if isinstance(price, (int, float)):
                    price_range = [price * 0.8, price * 1.2]  # Estimate range
                elif isinstance(price, str):
                    # Try to extract number from price string
                    import re
                    price_match = re.search(r'\$?(\d+)', price)
                    if price_match:
                        price_val = float(price_match.group(1))
                        price_range = [price_val * 0.8, price_val * 1.2]
            
            # Determine playstyle based on features
            playstyle = []
            features = item.get("features", [])
            if isinstance(features, str):
                features = [features]
            
            if any(keyword in str(features).lower() for keyword in ["guard", "quick", "lightweight"]):
                playstyle.append(Playstyle.GUARD)
            if any(keyword in str(features).lower() for keyword in ["forward", "versatile", "all-around"]):
                playstyle.append(Playstyle.FORWARD)
            if any(keyword in str(features).lower() for keyword in ["center", "heavy", "cushioning"]):
                playstyle.append(Playstyle.CENTER)
            
            if not playstyle:
                playstyle = [Playstyle.ALL_AROUND]
            
            # Determine weight class
            weight_class = None
            if any(keyword in str(features).lower() for keyword in ["lightweight", "minimal"]):
                weight_class = WeightClass.LIGHT
            elif any(keyword in str(features).lower() for keyword in ["heavy", "maximum"]):
                weight_class = WeightClass.HEAVY
            else:
                weight_class = WeightClass.MEDIUM
            
            # Create review
            review = ShoeReview(
                shoe_model=full_name,
                source=Source.RUNREPEAT,  # Assume RunRepeat for existing data
                title=f"Review of {full_name}",
                text=item.get("description", item.get("review", f"Review for {full_name}")),
                pros=pros,
                cons=cons,
                score=score,
                playstyle=playstyle,
                weight_class=weight_class,
                price_range=price_range,
                features=features if isinstance(features, list) else [],
                url=item.get("url", ""),
                timestamp=datetime.now()
            )
            
            reviews.append(review)
            
        except Exception as e:
            print(f"⚠️ Error converting item {item.get('name', 'Unknown')}: {e}")
            continue
    
    return reviews

def convert_sneaker_reviews_data(data: Dict[str, Any]) -> List[ShoeReview]:
    """Convert sneaker_reviews.json data to ShoeReview objects"""
    reviews = []
    
    # Process YouTube data
    if "youtube" in data:
        for video in data["youtube"]:
            try:
                review = ShoeReview(
                    shoe_model=video.get("title", "Unknown"),
                    source=Source.YOUTUBE,
                    title=video.get("title", ""),
                    text=video.get("transcript", ""),
                    pros=[],  # Would need to extract from transcript
                    cons=[],  # Would need to extract from transcript
                    score=None,
                    playstyle=[Playstyle.ALL_AROUND],  # Default
                    weight_class=WeightClass.MEDIUM,  # Default
                    price_range=None,
                    features=[],
                    url=f"https://youtube.com/watch?v={video.get('video_id', '')}",
                    timestamp=datetime.now()
                )
                reviews.append(review)
            except Exception as e:
                print(f"⚠️ Error converting YouTube video: {e}")
    
    # Process Reddit data
    if "reddit" in data:
        for post in data["reddit"]:
            try:
                review = ShoeReview(
                    shoe_model=post.get("title", "Unknown"),
                    source=Source.REDDIT,
                    title=post.get("title", ""),
                    text=post.get("text", ""),
                    pros=post.get("shoe_models", []),  # Use shoe models as features
                    cons=[],
                    score=None,
                    playstyle=[Playstyle.ALL_AROUND],  # Default
                    weight_class=WeightClass.MEDIUM,  # Default
                    price_range=None,
                    features=post.get("shoe_models", []),
                    url=post.get("metadata", {}).get("url", ""),
                    timestamp=datetime.now()
                )
                reviews.append(review)
            except Exception as e:
                print(f"⚠️ Error converting Reddit post: {e}")
    
    # Process RunRepeat data
    if "runrepeat" in data:
        for review_data in data["runrepeat"]:
            try:
                review = ShoeReview(
                    shoe_model=review_data.get("shoe_model", "Unknown"),
                    source=Source.RUNREPEAT,
                    title=f"RunRepeat Review: {review_data.get('shoe_model', 'Unknown')}",
                    text="",  # Would need to combine pros/cons/expert_verdict
                    pros=review_data.get("pros", []),
                    cons=review_data.get("cons", []),
                    score=None,
                    playstyle=[Playstyle.ALL_AROUND],  # Default
                    weight_class=WeightClass.MEDIUM,  # Default
                    price_range=None,
                    features=list(review_data.get("specs", {}).keys()),
                    url="",
                    timestamp=datetime.now()
                )
                reviews.append(review)
            except Exception as e:
                print(f"⚠️ Error converting RunRepeat review: {e}")
    
    return reviews

if __name__ == "__main__":
    migrate_existing_data() 