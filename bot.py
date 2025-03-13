import tracemalloc
import discord
from discord.ext import commands

# Import modular components
from modules.cooldown_manager import CooldownManager
from modules.message_history import MessageHistory
from modules.shopping_handler import ShoppingHandler
from modules.bot_commands import register_commands
from config import DISCORD_TOKEN
from db.database import get_db_session

# Start memory tracking
tracemalloc.start()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize components
cooldown_manager = CooldownManager(cooldown_seconds=30)
message_history = MessageHistory(max_context=5)
shopping_handler = ShoppingHandler(get_db_session)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return 

    channel_id = message.channel.id
    
    # Track message history
    message_history.add_message(channel_id, message.content)
    
    # Process shopping intents
    await shopping_handler.process_message(
        message, 
        message_history.get_context(channel_id),
        cooldown_manager
    )
    
    # Process commands
    await bot.process_commands(message)

# Register all bot commands
register_commands(bot, get_db_session)

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
