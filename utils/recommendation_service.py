import asyncio
from sqlalchemy.orm import Session
from db.repositories import get_recent_queries_by_user, get_wishlist_items_for_user, delete_all_recommendations_for_user, insert_recommendation_for_user
from services.openai_service import OpenAIService
from prompted_response import PromptedResponse
from config import OPENAI_API_KEY
import json
from datetime import datetime
import traceback


class RecommendationService:
    def __init__(self):
        self.openai_service = OpenAIService(OPENAI_API_KEY)
        self.prompted_response = PromptedResponse()
        
    async def update_recommendations(self, db: Session, user_id: str):
        """
        Asynchronously generates personalized recommendations based on user history
        and updates the Supabase recommendation table.
        
        This runs in the background and doesn't block the main bot functionality.
        """
        try:
            print(f"[RECOMMENDATION SERVICE] Started for user {user_id} at {datetime.now()}")
            
            # Get user's recent search history (last 20 queries)
            print(f"[RECOMMENDATION SERVICE] Fetching recent queries for user {user_id}")
            recent_queries = get_recent_queries_by_user(db, user_id, limit=20)
            print(f"[RECOMMENDATION SERVICE] Found {len(recent_queries)} recent queries")
            
            # Get user's wishlist items (last 20)
            wishlist_items = get_wishlist_items_for_user(db, user_id, limit=20)
            
            # Format the data for OpenAI
            query_data = [
                {
                    "query_text": q.raw_query if q.raw_query else "Unknown query",
                    "interpreted": q.interpreted_query
                } for q in recent_queries
            ]
            
            wishlist_data = [
                {
                    "item_name": item.item_name,
                    "price": str(item.price),
                    "vendor": item.vendor
                } for item in wishlist_items
            ]
            
            # Prepare prompt for OpenAI
            prompt = f"""
            Based on this user's recent search history and wishlist items, suggest 5 products they might be interested in.
            
            Recent Searches:
            {json.dumps(query_data, indent=2)}
            
            Wishlist Items:
            {json.dumps(wishlist_data, indent=2)}
            
            Generate 5 specific product recommendations (not categories) that this user might like.
            Each recommendation should be specific enough to search for (e.g., "wireless noise-canceling headphones" not just "headphones").
            Return as a JSON array of strings with just the product names. so it would be a json object with a key "recommendations" and a list of strings. It is paramount that you get this right
            """
            
            # Call OpenAI to get recommendations
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.reasoning_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            
            content = self.openai_service.strip_markdown(response.choices[0].message.content)
            recommendation_data = json.loads(content)
            recommended_items = recommendation_data.get("recommendations", [])
            
            if not recommended_items and isinstance(recommendation_data, list):
                # Handle if OpenAI returned an array directly
                recommended_items = recommendation_data[:5]
            
            # Ensure we have at least some recommendations even if OpenAI fails
            if not recommended_items:
                recommended_items = ["smart watch", "wireless earbuds", "portable charger", 
                                    "laptop sleeve", "phone case"]
            
            # Limit to 5 recommendations
            recommended_items = recommended_items[:5]
            print(f"Generated recommendations: {recommended_items}")
            
            # First, delete all existing recommendations for this user
            delete_all_recommendations_for_user(db, user_id)
            
            # Search for each recommended item IN PARALLEL
            region = "us"
            
            # Define an async function to search and process a single item
            async def search_and_process_item(item):
                search_results = await self.prompted_response.run_prompted_response(
                    {"item_name": item, "number_of_results": 1},
                    region
                )
                
                if search_results:
                    result = search_results[0]
                    # Format the price as a number for the database
                    price = 0.0
                    if result.price:
                        try:
                            price = float(result.price.replace('$', '').replace(',', ''))
                        except ValueError:
                            price = 0.0
                    
                    return {
                        "user_id": user_id,
                        "item_name": result.item_name,
                        "vendor": result.source if result.source else "Unknown",
                        "link": result.link if result.link else "",
                        "price": price,
                        "metadata": result.model_dump() if hasattr(result, "model_dump") else {}
                    }
                return None
            
            # Run all searches in parallel
            search_tasks = [search_and_process_item(item) for item in recommended_items]
            all_results = await asyncio.gather(*search_tasks)
            
            # Filter out None results and insert into database
            valid_results = [result for result in all_results if result]
            for result in valid_results:
                insert_recommendation_for_user(
                    db,
                    **result
                )
            
            print(f"[RECOMMENDATION SERVICE] Completed successfully for user {user_id} at {datetime.now()}")
            
        except Exception as e:
            print(f"[RECOMMENDATION SERVICE] Error: {e}")
            traceback.print_exc() 