import os
import json
import logging
import discord
import mistralai
import asyncio

from mistralai import Mistral

MISTRAL_MODEL = "codestral-latest"

search_web_prompt = (
    "you are an expert shopper assistant. You will be given a need of your customer "
    "and your job is to find 3 most relevant items for them to purchase. For each item "
    "also compare different places to purchase the item on the web and give a link to the "
    "cheapest option for each of the items."
)

class ShoppingAgents:
    def __init__(self):
        #MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        MISTRAL_API_KEY = 'E8cKlc8LFLvepl1h5mSsuY2jxvLpUrjb'
        self.client = Mistral(api_key=MISTRAL_API_KEY)

    async def execute_search(self, message: str) -> dict:
        # Search Web for item and find best purchasing link
        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": search_web_prompt},
                {"role": "user", "content": f"Discord message: {message}\nOutput:"},
            ],
            #response_format={"type": "json_object"},
        )

        result_message = response.choices[0].message.content
        return result_message

# Test message
message_test = "I am looking to get a new gaming mouse"

async def main():
    # Create an instance of ShoppingAgents
    agent = ShoppingAgents()
    # Call the async method and await its result
    result = await agent.execute_search(message_test)
    print(result)

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
