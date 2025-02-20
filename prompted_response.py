import os
import json
import openai
from typing import List
from pydantic import BaseModel
from openai import OpenAI
from serpapi.google_search import GoogleSearch
from dotenv import load_dotenv

load_dotenv()
from openai import AsyncOpenAI

#openai_model_choice = "gpt-4o"
openai_model_choice = "gpt-4o-mini"

# Pydantic models for structured responses
class Item(BaseModel):
    name: str

class StructuredResponse(BaseModel):
    recommendations: List[Item]


class PromptedResponse:
    def __init__(self):
        self.SERP_API_KEY = os.getenv("SERP_API_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        # Store the client as an instance attribute
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
    async def get_recommendations(self, user_query: str) -> List[Item]:
        """
        Uses the OpenAI API to generate 3 item recommendations in a structured JSON format.
        Expected output: List of Item objects, e.g.,
        [
            {"name": "Logitech G502 HERO"},
            {"name": "Razer DeathAdder V2"},
            {"name": "Corsair Harpoon RGB Pro"}
        ]
        """
        prompt = (
            "You are an expert shopping assistant. Given the following customer request, "
            "provide exactly 3 item recommendations as a JSON array. Each recommendation should be "
            "a JSON object with a single field 'name' representing the item name. "
            "Return only the JSON without any additional commentary.\n\n"
            f"Customer request: {user_query}"
        )
        # Use the asynchronous method
        response = await self.client.chat.completions.create(
            model=openai_model_choice,  
            messages=[
                {"role": "system", "content": "You are an expert shopping assistant."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            # max_tokens=200,
        )
        content = response.choices[0].message.content
        structured_response = StructuredResponse.parse_raw(content)
        return structured_response.recommendations

    #make async to improve peformance
    def web_search_tool(self, item: str, region: str) -> str:
        """
        Searches Google Shopping for the given item and returns a formatted string with purchase options.
        """
        params = {
            "engine": "google_shopping",
            "q": item,
            "gl": region,
            "api_key": self.SERP_API_KEY
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        shopping_results = results.get("shopping_results", [])
        if not shopping_results:
            return "No shopping results found."
        
        output = []
        for result in shopping_results:
            title = result.get("title", "N/A")
            link = result.get("link") or result.get("product_link", "N/A")
            price = result.get("price", "N/A")
            source = result.get("source", "N/A")
            output.append(
                f"Title: {title}\nLink: {link}\nPrice: {price}\nSource: {source}\n{'-' * 40}"
            )
        result_str = "\n".join(output)
        return result_str

    async def process_web_results(self, items: List[Item], purchase_options: dict) -> str:
        """
        Uses the OpenAI API to process purchase options for each item.
        The prompt instructs the model to select the best purchase option for each item 
        based solely on the provided information, returning a succinct recommendation.
        """
        prompt = (
            "You are an expert shopping assistant. For each of the following items, select the best "
            "purchase option from the provided options based solely on the information given. "
            "Return a succinct purchase recommendation for each item including only the item name, price, link, and source:\n\n"
        )
        for item in items:
            item_name = item.name
            options = purchase_options.get(item_name, "No options found.")
            prompt += f"Item: {item_name}\nPurchase Options:\n{options}\n\n"

        response = await self.client.chat.completions.create(
            model=openai_model_choice,
            messages=[
                {"role": "system", "content": "You are an expert shopping assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
        )
        content = response.choices[0].message.content
        return content

    async def run_prompted_response(self, user_query: str, region: str) -> str:
        """
        Given a customer query and region, this function:
        1. Retrieves 3 item recommendations.
        2. For each item, searches for purchase options.
        3. Processes the web search results to select the best purchase option for each item.
        
        Returns:
            The final purchase recommendations as a string.
        """
    
        # Step 1: Get item recommendations
        recommendations = await self.get_recommendations(user_query)

        # Step 2: For each recommended item, get purchase options using the web_search_tool.
        purchase_options = {}
        for item in recommendations:
            item_name = item.name
            options = self.web_search_tool(item_name, region)
            purchase_options[item_name] = options

        # Step 3: Process the web search results to select the best purchase option for each item.
        final_results = await self.process_web_results(recommendations, purchase_options)
        
        return final_results
