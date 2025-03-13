from utils.interpret_chat import interpret_chat
from prompted_response import PromptedResponse
from utils.shopping_keywords import is_potential_shopping_message
from views.recommended_item_embed import recommended_item_embed
from sqlalchemy.orm import Session
from db.repositories import (
    create_or_get_user, create_query, create_recommended_item
)
from utils.loading_animations import LoadingAnimations
from typing import List, Callable
import discord

class ShoppingHandler:
    def __init__(self, db_getter: Callable[[], Session]):
        self.prompted_response = PromptedResponse()
        self.get_db = db_getter  # Store the factory function

    async def process_message(self, message: discord.Message, context: List[str], cooldown_manager):
        """Process a message for shopping intent."""
    
        if not is_potential_shopping_message(message.content):
            print("Not a potential shopping message.")
            return
            
        channel_id = message.channel.id
        
        if not cooldown_manager.should_call_llm(channel_id):
            print("Not enough time has passed since last LLM call.")
            return
            
        query = await interpret_chat(context)
        
        if not query.get("item"):
            print("No item in query.")
            return
        
        loading_embed, _ = LoadingAnimations.get_loading_embed(
            operation="search", 
            message="🛒 **Detected Shopping Intent**. Searching for products..."
        )
        status_message = await message.channel.send(embed=loading_embed)
        region = "us"
        
        # Get a fresh database connection
        db = self.get_db()
        unprompted_query = None
        rec_item = None
        
        try:
            # Create or get user record
            user = create_or_get_user(
                db, 
                discord_id=str(message.author.id), 
                username=message.author.name
            )
            
            # Create query record
            interpreted = await self.prompted_response.parse_query(message.content)
            print(f"Interpreted: {interpreted}")
            unprompted_query = create_query(
                db,
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
                    try:
                        # Clean price string and convert to float
                        price_str = shopping_item.price if shopping_item.price is not None else "0.0"
                        price_str = price_str.replace('$', '').replace(',', '')  # Remove $ and commas
                        rec_price = float(price_str)
                        
                        rec_item = create_recommended_item(
                            db,
                            query_id=unprompted_query.id,
                            item_name=shopping_item.item_name,
                            vendor="Unknown" if shopping_item.source is None else shopping_item.source,
                            link=shopping_item.link if shopping_item.link is not None else "",
                            price=rec_price,
                            metadata=shopping_item.model_dump()
                        )

                        await recommended_item_embed(
                            None, 
                            message,
                            shopping_item.item_name,
                            shopping_item.price,
                            shopping_item.link if shopping_item.link else "",
                            query_id=unprompted_query.id,
                            rec_item_id=rec_item.id
                        )
                    except Exception as e:
                        print(f"Error processing recommendation: {e}")
                        continue  # Skip this item and continue with others
            else:
                await message.channel.send("No recommendations found.")
        except Exception as e:
            print(f"Error in database operations: {e}")
            db.rollback()  # Rollback on error
            # Delete the loading status message even if there was an error
            try:
                await status_message.delete()
            except:
                pass
                
            # Still try to show recommendations without DB
            try:
                recommendations = await self.prompted_response.run_prompted_response(query, region)
                if recommendations and unprompted_query and unprompted_query.id:
                    for shopping_item in recommendations:
                        await recommended_item_embed(
                            None, 
                            message, 
                            shopping_item.item_name, 
                            shopping_item.price, 
                            shopping_item.link,
                            query_id=unprompted_query.id,
                            rec_item_id=rec_item.id if rec_item else None
                        )
                else:
                    await message.channel.send("No recommendations found.")
            except Exception as inner_e:
                print(f"Error showing recommendations without DB: {inner_e}")
                await message.channel.send("Sorry, I encountered an error while processing your request.")
        finally:
            db.close()  # Always close the connection
