import os
import json
import logging
import discord
import mistralai
import asyncio
from openai import OpenAI

#from dotenv import load_dotenv

from mistralai import Mistral
from tools.web_search import web_search_tool

MISTRAL_MODEL = "codestral-latest"

search_web_prompt = (
    "You are an expert shopping assistant. Given a description of what your customer is looking for, "
    "your job is to find the names of the 3 most relevant items for them to purchase, do not look at where to buy them. Then, use your tools to find the best "
    "and cheapest place to purchase these items on the web. Return each of the 3 item suggestions with their price, "
    "purchase link, and purchase source."
)

#load_dotenv()


class ShoppingAgents:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    
        # Initialize your Mistral client
        self.client = Mistral(api_key=MISTRAL_API_KEY)
        
        # Define the tool metadata 
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search_tool",
                    "description": "Search Google Shopping for a particular item; returns pricing and purchasing options.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string"},
                            "region": {"type": "string"},
                        },
                        "required": ["item", "region"],
                    },
                },
            }
        ]
        # Map the tool name to our local function
        self.tools_to_functions = {
            "web_search_tool": web_search_tool,
        }

    async def mistral_execute_search(self, message: str, region: str) -> str:
        # Create and initialize the conversation messages list
        messages = [
            {"role": "system", "content": search_web_prompt},
            {"role": "user", "content": f"Discord message: {message}\nRegion: {region}\nOutput:"},
        ]
        
        # First, let the model generate an initial response.
        initial_response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        print(initial_response.choices[0].message)
        # (Optional) You might want to process initial_response if needed.
        
        # Now, force the model to use a tool by specifying tools and a tool_choice.
        tool_response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
            tools=self.tools,
            tool_choice="any",
        )
        
        # Append the model's tool call message to the conversation.
        messages.append(tool_response.choices[0].message)
        
        # Extract the tool call details.
        tool_call = tool_response.choices[0].message.tool_calls[0]
        function_name = tool_call.function.name
        function_params = json.loads(tool_call.function.arguments)
        
        # Call the local tool function.
        function_result = self.tools_to_functions[function_name](**function_params)
        
        # Append the tool's result to the conversation.
        messages.append(
            {
                "role": "tool",
                "name": function_name,
                "content": function_result,
                "tool_call_id": tool_call.id,
            }
        )
        
        # Run the model again with the updated conversation (including the tool result).
        final_response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        
        # Return the final answer from the assistant.
        return final_response.choices[0].message.content




# Test message
message_test = "I am looking to get a new gaming mouse"
region = "United States"

async def main():
    # Create an instance of ShoppingAgents
    agent = ShoppingAgents()
    # Call the async method and await its result
    result = await agent.mistral_execute_search(message_test,region)
    print(result)

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
