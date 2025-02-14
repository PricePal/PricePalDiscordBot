import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load the token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set up bot with a command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.command()
async def hello(ctx):
    await ctx.send("Hello! Your bot is working!")


bot.run(TOKEN)
