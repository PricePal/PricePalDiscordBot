import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")    
OPENAI_MODEL = "gpt-4o-mini"
REASONING_MODEL = "o1-mini"







