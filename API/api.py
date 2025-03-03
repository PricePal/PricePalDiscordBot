# api.py
from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from prompted_response import PromptedResponse
from models.shopping_models import QueryRequest, Recommendation
from db.database import SessionLocal
from db.repositories import (
    create_or_get_user, 
    create_query, 
    create_recommended_item
)

app = FastAPI(title="Shopping Recommendations API")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Request Models
class UserRequest(BaseModel):
    user_id: str
    username: str

class RecommendationRequest(BaseModel):
    query: str
    region: str = "us"
    user_id: Optional[str] = None
    username: Optional[str] = None

# Response Models
class ApiResponse(BaseModel):
    success: bool
    data: Optional[List[Recommendation]] = None
    error: Optional[str] = None

# Endpoints
@app.post("/recommendations", response_model=ApiResponse)
async def get_recommendations(
    request: RecommendationRequest, 
    db: Session = Depends(get_db)
):
    """Get product recommendations based on a query string."""
    prompted_response = PromptedResponse()
    
    try:
        # Handle optional user tracking
        user = None
        if request.user_id and request.username:
            user = create_or_get_user(
                db, 
                discord_id=request.user_id, 
                username=request.username
            )
        
        # Parse query
        interpreted = await prompted_response.parse_query(request.query)
        
        # Create query record if user is provided
        if user:
            new_query = create_query(
                db,
                user_id=user.id,
                query_type="prompted",
                raw_query=request.query,
                interpreted_query=interpreted
            )
            query_id = new_query.id
        else:
            query_id = None
        
        # Get recommendations
        recommendations = await prompted_response.run_prompted_response(
            request.query, 
            request.region
        )
        
        # Store recommendations in DB if user is provided
        if user and query_id:
            for item in recommendations:
                rec_price = float(item.price) if item.price else 0.0
                create_recommended_item(
                    db,
                    query_id=query_id,
                    item_name=item.item_name,
                    vendor="Unknown" if item.source is None else item.source,
                    link=item.link if item.link else "",
                    price=rec_price,
                    metadata=item.dict()
                )
        
        return {
            "success": True,
            "data": recommendations
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/parse-query")
async def parse_query(query: str):
    """Parse a natural language query into structured data."""
    prompted_response = PromptedResponse()
    try:
        result = await prompted_response.parse_query(query)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Run with: uvicorn api:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)