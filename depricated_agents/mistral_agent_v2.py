import os
import json
import asyncio
from mistralai import Mistral
from tools.web_search import web_search_tool

MISTRAL_MODEL = "codestral-latest"

# Prompt to only get the item recommendations
recommendation_prompt = (
    "You are an expert shopping assistant. Given a description of what your customer is looking for, "
    "your job is to identify the names of the 3 most relevant items for them to purchase. "
    "Do NOT provide any pricing, purchase links, or source details at this stage; only list the item names."
)

class ShoppingAgents:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
       
        self.client = Mistral(api_key=MISTRAL_API_KEY)

    async def get_item_recommendations(self, user_message: str) -> list:
        messages = [
            {"role": "system", "content": recommendation_prompt},
            {"role": "user", "content": f"Customer request: {user_message}"}
        ]
        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        # Here, we assume the response is something like:
        # "1. Logitech G502 HERO\n2. Razer DeathAdder V2\n3. Corsair Harpoon RGB Pro"
        items_str = response.choices[0].message.content
        # Parse the response into a list. (You may need to adjust parsing based on the exact format.)
        items = [line.strip().split(". ", 1)[-1] for line in items_str.strip().split("\n") if line.strip()]
        return items

    async def get_best_purchase_option(self, item: str, region: str) -> str:
        # Get purchase options from your tool
        tool_result = web_search_tool(item=item, region=region)
        
        # Update the prompt to be explicit
        selection_prompt = (
            "You are an expert shopping assistant. Using only the following provided purchase options, "
            "select the option with the lowest price and highest reliability. Return only the purchase URL "
            "(and nothing else) associated with that option. Do not mention any limitations about browsing the internet.\n\n"
            "Purchase options:\n" + tool_result
        )
        
        messages = [
            {"role": "system", "content": selection_prompt},
            {"role": "user", "content": f"Item: {item}"}
        ]
        
        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        best_option = response.choices[0].message.content.strip()
        return best_option

    async def execute_full_search(self, user_message: str, region: str) -> dict:
        # Stage 1: Get recommended items
        items = await self.get_item_recommendations(user_message)
        results = {}
        # Stage 2 & 3: For each item, get the best purchase option.
        for item in items:
            best_option = await self.get_best_purchase_option(item, region)
            results[item] = best_option
        return results

# Test message
message_test = "I am looking to get a new gaming mouse"
region = "United States"

async def main():
    agent = ShoppingAgents()
    results = await agent.execute_full_search(message_test, region)
    for item, option in results.items():
        print(f"Item: {item}\nBest Purchase Option: {option}\n{'-' * 40}")

if __name__ == "__main__":
    asyncio.run(main())
