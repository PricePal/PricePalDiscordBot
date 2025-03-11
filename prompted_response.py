from typing import List, Union, Dict
from dotenv import load_dotenv
from services.openai_service import OpenAIService
from services.search_service import SearchService
from models.shopping_models import ShoppingItem, Recommendation
from config import OPENAI_MODEL, OPENAI_API_KEY, SERP_API_KEY

load_dotenv()

class PromptedResponse:
    def __init__(self, openai_service=None, search_service=None):
        # Dependency injection for better testability
        self.openai_service = openai_service or OpenAIService(api_key=OPENAI_API_KEY)
        self.search_service = search_service or SearchService(api_key=SERP_API_KEY)
       
    async def parse_query(self, query_str: str) -> Dict:
        """
        Uses the OpenAI API to parse a plain text query into a structured JSON object.
        """
        return await self.openai_service.parse_query(query_str)

    async def parse_multi_item_query(self, query_str: str) -> Dict:
        """
        Uses the OpenAI API to parse a plain text query into a structured JSON object.
        """
        return await self.openai_service.parse_multi_item_query(query_str)
    
    async def generate_user_profile(self, user_history: List[Dict]) -> Dict:
        """
        Uses the OpenAI API to generate a user profile based on their shopping history.
        """
        return await self.openai_service.generate_user_profile(user_history)
    
    async def generate_surprise_recommendation(self, message_context: List[str]) -> str:
        """
        Analyzes chat context and suggests a surprising but relevant item.
        """
        return await self.openai_service.generate_surprise_recommendation(message_context)

    async def get_recommendations(self, query: Dict) -> List[ShoppingItem]:
        """
        Uses the OpenAI API to generate a specified number of item recommendations.
        """
        return await self.openai_service.get_recommendations(query)

    async def process_web_results(self, items: List[ShoppingItem], purchase_options: Dict) -> List[Recommendation]:
        """
        Processes purchase options for each item and returns best recommendations.
        """
        return await self.openai_service.process_web_results(items, purchase_options)

    async def run_prompted_response(self, query: Union[str, Dict], region: str) -> List[Recommendation]:
        """
        Main workflow method that orchestrates the entire recommendation process.
        """
        # Step 1: Parse query if it's a string
        if isinstance(query, str):
            query_dict = await self.parse_query(query)
        else:
            query_dict = query

        # Step 2: Get recommended items
        recommendations = await self.get_recommendations(query_dict)
        
        # Step 3: Search for purchase options for each recommendation
        purchase_options = {}
        for item in recommendations:
            # options = ""
            options = self.search_service.search_shopping(
                item_name=item.item_name,
                region=region,
                price_range=query_dict.get("price_range")
            )

            purchase_options[item.item_name] = options

        # Step 4: Process results to select the best options
        final_results = await self.process_web_results(recommendations, purchase_options)
        return final_results
