from utils.interpret_chat import interpret_chat
from prompted_response import PromptedResponse
from utils.shopping_keywords import is_potential_shopping_message
from views.recommended_item_embed import recommended_item_embed
from sqlalchemy.orm import Session
from db.repositories import (
    create_or_get_user, create_query, create_recommended_item
)
from utils.loading_animations import LoadingAnimations

class ShoppingHandler:
    def __init__(self, db: Session):
        self.prompted_response = PromptedResponse()
        self.db = db

    async def process_message(self, message, message_context, cooldown_manager):
        """Process a message for shopping intent."""
    
        if not is_potential_shopping_message(message.content):
            print("Not a potential shopping message.")
            return
            
        channel_id = message.channel.id
        
        if not cooldown_manager.should_call_llm(channel_id):
            print("Not enough time has passed since last LLM call.")
            return
            
        query = await interpret_chat(message_context)
        
        if not query.get("item"):
            print("No item in query.")
            return
            
        # Check if duplicate query
        if cooldown_manager.is_duplicate_query(channel_id, query["item"]):
            print("Same query detected; skipping new search.")
            return
            
        # Search and display results
   
        
        loading_embed, _ = LoadingAnimations.get_loading_embed(
            operation="search", 
            message="🛒 **Detected Shopping Intent**. Searching for products..."
        )
        status_message = await message.channel.send(embed=loading_embed)
        region = "us"
        
        # Database integration - Store user, query and recommendations
        try:
            # Create or get user record
            user = create_or_get_user(
                self.db, 
                discord_id=str(message.author.id), 
                username=message.author.name
            )
            
            # Create query record
            interpreted = await self.prompted_response.parse_query(message.content)
            print(f"Interpreted: {interpreted}")
            unprompted_query = create_query(
                self.db,
                user_id=user.id,
                query_type="unprompted",
                raw_query=message.content,
                interpreted_query=interpreted
            )
            
            # Get recommendations
            recommendations = await self.prompted_response.run_prompted_response(interpreted, region)
            print("--------------------------------")
            print(f"Recommendations: {recommendations}")
            print("--------------------------------")
            # Delete the loading status message
            await status_message.delete()
            
            if recommendations:
                for shopping_item in recommendations:
                    # Create recommendation record in DB
                    rec_link = shopping_item.link if shopping_item.link is not None else ""
                    rec_price = float(shopping_item.price.replace('$', '')) if shopping_item.price is not None else 0.0
                    rec_item = create_recommended_item(
                        self.db,
                        query_id=unprompted_query.id,
                        item_name=shopping_item.item_name,
                        vendor="VendorX",
                        link=rec_link,
                        price=rec_price,
                        metadata=shopping_item.model_dump()
                    )
                    
                    # Display recommendation
                    await recommended_item_embed(
                        None, 
                        message, 
                        shopping_item.item_name, 
                        shopping_item.price, 
                        shopping_item.link,
                        query_id=unprompted_query.id, 
                        rec_item_id=rec_item.id
                    )
            else:
                await message.channel.send("No recommendations found.")
        except Exception as e:
            print(f"Error in database operations: {e}")
            # Delete the loading status message even if there was an error
            try:
                await status_message.delete()
            except:
                pass
                
            # Still try to show recommendations without DB if there was an error
            recommendations = await self.prompted_response.run_prompted_response(query, region)
            if recommendations:
                for shopping_item in recommendations:
                    await recommended_item_embed(
                        None, 
                        message, 
                        shopping_item.item_name, 
                        shopping_item.price, 
                        shopping_item.link,
                        query_id=unprompted_query.id,
                        rec_item_id=rec_item.id
                    )
            else:
                await message.channel.send("No recommendations found.")
