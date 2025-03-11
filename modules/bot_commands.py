from discord.ext import commands
from db.repositories import (
    create_or_get_user, create_query, create_recommended_item, get_wishlist_items_for_user
)
from sqlalchemy.orm import Session
import discord
from prompted_response import PromptedResponse
from views.recommended_item_embed import recommended_item_embed
from modules.user_profile import UserProfileAnalyzer
import matplotlib.pyplot as plt
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import numpy as np
from utils.loading_animations import LoadingAnimations
from utils.recommendation_service import RecommendationService
import asyncio

def register_commands(bot, db: Session):
    # Initialize the recommendation service
    recommendation_service = RecommendationService()

    @bot.command()
    async def hello(ctx: commands.Context):
        """Simple test command to check if the bot is responding."""
        await ctx.send("Hello! Your bot is working!")

    @bot.command()
    async def find(ctx: commands.Context, *, query: str):
        """
        Search for product recommendations based on your description.
        Example: !find wireless headphones under $100
        """
        
        async def do_search():
            prompted_response = PromptedResponse()
            try:
                # Get the user
                user = create_or_get_user(db, discord_id=str(ctx.author.id), username=ctx.author.name)
                
                # Create an embed with a loading animation
                loading_embed, _ = LoadingAnimations.get_loading_embed(
                    operation="search", 
                    message=f"🔍 **Searching for:** {query}\n\nScouring the web for the best options..."
                )
                status_message = await ctx.send(embed=loading_embed)
                
                # Parse the query into structured data
                parsed_query = await prompted_response.parse_query(query)
                # if parsed_query.get("item") is None:
                #     await status_message.delete()
                #     await ctx.send("Sorry, I couldn't understand what you're looking for. Please try rephrasing your query.")
                #     return
                
                # Log the query
                new_query = create_query(
                    db,
                    user_id=user.id,
                    query_type="prompted",
                    raw_query=query,
                    interpreted_query=parsed_query
                )
                
                # Get product recommendations
                region = "us"  # Default to US region
                recommendations = await prompted_response.run_prompted_response(query, region)
                
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
                
                # Trigger the background recommendation service
                # This doesn't await the result, so it won't block execution
                asyncio.create_task(recommendation_service.update_recommendations(db, user.id))
                
            finally:
                db.close()
        
        bot.loop.create_task(do_search())

    @bot.command()
    async def multi_find(ctx: commands.Context, *, query: str):
        """
        Find a complete set of complementary items based on your query.
        Example: !multi_find ski equipment
        """
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
                
                # Trigger the background recommendation service
                # This doesn't await the result, so it won't block execution
                asyncio.create_task(recommendation_service.update_recommendations(db, user.id))
                
            finally:
                db.close()
        
        bot.loop.create_task(do_multi_search())

    @bot.command()
    async def wishlist(ctx: commands.Context):
        """
        Shows all items you've added to your wishlist.
        Can be used in DMs for privacy.
        """
        
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
        Uses conversation context to recommend something interesting.
        """
        
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
                
                loading_embed, _ = LoadingAnimations.get_loading_embed(
                    operation="surprise", 
                    message="🔍 **Reading the room and finding something you might like...**"
                )
                status_message = await ctx.send(embed=loading_embed)
                
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

    @bot.command(name="wrapped")
    async def wrapped(ctx: commands.Context):
        """
        Analyzes your past searches and creates a visual shopping profile.
        Shows shopping personality, interests, and preferred price ranges.
        """
        
        # Send initial status message with loading animation
        loading_embed, _ = LoadingAnimations.get_loading_embed(
            operation="profile", 
            message="📊 **Analyzing your shopping profile...**\n\nLooking at your past searches and preferences to create your shopper profile."
        )
        status_message = await ctx.send(embed=loading_embed)
        
        try:
            # Get the user
            user = create_or_get_user(db, discord_id=str(ctx.author.id), username=ctx.author.name)
            
            # Create profile analyzer
            profile_analyzer = UserProfileAnalyzer(db)
            
            # Get user's past queries and recommended items
            user_history = profile_analyzer.get_user_history(user.id)
            
            if not user_history['queries']:
                await status_message.delete()
                await ctx.send("You don't have any shopping history yet! Try searching for some products first with the `!find` command.")
                return
            
            # Generate profile analysis using LLM
            prompted_response = PromptedResponse()
            profile_insights = await prompted_response.generate_user_profile(user_history)
            
            # Create visual representation of shopping interests
            # Create a pie chart of product categories
            if profile_insights['category_breakdown']:
                plt.figure(figsize=(8, 5))
                categories = list(profile_insights['category_breakdown'].keys())
                values = list(profile_insights['category_breakdown'].values())
                
                # Color palette
                colors = plt.cm.Pastel1(np.linspace(0, 1, len(categories)))
                
                plt.pie(values, labels=categories, autopct='%1.1f%%', startangle=140, colors=colors)
                plt.axis('equal')
                plt.title('Your Shopping Interests')
                
                # Save the pie chart to a bytes buffer
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                
                # Create file object for discord attachment
                chart_file = discord.File(buf, filename="shopping_profile.png")
                
                # Prepare shopping personality image
                personality_img = profile_analyzer.generate_personality_image(profile_insights['shopping_personality'])
                personality_buf = io.BytesIO()
                personality_img.save(personality_buf, format='PNG')
                personality_buf.seek(0)
                personality_file = discord.File(personality_buf, filename="personality.png")
                
                # Create embed with insights
                embed = discord.Embed(
                    title=f"🛍️ {ctx.author.name}'s Shopping Profile",
                    description=profile_insights['summary'],
                    color=discord.Color.blue()
                )
                
                # Add fields with insights
                embed.add_field(
                    name="Shopping Personality", 
                    value=profile_insights['shopping_personality']['type'], 
                    inline=False
                )
                embed.add_field(
                    name="Price Sensitivity", 
                    value=f"${profile_insights['avg_price_interest']:.2f} average interest • {profile_insights['price_range_preference']}", 
                    inline=True
                )
                embed.add_field(
                    name="Activity", 
                    value=f"{len(user_history['queries'])} searches • {profile_insights['activity_level']}", 
                    inline=True
                )
                
                # Top brands section if available
                if profile_insights['preferred_brands']:
                    embed.add_field(
                        name="Favorite Brands", 
                        value=" • ".join(profile_insights['preferred_brands'][:3]), 
                        inline=False
                    )
                
                # Recommendations based on profile
                embed.add_field(
                    name="Personalized Recommendations", 
                    value="\n".join([f"• {item}" for item in profile_insights['recommendations'][:3]]), 
                    inline=False
                )
                
                # Set thumbnail to personality image
                embed.set_thumbnail(url="attachment://personality.png")
                # Set the pie chart as the main image
                embed.set_image(url="attachment://shopping_profile.png")
                
                # Add timestamp and footer
                embed.timestamp = datetime.now()
                embed.set_footer(text="Profile updated")
                
                # Delete the loading message and send the final embed
                await status_message.delete()
                await ctx.send(embed=embed, files=[chart_file, personality_file])
            else:
                # Simple embed if not enough data for visualization
                embed = discord.Embed(
                    title=f"🛍️ {ctx.author.name}'s Shopping Profile",
                    description="Not enough shopping data to generate a detailed profile. Keep searching for products!",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Searches So Far", value=str(len(user_history['queries'])), inline=True)
                embed.add_field(name="Next Steps", value="Try using `!find` to look for products you're interested in!", inline=True)
                
                await status_message.delete()
                await ctx.send(embed=embed)
                
        except Exception as e:
            print(f"Error in profile command: {str(e)}")
            await status_message.delete()
            await ctx.send(f"Sorry, I encountered an error while analyzing your profile: {str(e)}")

    @bot.command()
    async def all_commands(ctx: commands.Context):
        """
        Shows all available commands and their descriptions.
        Learn what the shopping assistant can do for you.
        """
        
        # Create an embed for the help menu
        embed = discord.Embed(
            title="🛍️ PricePal - Commands",
            description="Here are all the available commands you can use:",
            color=discord.Color.blue()
        )
        
        # Get all commands from the bot
        command_list = sorted(bot.commands, key=lambda x: x.name)
        
        # Add each command to the embed with improved formatting
        for command in command_list:
            # Skip the help command itself to avoid recursion
            if command.name == "help":
                continue
            
            # Extract the first line of the docstring as a short description
            description = command.help.split('\n')[0] if command.help else "No description available."
            
            # Add command emoji based on the command name
            emoji = "❓"  # Default emoji
            if "find" in command.name:
                emoji = "🔍"
            elif command.name == "wishlist":
                emoji = "❤️"
            elif command.name == "wrapped":
                emoji = "📊"
            elif command.name == "feeling_lucky":
                emoji = "✨"
            elif command.name == "hello":
                emoji = "👋"
            
            # Add field for each command with emoji and formatted name
            embed.add_field(
                name=f"{emoji} `!{command.name}`",
                value=f"**{description}**",
                inline=False
            )
        
        # Add a footer with additional info
        embed.set_footer(text="Type !all_commands to see this message again | Use commands in this server or in DMs")
        
        
        # Send the embed
        await ctx.send(embed=embed)