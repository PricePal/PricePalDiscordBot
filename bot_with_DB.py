# bot.py
import os
import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
from time import time

# Import local modules for processing queries and recommendations.
from interpret_chat import interpret_chat
from prompted_response import PromptedResponse

# Import database modules.
from DB_management.database import SessionLocal, engine
from DB_management.repositories import (
    create_or_get_user, create_query, create_recommended_item, create_reaction
)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Create an instance of our PromptedResponse class.
prompted_response = PromptedResponse()

# ------------------------
# Global Variables for Cooldowns and Context
# ------------------------
channel_last_called = {}
COOLDOWN_SECONDS = 30
recent_messages = {}  # Maintain recent messages per channel for context
MAX_CONTEXT = 5

def get_current_time():
    from time import time
    return time()

async def should_call_llm(channel_id: int) -> bool:
    now = get_current_time()
    if channel_id in channel_last_called:
        if now - channel_last_called[channel_id] < COOLDOWN_SECONDS:
            return False
    channel_last_called[channel_id] = now
    return True

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ------------------------
# Recommended Item Embed with Reaction Buttons
# ------------------------
async def recommended_item_embed(ctx: commands.Context | None, message: discord.Message | None,
                                 item_name: str, price: str, link: str,
                                 query_id: str, rec_item_id: str):
    embed = discord.Embed(title=item_name, color=discord.Color.blue())
    embed.add_field(name="Price", value=price, inline=True)
    embed.add_field(name="Link", value=link, inline=False)

    class ShoppingItemView(View):
        def __init__(self, query_id: str, rec_item_id: str):
            super().__init__()
            self.query_id = query_id
            self.rec_item_id = rec_item_id

        @discord.ui.button(label="Add to Wishlist", style=discord.ButtonStyle.success, emoji="❤️")
        async def on_wishlist_click(self, interaction: discord.Interaction, button: discord.ui.Button):
            db = SessionLocal()
            try:
                create_reaction(db, query_id=self.query_id, recommended_item_id=self.rec_item_id, reaction_type="wishlist")
                await interaction.response.send_message("Added to your wishlist!", ephemeral=True)
            finally:
                db.close()

        @discord.ui.button(label="Dislike", style=discord.ButtonStyle.danger, emoji="👎")
        async def on_dislike_click(self, interaction: discord.Interaction, button: discord.ui.Button):
            db = SessionLocal()
            try:
                create_reaction(db, query_id=self.query_id, recommended_item_id=self.rec_item_id, reaction_type="dislike")
                await interaction.response.send_message("You disliked this item.", ephemeral=True)
            finally:
                db.close()

    view = ShoppingItemView(query_id, rec_item_id)
    if ctx:
        await ctx.send(embed=embed, view=view)
    else:
        await message.channel.send(embed=embed, view=view)

# ------------------------
# PROMPTED QUERY HANDLER (e.g., !find command)
# ------------------------
@bot.command()
async def find(ctx: commands.Context, *, query: str):
    async def do_search():
        db = SessionLocal()
        try:
            # Log or retrieve the user.
            user = create_or_get_user(db, discord_id=str(ctx.author.id), username=ctx.author.name)
            # Use the parse_query method to interpret the raw query.
            interpreted = await prompted_response.parse_query(query)
            # Log the prompted query with raw text and interpreted output.
            new_query = create_query(
                db,
                user_id=user.id,
                query_type="prompted",
                raw_query=query,
                interpreted_query=interpreted
            )
            status_message = await ctx.send("🛒 **Fetching recommendations...**")
            # Get recommendations from your PromptedResponse module.
            recommendations = await prompted_response.run_prompted_response(query, region="us")
            for rec in recommendations:
                # Ensure that link is not None (default to an empty string if necessary)
                rec_link = rec.link if rec.link is not None else ""
                rec_price = float(rec.price) if rec.price is not None else 0.0
                rec_item = create_recommended_item(
                    db,
                    query_id=new_query.id,
                    item_name=rec.item_name,
                    vendor="VendorX",  # Replace with actual vendor if available.
                    link=rec_link,
                    price=rec_price,
                    metadata=rec.dict()  # Log additional metadata.
                )
                await recommended_item_embed(ctx, None, rec.item_name, rec.price, rec_link,
                                             query_id=new_query.id, rec_item_id=rec_item.id)
            await status_message.delete()
        finally:
            db.close()
    bot.loop.create_task(do_search())

# ------------------------
# UNPROMPTED QUERY HANDLER (via on_message)
# ------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    channel_id = message.channel.id
    if channel_id not in recent_messages:
        recent_messages[channel_id] = []
    recent_messages[channel_id].append(message.content)
    if len(recent_messages[channel_id]) > MAX_CONTEXT:
        recent_messages[channel_id].pop(0)

    # If the message is not a command, check for unprompted shopping intent.
    if not message.content.startswith("!"):
        if await should_call_llm(channel_id):
            query_dict = await interpret_chat(recent_messages[channel_id])
            if query_dict.get("item"):
                db = SessionLocal()
                try:
                    user = create_or_get_user(db, discord_id=str(message.author.id), username=message.author.name)
                    # Use parse_query to get structured data from the raw message.
                    interpreted = await prompted_response.parse_query(message.content)
                    unprompted_query = create_query(
                        db,
                        user_id=user.id,
                        query_type="unprompted",
                        raw_query=message.content,
                        interpreted_query=interpreted
                    )
                    recommendations = await prompted_response.run_prompted_response(query_dict, region="us")
                    for rec in recommendations:
                        rec_link = rec.link if rec.link is not None else ""
                        rec_price = float(rec.price) if rec.price is not None else 0.0
                        rec_item = create_recommended_item(
                            db,
                            query_id=unprompted_query.id,
                            item_name=rec.item_name,
                            vendor="VendorX",
                            link=rec_link,
                            price=rec_price,
                            metadata=rec.dict()
                        )
                        await recommended_item_embed(None, message, rec.item_name, rec.price, rec_link,
                                                     query_id=unprompted_query.id, rec_item_id=rec_item.id)
                finally:
                    db.close()
    await bot.process_commands(message)

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send("Hello! Your bot is working!")

bot.run(TOKEN)
