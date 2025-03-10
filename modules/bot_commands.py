from discord.ext import commands
from db.repositories import (
    create_or_get_user, create_query, create_recommended_item, get_wishlist_items_for_user
)
from sqlalchemy.orm import Session
import discord

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
                        rec_price = float(shopping_item.price.replace('$', '').replace(",", "")) if shopping_item.price is not None else 0.0
                        
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

    @bot.command()
    async def multi_find(ctx: commands.Context, *, query: str):
        """
        Find a complete set of complementary items based on your query.
        Example: !multi_find ski equipment
        """
        from prompted_response import PromptedResponse
        from views.recommended_item_embed import recommended_item_embed
        
        async def do_multi_search():
            prompted_response = PromptedResponse()
            try:
                # Log or retrieve the user
                user = create_or_get_user(db, discord_id=str(ctx.author.id), username=ctx.author.name)
                
                # Parse the query to get a set of items
                interpreted_set = await prompted_response.parse_multi_item_query(query)
                
                # Log the query in database
                new_query = create_query(
                    db,
                    user_id=user.id,
                    query_type="prompted",
                    raw_query=query,
                    interpreted_query=interpreted_set
                )
                
                status_message = await ctx.send("🛒 **Fetching complementary items...**")
                region = "us"
                
                # Get recommendations for each item in the set (up to 4)
                item_set = interpreted_set.get("items", [])[:4]  # Limit to 4 items
                
                if not item_set:
                    await ctx.send("Couldn't identify items in your query. Try something like '!multi_search ski equipment'")
                    await status_message.delete()
                    return
                    
                await ctx.send(f"Finding items for: **{', '.join(item_set)}**")
                
                for item in item_set:
                    recommendations = await prompted_response.run_prompted_response(
                        {"item_name": item, "number_of_results": 1},  # Just get 1 result per item
                        region
                    )
                    
                    if recommendations:
                        shopping_item = recommendations[0]
                        # Store recommendation in database
                        rec_link = shopping_item.link if shopping_item.link is not None else ""
                        rec_price = float(shopping_item.price.replace('$', '').replace(",", "")) if shopping_item.price is not None else 0.0
                        
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
                        await ctx.send(f"No recommendations found for {item}.")
                    
                await status_message.delete()  # Remove the status message once done
            finally:
                db.close()
        
        bot.loop.create_task(do_multi_search())

    @bot.command()
    async def wishlist(ctx: commands.Context):
        """
        Shows all items you've added to your wishlist.
        Can be used in DMs for privacy.
        """
        from views.recommended_item_embed import recommended_item_embed
        
        async def get_wishlist():
            try:
                # Get the user
                user = create_or_get_user(db, discord_id=str(ctx.author.id), username=ctx.author.name)
                
                # Get all wishlist items for the user
                wishlist_items = get_wishlist_items_for_user(db, user.id)
                
                if not wishlist_items:
                    await ctx.send("Your wishlist is empty. Add items using the ❤️ button on product recommendations!")
                    return
                    
                await ctx.send(f"**Your Wishlist** ({len(wishlist_items)} items)")
                
                for item in wishlist_items:
                    # Create item embeds for each wishlist item
                    await recommended_item_embed(
                        ctx,
                        None,
                        item.item_name,
                        str(item.price),
                        item.link,
                        query_id=item.query_id,
                        rec_item_id=item.id
                    )
                    
            finally:
                db.close()
        
        # Only process in DMs or when invoked in a server
        if isinstance(ctx.channel, discord.DMChannel) or not hasattr(ctx, 'guild'):
            bot.loop.create_task(get_wishlist())
        else:
            await ctx.send("For privacy, please DM me with `!wishlist` to see your saved items.")

    @bot.command(name="feeling_lucky")
    async def feeling_lucky(ctx: commands.Context):
        """
        Analyzes recent chat and suggests a surprising item you might like.
        """
        from prompted_response import PromptedResponse
        from views.recommended_item_embed import recommended_item_embed
        
        async def lucky_search():
            from modules.message_history import MessageHistory
            prompted_response = PromptedResponse()
            
            try:
                # Get the user
                user = create_or_get_user(db, discord_id=str(ctx.author.id), username=ctx.author.name)
                
                # Get recent message history from the channel
                message_texts = []
                async for msg in ctx.channel.history(limit=50):
                    if not msg.author.bot:
                        message_texts.append(msg.content)
                
                # If there's not enough context, use a generic approach
                if len(message_texts) < 3:
                    await ctx.send("Not enough chat history. I'll suggest something random!")
                    message_texts = ["I'm looking for something interesting"]
                
                status_message = await ctx.send("🔍 **Reading the room and finding something you might like...**")
                
                # Use OpenAI to analyze the conversation and suggest a surprising item
                surprise_item = await prompted_response.generate_surprise_recommendation(message_texts)
                
                # Log the query
                new_query = create_query(
                    db,
                    user_id=user.id,
                    query_type="unprompted",
                    raw_query="Generated from chat context",
                    interpreted_query={"surprise_item": surprise_item}
                )
                
                # Get recommendation for the surprise item
                region = "us"
                recommendations = await prompted_response.run_prompted_response(
                    {"item_name": surprise_item, "number_of_results": 1},
                    region
                )
                
                await status_message.delete()
                
                if recommendations:
                    shopping_item = recommendations[0]
                    
                    # Store recommendation in database
                    rec_link = shopping_item.link if shopping_item.link is not None else ""
                    rec_price = float(shopping_item.price.replace('$', '').replace(",", "")) if shopping_item.price is not None else 0.0
                    
                    rec_item = create_recommended_item(
                        db,
                        query_id=new_query.id,
                        item_name=shopping_item.item_name,
                        vendor="Unknown" if shopping_item.source is None else shopping_item.source,
                        link=rec_link,
                        price=rec_price,
                        metadata=shopping_item.model_dump()
                    )
                    
                    await ctx.send(f"✨ **Based on the chat, you might be interested in:** {surprise_item}")
                    
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
                    await ctx.send(f"I thought you might like **{surprise_item}**, but couldn't find any good recommendations.")
                    
            finally:
                db.close()
        
        bot.loop.create_task(lucky_search())