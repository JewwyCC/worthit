from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class Playstyle(str, Enum):
    GUARD = "guard"
    FORWARD = "forward"
    CENTER = "center"
    ALL_AROUND = "all_around"

class WeightClass(str, Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"

class Source(str, Enum):
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    RUNREPEAT = "runrepeat"
    WEB_SEARCH = "web_search"

class ShoeDocument(BaseModel):
    """Document structure for RAG database"""
    id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ShoeReview(BaseModel):
    """Structured shoe review data"""
    shoe_model: str
    source: Source
    title: str
    text: str
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    score: Optional[float] = None
    playstyle: List[Playstyle] = Field(default_factory=list)
    weight_class: Optional[WeightClass] = None
    price_range: Optional[List[float]] = None
    features: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class UserQuery(BaseModel):
    """User query structure"""
    query: str
    playstyle: Optional[Playstyle] = None
    budget: Optional[float] = None
    foot_type: Optional[str] = None
    injury_concerns: Optional[List[str]] = None

class RecommendationResponse(BaseModel):
    """System response structure"""
    recommendations: List[ShoeReview]
    reasoning: str
    sources: List[str]
    confidence_score: float
    search_used: bool = False

class SearchResult(BaseModel):
    """Web search result structure"""
    title: str
    snippet: str
    url: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    trust_score: float = Field(ge=0.0, le=1.0) 