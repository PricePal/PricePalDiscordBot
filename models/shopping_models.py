from typing import List, Optional
from pydantic import BaseModel

class ShoppingItem(BaseModel):
    item_name: str

class Recommendation(BaseModel):
    item_name: str
    price: Optional[str] = None
    link: Optional[str] = None
    source: Optional[str] = None

class StructuredResponse(BaseModel):
    recommendations: List[ShoppingItem]

class QueryRequest(BaseModel):
    item_name: str
    type: Optional[str] = None
    price_range: Optional[str] = None
    number_of_results: int = 3 