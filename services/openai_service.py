import json
from typing import List, Dict, Any
from openai import AsyncOpenAI
from models.shopping_models import ShoppingItem, Recommendation, StructuredResponse
from config import OPENAI_MODEL

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = OPENAI_MODEL

    async def parse_query(self, query_str: str) -> Dict:
        """
        Parses a natural language query into structured format.
        """
        prompt = (
            "You are a text parser. Convert the following query into a JSON object with the following structure:\n"
            "{\n"
            '  "item_name": "<product name>",\n'
            '  "type": "<category or None>",\n'
            '  "price_range": "<price range or None>",\n'
            '  "number_of_results": <number>\n'
            "}\n\n"
            # ... [rest of your existing prompt]
            f"Now parse the following query and return only the JSON:\n{query_str}"
        )

        try: 
            response = await self.client.chat.completions.create(
                model=self.model,  
                messages=[
                    {"role": "system", "content": "You are a helpful text parser."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            # Set defaults for missing fields
            if "item_name" not in parsed or not parsed["item_name"]:
                parsed["item_name"] = query_str.strip()
            if "type" not in parsed:
                parsed["type"] = None
            if "price_range" not in parsed:
                parsed["price_range"] = None
            if "number_of_results" not in parsed:
                parsed["number_of_results"] = 3
                
            return parsed
        
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON from OpenAI response.")
            return {}
        except Exception as e:
            print(f"Parse Query Error: {e}")
            return {}

    async def get_recommendations(self, query: Dict) -> List[ShoppingItem]:
        """
        Generates shopping item recommendations based on the query.
        """
        """
            Uses the OpenAI API to generate a specified number of item recommendations in a JSON array.
            The 'query' dict should contain:
                "item_name": <product name>,
                "type": <category or None>,
                "price_range": <price range or None>,
                "number_of_results": <number of results to return>
            
            """
        number_of_results = query.get("number_of_results", 3)
        customer_request = (
            f"Item_Name: {query.get('item_name')}, "
            f"Type: {query.get('type', 'None')}, "
            f"Price Range: {query.get('price_range', 'None')}, "
            f"Number of Results: {number_of_results}"
        )

        prompt = (
            "You are an expert shopping assistant. Given the following customer request, "
            f"provide exactly {number_of_results} item recommendations as a JSON array. "
            "Each recommendation should be a JSON object with a single field 'item_name' representing the item name. "
            "Return only the JSON without any additional commentary.\n\n"
            f"Customer request: {customer_request}"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,  
                messages=[
                    {"role": "system", "content": "You are an expert shopping assistant that returns valid json."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.3
            )

            # print(f"API Response: {response}")

            # Extract the message content from the API response.
            # Use dictionary indexing assuming the response is a dict.
            content = response.choices[0].message.content.strip()

            # Remove markdown code fences if present.
            if content.startswith("```"):
                content = content.strip("```").strip()
                # If the language tag is included (e.g., "json"), remove it.
                if content.lower().startswith("json"):
                    content = content[4:].strip()

            # Parse the JSON into your StructuredResponse model.
            parsed = json.loads(content)

            if isinstance(parsed, list):
                parsed = {"recommendations": parsed}
            print(f"Parsed: {parsed}")

            structured_response = StructuredResponse.model_validate(parsed)
            return structured_response.recommendations

        except json.JSONDecodeError:
            print("Error: Failed to parse JSON from OpenAI response.")
            return []
        except Exception as e:
            print(f"Get Recommendations Error: {e}")
            return []
        

    async def process_web_results(self, items: List[ShoppingItem], purchase_options: Dict) -> List[Recommendation]:
        """
        Processes web search results to find the best options.
        """
        """
        Uses the OpenAI API to process purchase options for each item.
        Instruct the model to return a JSON array where each element is an object with the following keys:
        'item', 'price', 'link', and 'source'.
        """
        prompt = (
            "You are an expert shopping assistant. For each of the following items, "
            "select the best purchase option from the provided options based solely on the given data. "
            "The key for this array is 'results', very important that this is always the case"
            "Return a JSON array where each element is a JSON object with the keys: "
            "'item_name', 'price', 'link', and 'source'. "
            "If there are no options, still return each item as an element in the array, just have the item_name be the item name, and the price, link, and source be None."
            "Return only the JSON array without any additional commentary.\n\n"
        )
        for item in items:
            item_name = item.item_name
            print(f"purchase_options: {purchase_options}")
            options = purchase_options.get(item_name, "No options found.")
            print(f"Options: {options}")
            prompt += f"Item: {item_name}\nPurchase Options:\n{options}\n\n"

        try:
            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert shopping assistant that returns valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=400,
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()
            print(f"Content: {content}")
            if content.startswith("```"):
                content = content.strip("```").strip()
                if content.lower().startswith("json"):
                    content = content[4:].strip()

            recommendations = json.loads(content)
            print(f"Final Recommendations: {recommendations}")
            # print(recommendations)
            # Handle both a raw JSON array and a JSON object with key "results"
            if isinstance(recommendations, dict):
                if "results" in recommendations and isinstance(recommendations["results"], list):
                    recommendations = recommendations["results"]
                else:
                    raise ValueError("Expected a JSON array or an object with a 'results' key")
            if not isinstance(recommendations, list):
                raise ValueError("Expected a JSON array")
            
            # Convert each recommendation into a Recommendation model
            final_recommendations = []
            for rec in recommendations:
                try:
                    final_recommendations.append(Recommendation(**rec))
                except Exception as e:
                    print(f"Error validating recommendation: {e}")
            return final_recommendations

        except Exception as e:
            print(f"Process Web Results Error: {e}")
            return []