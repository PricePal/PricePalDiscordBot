import json
from typing import List, Dict, Any
from openai import AsyncOpenAI
from models.shopping_models import ShoppingItem, Recommendation, StructuredResponse
from config import OPENAI_MODEL, REASONING_MODEL
from db.models import Query, RecommendedItem, Reaction

def strip_markdown(content: str) -> str:
    """Removes markdown code block delimiters from the response."""
    if content.startswith("```"):
        lines = content.splitlines()
        # Remove the first line if it starts with ```
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Remove the last line if it starts with ```
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    return content

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = OPENAI_MODEL
        self.reasoning_model = REASONING_MODEL

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
            "For the JSON structure:\n"
            "- 'item_name' should be the main product the user is looking for\n"
            "- 'type' should be the category, subcategory, or specific type of the item (or null if not specified)\n"
            "- 'price_range' should capture any budget constraints or price expectations (or null if not specified)\n"
            "- 'number_of_results' should be the number of recommendations requested (default to 3 if not specified)\n\n"
            "Examples:\n"
            "Query: 'Find me a good gaming laptop under $1000'\n"
            "{\n"
            '  "item_name": "gaming laptop",\n'
            '  "type": "electronics",\n'
            '  "price_range": "under $1000",\n'
            '  "number_of_results": 3\n'
            "}\n\n"
            "Query: 'Show me 5 wireless headphones'\n"
            "{\n"
            '  "item_name": "wireless headphones",\n'
            '  "type": "audio equipment",\n'
            '  "price_range": null,\n'
            '  "number_of_results": 5\n'
            "}\n\n"
            "Always extract as much detail as possible from the query. If the number of results isn't specified, use 3 as the default value."
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
    
    # Add this method to the PromptedResponse class

    async def parse_multi_item_query(self, query_str: str) -> Dict:
        """
        Parses a query for a set of items (like "ski equipment") into up to 4 complementary items.
        """
        prompt = (
            "You are a product expert who helps find complementary items in a set. "
            "For the following query, identify up to 4 specific complementary items that would form a complete set. "
            "For example, if the query is 'ski equipment', you might suggest 'ski helmet', 'ski boots', 'ski jacket', and 'ski goggles'. "
            "Return a JSON object with the following structure:\n"
            "{\n"
            '  "category": "<main category>",\n'
            '  "items": ["<specific item 1>", "<specific item 2>", "<specific item 3>", "<specific item 4>"]\n'
            "}\n\n"
            f"Query: {query_str}\n\n"
            "Important:\n"
            "1. Return exactly 4 items if possible, or fewer if the set naturally has fewer items\n"
            "2. Be specific with item names (include type, purpose, etc.)\n"
            "3. Ensure items are complementary and make sense as a set\n"
            "4. Return only the JSON object"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful product set expert."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content

            parsed = json.loads(content)
            
            if "category" not in parsed:
                parsed["category"] = query_str
            if "items" not in parsed or not isinstance(parsed["items"], list):
                parsed["items"] = [query_str]
                
            parsed["items"] = parsed["items"][:4]
                    
            return parsed
        
        except Exception as e:
            print(f"Parse Multi-Item Query Error: {e}")
            return {"category": query_str, "items": [query_str]}

    async def get_recommendations(self, query: Dict) -> List[ShoppingItem]:
        """
        Generates shopping item recommendations based on the query.
        
        Uses the OpenAI API to generate a specified number of item recommendations in a JSON array.
        The 'query' dict should contain:
            "item_name": <product name>,
            "type": <category or None>,
            "price_range": <price range or None>,
            "number_of_results": <number of results to return>
        
        Returns:
            List[ShoppingItem]: A list of recommended shopping items
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
            f"provide exactly {number_of_results} specific item recommendations. "
            "The response MUST be a valid JSON object with the following structure:\n"
            "{\n"
            '  "recommendations": [\n'
            '    {"item_name": "specific product name"},\n'
            '    {"item_name": "specific product name"},\n'
            '    {"item_name": "specific product name"}\n'
            '  ]\n'
            "}\n\n"
            "Examples:\n"
            "For 1 result:\n"
            "{\n"
            '  "recommendations": [\n'
            '    {"item_name": "Sony WH-1000XM4 Wireless Noise-Canceling Headphones"}\n'
            '  ]\n'
            "}\n\n"
            "For 3 results:\n"
            "{\n"
            '  "recommendations": [\n'
            '    {"item_name": "Logitech G Pro X Wireless Gaming Headset"},\n'
            '    {"item_name": "SteelSeries Arctis 7P+ Wireless Gaming Headset"},\n'
            '    {"item_name": "Razer BlackShark V2 Pro Wireless Gaming Headset"}\n'
            '  ]\n'
            "}\n\n"
            "Important rules:\n"
            f"1. Return EXACTLY {number_of_results} recommendations, no more, no less\n"
            "2. Each recommendation must have ONLY the 'item_name' field\n"
            "3. Be specific with product names, including brand and model when appropriate\n"
            "4. Return ONLY the JSON object with the 'recommendations' key containing the array\n\n"
            f"Customer request: {customer_request}"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,  
                messages=[
                    {"role": "user", "content": prompt},
                ],
                # max_completion_tokens=300,
                temperature=0.3 
            )

            # Extract the message content from the API response.
            print(f"Response: {response}")

            content = response.choices[0].message.content.strip()
            print(f"Raw Content: {content}")

            content = strip_markdown(content)
            print(f"Cleaned Content: {content}")

            # Parse the JSON
            parsed = json.loads(content)

            # Ensure we always have a list of recommendations
            if isinstance(parsed, dict) and "recommendations" in parsed:
                recommendations = parsed["recommendations"]
            elif isinstance(parsed, list):
                recommendations = parsed
            else:
                # If we get an unexpected format, convert it to a list
                recommendations = [parsed] if isinstance(parsed, dict) else []
                
            # Ensure we have exactly the requested number of recommendations
            while len(recommendations) < number_of_results:
                recommendations.append({"item_name": f"Alternative {len(recommendations) + 1} for {query.get('item_name')}"})
            
            if len(recommendations) > number_of_results:
                recommendations = recommendations[:number_of_results]

            # Convert to ShoppingItem objects
            return [ShoppingItem(item_name=item.get("item_name", "")) for item in recommendations]

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
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert shopping assistant that returns valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()

            print(f"Raw Content: {content}")

            content = strip_markdown(content)
            print(f"Cleaned Content: {content}")

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
                    # Convert price to string if it's a number
                    if 'price' in rec and rec['price'] is not None and not isinstance(rec['price'], str):
                        rec['price'] = str(rec['price'])
                    final_recommendations.append(Recommendation(**rec))
                except Exception as e:
                    print(f"Error validating recommendation: {e}")
            return final_recommendations

        except Exception as e:
            print(f"Process Web Results Error: {e}")
            return []
    
    # Add this method to the PromptedResponse class

    async def generate_surprise_recommendation(self, message_context: List[str]) -> str:
        """
        Analyzes chat context and suggests a surprising but relevant item.
        """
        context = "\n".join(message_context[-10:])  # Use the 10 most recent messages for context

        prompt = (
            "You are a perceptive shopping assistant with a knack for unexpected but delightful recommendations. "
            "Based on the following chat conversation, suggest ONE surprising item that the participants might be interested in, "
            "but haven't explicitly mentioned. The item should be somewhat related to their interests, but unexpected.\n\n"
            f"Chat conversation:\n{context}\n\n"
            "Rules:\n"
            "1. Suggest exactly ONE specific product, not a category\n"
            "2. Be specific (include brand, type, purpose, etc. when appropriate)\n"
            "3. Make it unexpected yet relevant to their apparent interests\n"
            "4. Return ONLY the name of the item, nothing else\n"
            "Example good responses: 'Ember Temperature Control Smart Mug', 'Sony WH-1000XM4 Noise Canceling Headphones'"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You suggest surprising but relevant product recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50, 
                temperature=0.7  
            )
            
            surprise_item = response.choices[0].message.content.strip()
            
            # Clean up the response if needed
            if surprise_item.startswith('"') and surprise_item.endswith('"'):
                surprise_item = surprise_item[1:-1]
            
            return surprise_item
            
        except Exception as e:
            print(f"Surprise Recommendation Error: {e}")
            return "unexpected gadget"  # Fallback recommendation

    async def generate_user_profile(self, user_history: dict) -> dict:
        """
        Analyzes a user's shopping history to generate a comprehensive shopping profile.
        """
        queries = user_history.get('queries', [])
        items = user_history.get('items', [])
        reactions = user_history.get('reactions', [])
        
        if not queries:
            return {
                "summary": "Not enough shopping history to generate a profile.",
                "shopping_personality": {"type": "Casual Browser", "traits": ["New User"]},
                "category_breakdown": {},
                "price_range_preference": "Unknown",
                "avg_price_interest": 0.0,
                "activity_level": "New User",
                "preferred_brands": [],
                "recommendations": ["Try searching for products to build your profile!"]
            }
        
        # Format the data for the AI to analyze
        formatted_data = {
            "queries": [
                {
                    "query": q["raw_query"],
                    "interpreted": q["interpreted_query"],
                    "date": q["created_at"].isoformat() if hasattr(q["created_at"], "isoformat") else str(q["created_at"])
                } for q in queries
            ],
            "items": [
                {
                    "name": i["item_name"],
                    "price": i["price"],
                    "vendor": i["vendor"],
                    "metadata": i["metadata"]
                } for i in items
            ],
            "reactions": [
                {
                    "item_id": r["recommended_item_id"],
                    "type": r["reaction_type"]
                } for r in reactions
            ]
        }
        
        # Prepare the prompt for the AI
        prompt = f"""
        You are an expert shopping analyst. Analyze this user's shopping history and generate a comprehensive profile:
        
        {json.dumps(formatted_data, indent=2)}
        
        Create a detailed shopping profile with the following structure:
        1. A brief summary of their shopping behavior (2-3 sentences)
        2. Their shopping personality type (choose one: Bargain Hunter, Luxury Seeker, Practical Buyer, Trendsetter, Tech Enthusiast, Fashion Forward, Minimalist, Impulse Shopper, Research Master, Casual Browser) 
        3. 3-5 specific traits that define their shopping behavior
        4. A breakdown of product categories they're interested in (as percentages)
        5. Their price range preference 
        6. Average price point they're interested in
        7. Their shopping activity level (Very Active, Active, Occasional, Rare)
        8. Their preferred brands (if detectable)
        9. 3-5 personalized product recommendations based on this profile, just the names of the products as strings in an array
        
        Return the analysis as a valid JSON object with these keys:
        "summary", "shopping_personality" (with nested "type" and "traits" array), "category_breakdown" (category name to percentage), "price_range_preference", "avg_price_interest" (as a number), "activity_level", "preferred_brands" (array), "recommendations" (array of product suggestions)
        It is essential that you return a valid JSON object. and just that
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.reasoning_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            content = strip_markdown(response.choices[0].message.content)
            profile_data = json.loads(content)
            return profile_data
        
        except Exception as e:
            print(f"Error in generating user profile: {str(e)}")
            # Return a basic profile if there's an error
            return {
                "summary": "Based on your limited shopping history, you appear to be exploring various products.",
                "shopping_personality": {"type": "Casual Browser", "traits": ["Exploratory", "Diverse Interests"]},
                "category_breakdown": {"General": 100.0},
                "price_range_preference": "Mid-range",
                "avg_price_interest": 99.99,
                "activity_level": "New User",
                "preferred_brands": [],
                "recommendations": ["Try searching for more specific products to get better recommendations!"]
            }

    def get_user_history(self, user_id):
        """
        Retrieves a user's complete shopping history from the database
        """
        # Get all queries by this user
        queries = self.db.query(Query).filter(Query.user_id == user_id).all()
        
        # Get all recommended items associated with these queries
        query_ids = [q.id for q in queries]
        items = []
        if query_ids:
            items = self.db.query(RecommendedItem).filter(RecommendedItem.query_id.in_(query_ids)).all()
        
        # Get all reactions by this user
        reactions = []
        if query_ids:
            reactions = self.db.query(Reaction).filter(Reaction.query_id.in_(query_ids)).all()
        
        # Format the data
        formatted_queries = []
        for query in queries:
            formatted_queries.append({
                'id': str(query.id),
                'query_type': query.query_type,
                'raw_query': query.raw_query,
                'interpreted_query': query.interpreted_query,
                'created_at': query.created_at
            })
        
        formatted_items = []
        for item in items:
            try:
                formatted_items.append({
                    'id': str(item.id),
                    'query_id': str(item.query_id),
                    'item_name': item.item_name,
                    'vendor': item.vendor,
                    'price': float(item.price) if item.price else 0.0,
                    'link': item.link,
                    'metadata': item.item_metadata if hasattr(item, 'item_metadata') else {},
                    'created_at': item.created_at
                })
            except Exception as e:
                print(f"Error formatting item {item.id}: {str(e)}")
                # Add a simpler version without the problematic fields
                formatted_items.append({
                    'id': str(item.id),
                    'item_name': item.item_name,
                    'price': 0.0,
                    'vendor': item.vendor if hasattr(item, 'vendor') else "Unknown",
                    'metadata': {}
                })
        
        # Reactions remain unchanged
        formatted_reactions = []
        for reaction in reactions:
            formatted_reactions.append({
                'id': str(reaction.id),
                'query_id': str(reaction.query_id),
                'recommended_item_id': str(reaction.recommended_item_id) if reaction.recommended_item_id else None,
                'reaction_type': reaction.reaction_type,
                'created_at': reaction.created_at
            })
        
        # Combine everything into a user history object
        return {
            'user_id': str(user_id),
            'queries': formatted_queries,
            'items': formatted_items,
            'reactions': formatted_reactions
        }