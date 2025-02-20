import os
import json
import logging
import discord
import asyncio
import aiohttp

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

search_web_prompt = (
    "You are an expert shopper assistant. You will be given a need of your customer "
    "and your job is to find 3 most relevant items for them to purchase. For each item "
    "also compare different places to purchase the item on the web and give a link to the "
    "cheapest option for each of the items. Make sure the links you provide are correct and go to real website with the correct item"
)

class ShoppingAgents:
    def __init__(self):
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }

    async def perplexity_execute_search(self, message: str) -> str:
        payload = {
            "model": "sonar-reasoning-pro",
            "messages": [
                {"role": "system", "content": search_web_prompt},
                {"role": "user", "content": f"Discord message: {message}\nOutput:"}
            ],
            "max_tokens": 1024,
            "temperature": 0.7
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    return f"Error: {response.status} - {await response.text()}"

# Test message
message_test = "I am looking to get a new gaming mouse"

async def main():
    agent = ShoppingAgents()
    result = await agent.perplexity_execute_search(message_test)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
