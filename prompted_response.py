import os
import json
from openai import AsyncOpenAI
from typing import List, Union
from pydantic import BaseModel
from serpapi import GoogleSearch 
from dotenv import load_dotenv

load_dotenv()

openai_model_choice = "gpt-4o-mini"

# Pydantic models for structured responses
class Item(BaseModel):
    name: str

class Recommendation(BaseModel):
    item: str
    price: str | None
    link: str | None
    source: str | None

class StructuredResponse(BaseModel):
    recommendations: List[Item]

class PromptedResponse:
    def __init__(self):

        self.SERP_API_KEY = os.getenv("SERP_API_KEY")
        if not self.SERP_API_KEY:
            raise ValueError("SERP_API_KEY not set in environment.")
        
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment.")
        
        self.client = AsyncOpenAI(api_key=self.OPENAI_API_KEY)
       

    async def parse_query(self, query_str: str) -> dict:
        """
        Uses the OpenAI API to parse a plain text query into a structured JSON object with the format:
        {
        "item": "<product name>",
        "type": "<category or None>",
        "price_range": "<price range or None>",
        "number_of_results": <number>
        }
        This method handles edge cases where the query might be very simple (e.g., "ski mask")
        by filling in default values.
        """
        prompt = (
        "You are a text parser. Convert the following query into a JSON object with the following structure:\n"
        "{\n"
        '  "item": "<product name>",\n'
        '  "type": "<category or None>",\n'
        '  "price_range": "<price range or None>",\n'
        '  "number_of_results": <number>\n'
        "}\n\n"
        "Feel free to add adjectives to the item name to make it more specific. For instance:\n"
        "- If the query is \"I want a pair of shoes that I can run in\", output \"running shoes\".\n"
        "- If the query is \"I want a pair of shoes that are comfortable\", output \"comfortable shoes\".\n"
        "- If the query is \"black ski mask that's scary\", output \"scary black ski mask\".\n\n"
        "For example, if the query is \"find a ski mask that is within 30 to 50 dollars, return 10 examples\", "
        "the output might be:\n"
        "{\n"
        '  "item": "ski mask",\n'
        '  "type": null,\n'
        '  "price_range": "30-50",\n'
        '  "number_of_results": 10\n'
        "}\n\n"
        "If the query is simple (like \"ski mask\"), return a JSON object with 'item' set to the query, "
        "'type' and 'price_range' as null, and 'number_of_results' as 3.\n\n"
        f"Now parse the following query and return only the JSON:\n{query_str}"
        )

        

        try: 
            response = await self.client.chat.completions.create(
            model=openai_model_choice,  
            messages=[
                {"role": "system", "content": "You are a helpful text parser."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            # max_tokens=200,
            )
            content = response.choices[0].message.content
            # print(f"API Response: {content}")
            parsed = json.loads(content)
            if "item" not in parsed or not parsed["item"]:
                parsed["item"] = query_str.strip()
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



    async def get_recommendations(self, query: dict) -> List[Item]:
            """
            Uses the OpenAI API to generate a specified number of item recommendations in a JSON array.
            The 'query' dict should contain:
                "item": <product name>,
                "type": <category or None>,
                "price_range": <price range or None>,
                "number_of_results": <number of results to return>
            """
            number_of_results = query.get("number_of_results", 3)
            customer_request = (
                f"Item: {query.get('item')}, "
                f"Type: {query.get('type', 'None')}, "
                f"Price Range: {query.get('price_range', 'None')}, "
                f"Number of Results: {number_of_results}"
            )

            prompt = (
                "You are an expert shopping assistant. Given the following customer request, "
                f"provide exactly {number_of_results} item recommendations as a JSON array. "
                "Each recommendation should be a JSON object with a single field 'name' representing the item name. "
                "Return only the JSON without any additional commentary.\n\n"
                f"Customer request: {customer_request}"
            )

            try:
                # IMPORTANT: Remove the trailing comma so that the response is not a tuple.
                response = await self.client.chat.completions.create(
                    model=openai_model_choice,  
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

                structured_response = StructuredResponse.model_validate(parsed)
                return structured_response.recommendations

            except json.JSONDecodeError:
                print("Error: Failed to parse JSON from OpenAI response.")
                return []
            except Exception as e:
                print(f"Get Recommendations Error: {e}")
                return []

    def web_search_tool(self, item: str, region: str, price_range: str = None) -> str:
        """
        Searches Google Shopping for the given item and returns a formatted string with purchase options.
        If a price_range is provided (e.g., "30-50"), it modifies the search query accordingly.
        """
        q = item
        if price_range and price_range.lower() != "none":
            parts = price_range.split('-')
            if len(parts) == 2:
                q += f" between {parts[0].strip()} and {parts[1].strip()} dollars"
            else:
                q += f" {price_range}"

        params = {
            "engine": "google_shopping",
            "q": q,
            "gl": region,
            "api_key": self.SERP_API_KEY
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        # print(f"Results: {results}")
        shopping_results = results.get("shopping_results", [])
        if not shopping_results or len(shopping_results) == 0:
            print(f"No shopping results found for {item} in {region} with price range {price_range}")
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
        return "\n".join(output)

    async def process_web_results(self, items: List[Item], purchase_options: dict) -> List[dict]:
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
            "'item' (the item name), 'price', 'link', and 'source'. "
            "Return only the JSON array without any additional commentary.\n\n"
        )
        for item in items:
            item_name = item.name
            options = purchase_options.get(item_name, "No options found.")
            prompt += f"Item: {item_name}\nPurchase Options:\n{options}\n\n"

        try:
            response = await self.client.chat.completions.create(
                model=openai_model_choice,
                messages=[
                    {"role": "system", "content": "You are an expert shopping assistant that returns valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=400,
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.strip("```").strip()
                if content.lower().startswith("json"):
                    content = content[4:].strip()

            recommendations = json.loads(content)
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


    async def run_prompted_response(self, query: Union[str, dict], region: str) -> str:
        """
        Given a customer query (either a plain string or a structured dictionary) and a region, this function:
        1. Uses NLP to parse a plain text query into a structured format if needed.
        2. Retrieves item recommendations.
        3. For each item, searches for purchase options (using the price range if provided).
        4. Processes the web search results to select the best purchase option for each item.
        5. Returns the final purchase recommendations as a string.
        """
        if isinstance(query, str):
            # Use NLP to parse the plain text query into our desired JSON structure
            query_dict = await self.parse_query(query)
        else:
            query_dict = query

        # Step 1: Get item recommendations using the structured query
        recommendations = await self.get_recommendations(query_dict)

        # Step 2: For each recommended item, get purchase options using the price range.
        purchase_options = {}
        for item in recommendations:
            options = self.web_search_tool(item.name, region, query_dict.get("price_range"))
            purchase_options[item.name] = options

        # Step 3: Process the web search results to select the best purchase option for each item.
        final_results = await self.process_web_results(recommendations, purchase_options)
        return final_results
