from discord.ext import commands
from db.repositories import (
    create_or_get_user, create_query, create_recommended_item
)
from sqlalchemy.orm import Session

def register_commands(bot, db: Session):
    @bot.command()
    async def hello(ctx: commands.Context):
        """Simple test command."""
        await ctx.send("Hello! Your bot is working!")

    @bot.command()
    async def find(ctx: commands.Context, *, query: str):
        """
        The !find command: searches for product recommendations.
        """
        from prompted_response import PromptedResponse
        from views.recommended_item_embed import recommended_item_embed
        
        async def do_search():
            prompted_response = PromptedResponse()
            try:
                # Log or retrieve the user
                user = create_or_get_user(db, discord_id=str(ctx.author.id), username=ctx.author.name)
                
                # Interpret the query
                interpreted = await prompted_response.parse_query(query)
                
                # Log the query in database
                new_query = create_query(
                    db,
                    user_id=user.id,
                    query_type="prompted",
                    raw_query=query,
                    interpreted_query=interpreted
                )
                
                status_message = await ctx.send("🛒 **Fetching recommendations...**")
                region = "us"
                recommendations = await prompted_response.run_prompted_response(query, region)
                # print(f"Recommendations: {recommendations}")
                
                if recommendations:
                    for shopping_item in recommendations:
                        # Store recommendation in database
                        rec_link = shopping_item.link if shopping_item.link is not None else ""
                        rec_price = float(shopping_item.price) if shopping_item.price is not None else 0.0
                        
                        rec_item = create_recommended_item(
                            db,
                            query_id=new_query.id,
                            item_name=shopping_item.item_name,
                            vendor="Unknown" if shopping_item.source is None else shopping_item.source,
                            link=rec_link,
                            price=rec_price,
                            metadata=shopping_item.model_dump()
                        )
                        
                        await recommended_item_embed(
                            ctx, 
                            None, 
                            shopping_item.item_name, 
                            shopping_item.price, 
                            rec_link,
                            query_id=new_query.id,
                            rec_item_id=rec_item.id
                        )
                else:
                    await ctx.send("No recommendations found.")
                    
                await status_message.delete()  # Remove the status message once done
            finally:
                db.close()
        
        bot.loop.create_task(do_search())