import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from prompted_response import PromptedResponse

# Load environment variables and get the Discord token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set up bot intents and create the bot instance
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Create an instance of our PromptedResponse class
prompted_response = PromptedResponse()

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! Your bot is working!")

@bot.command()
async def find(ctx, *, query: str):
    """
    The !find command: passes the user’s query to our PromptedResponse class,
    processes the recommendations, and sends the result back to the channel.
    """
    # Inform the user that recommendations are being fetched
    status_message = await ctx.send("Fetching recommendations...")
    
    region = "us"  # Adjust the region as needed.
    results = await prompted_response.run_prompted_response(query, region)
    
    # Update the original message with the final results.
    await status_message.edit(content=results)

bot.run(TOKEN)
