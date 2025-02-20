# bot.py
import os
import discord
from collections import defaultdict
from discord.ext import commands
from discord.ext import commands
from dotenv import load_dotenv
from prompted_response import PromptedResponse

# Load environment variables and get the Discord token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
from collections import deque
import time


# Set up bot intents and create the bot instance
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)


# Configure message history and cooldowns
MESSAGE_HISTORY = defaultdict(lambda: deque(maxlen=20))  # Per-channel context
COOLDOWNS = defaultdict(float)  # Channel-based cooldowns
RESPONSE_COOLDOWN = 300  # 5 minutes between auto-responses per channel

class ShoppingBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompted_response = PromptedResponse()

    async def process_chat_context(self, message):
        """Main processing pipeline for chat messages"""
        if message.author == self.user:
            return

        # Update message history
        channel = message.channel
        MESSAGE_HISTORY[channel.id].append(message.content)
        
        # Check cooldown
        if time.time() - COOLDOWNS[channel.id] < RESPONSE_COOLDOWN:
            return

        # Parse conversation context
        context = list(MESSAGE_HISTORY[channel.id])[-5:]  # Last 5 messages
        parsed = interpret_chat(context)
        
        if parsed.get('item'):
            await self.generate_auto_response(message, parsed)

    async def generate_auto_response(self, message, query):
        """Handle recommendation generation and delivery"""
        try:
            results = await self.prompted_response.run_prompted_response(
                query['item'], 
                region="us",
                price_range=query.get('price_range'),
                max_results=query.get('number_of_results', 3)
            )
            
            response = f"{message.author.mention} I found these options:\n{results}"
            await message.channel.send(response)
            COOLDOWNS[message.channel.id] = time.time()
            
        except Exception as e:
            print(f"Error generating response: {e}")

# Modified message handler with command passthrough
@bot.event
async def on_message(message):
    await bot.process_commands(message)  # Maintain existing command functionality
    await bot.process_chat_context(message)

bot.run(TOKEN)

