import os
import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
from time import time
import tracemalloc

# Import your local modules
from interpret_chat import interpret_chat
from prompted_response import PromptedResponse
from shopping_keywords import is_potential_shopping_message

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Create an instance of our PromptedResponse class
prompted_response = PromptedResponse()

# ------------------------
# 1) Cooldown Config
# ------------------------
channel_last_called = {}
COOLDOWN_SECONDS = 30
last_searched_query = {}

tracemalloc.start()



async def should_call_llm(channel_id: int) -> bool:
    """Returns True if enough time has passed since last LLM call for this channel."""
    now = time()
    if channel_id in channel_last_called:
        last_called = channel_last_called[channel_id]
        if now - last_called < COOLDOWN_SECONDS:
            return False
    channel_last_called[channel_id] = now
    return True

# ------------------------
# 3) Store Recent Messages (for context)
# ------------------------
recent_messages = {}  # {channel_id: [last X messages]}
MAX_CONTEXT = 5

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

async def recommended_item_embed(ctx: commands.Context | None, message: discord.Message | None, item_name: str, price: str, link: str):
    # Create an embed
    embed = discord.Embed(
        title= item_name,
        color=discord.Color.blue()
    )
    embed.add_field(name="Price", value=price, inline=True)
    embed.add_field(name="Link", value=link, inline=False)

    class ShoppingItemView(View):
        @discord.ui.button(label="Add to Wishlist", style=discord.ButtonStyle.success, emoji="❤️")
        async def on_wishlist_click(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("You added this to your wishlist!", ephemeral=True)

        @discord.ui.button(label="Dislike", style=discord.ButtonStyle.danger, emoji="👎")
        async def on_dislike_click(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("You disliked this item!", ephemeral=True)

    view = ShoppingItemView()
    
    # Send the embed with the buttons
    if ctx:
        await ctx.send(embed=embed, view=view)
    else:
        await message.channel.send(embed=embed, view=view)

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return  # Ignore self

    channel_id = message.channel.id
    # Initialize if not in dict
    if channel_id not in recent_messages:
        recent_messages[channel_id] = []

    # Maintain a small history of messages for context
    recent_messages[channel_id].append(message.content)
    if len(recent_messages[channel_id]) > MAX_CONTEXT:
        recent_messages[channel_id].pop(0)

    if not message.content.startswith("!find"):
        if is_potential_shopping_message(message.content):
            if await should_call_llm(channel_id):
                query = await interpret_chat(recent_messages[channel_id])
                if query.get("item"):
                    # Check if this query is different from the last one
                    if last_searched_query.get(channel_id) == query["item"]:
                        # Query is the same, so skip triggering another search.
                        print("Same query detected; skipping new search.")
                    else:
                        # New query! Update the last_searched_query and perform search.
                        last_searched_query[channel_id] = query["item"]
                        region = "us"
                        await message.channel.send("🛒 **Detected Shopping Intent**. Searching...")
                        recommendations = await prompted_response.run_prompted_response(query, region)
                        print(f"Recommendations: {recommendations}")
                        if recommendations:
                            for shopping_item in recommendations:
                                await recommended_item_embed(None, message, shopping_item.item_name, shopping_item.price, shopping_item.link)
                        else:
                            await message.channel.send("No recommendations found.")
                    
                    

    # Process commands (like !hello, !find)
    await bot.process_commands(message)

@bot.command()
async def hello(ctx: commands.Context):
    """Simple test command."""
    await ctx.send("Hello! Your bot is working!")


@bot.command()
async def find(ctx: commands.Context, *, query: str):
    """
    The !find command: passes the user’s query to our PromptedResponse class,
    processes the recommendations, and sends each result as a Discord embed.
    """
    async def do_search():
        status_message = await ctx.send("🛒 **Fetching recommendations...**")
        region = "us"
        recommendations = await prompted_response.run_prompted_response(query, region)
        print(f"Recommendations: {recommendations}")
        if recommendations:
            for shopping_item in recommendations:
                await recommended_item_embed(ctx, None, shopping_item.item_name, shopping_item.price, shopping_item.link)
    
        else:
            await ctx.send("No recommendations found.")
        await status_message.delete()  # Remove the status message once done.
    
    bot.loop.create_task(do_search())


bot.run(TOKEN)
