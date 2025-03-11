from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

import json



client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def interpret_chat(messages):
    """
    Input: List of recent messages (strings)
    Output: Parsed query as a dictionary:
      e.g. {
        "item": "wireless headphones",
        "type": "electronics",
        "price_range": "50-100",
        "number_of_results": 3
      }
      or { "item": None } if no shopping intent
    """
    # Join messages into one context
    context = "\n".join(messages)
    print(f"Interpret Chat Context: {context}")
    prompt = f"""
    You are a shopping assistant that extracts product search queries from chat conversations.

    Recent conversation:
    {context}

    Your task:
    1. If there is a shopping-related intent (i.e., someone wants to buy something), return a JSON with the following keys:
      - "item": a specific product name. Feel free to add adjectives to enhance specificity. For example:
          - If the user says "I want a pair of shoes that I can run in", you can return "running shoes".
          - If the user says "I want a pair of shoes that are comfortable", you can return "comfortable shoes".
          - If the user says "another, black ski mask thats scary", you can return "scary black ski mask".
      - "type": the product category (e.g., "electronics", "clothing", etc.) or None if not applicable.
      - "price_range": the price range as mentioned in the conversation (e.g., "0 - 100") or None if not specified.
      - "number_of_results": the number of search results. Default is 3 and must never be 1. If the user specifies a quantity (e.g., "I'm looking for 5 pairs of shoes"), use that number.

    2. If there is no shopping-related intent in the conversation, simply return:
      {{
        "item": null
      }}

    Examples:
    - Chat: "I'm looking for wireless headphones, any suggestions?"
      Output: {{ "item": "wireless headphones", "type": "electronics", "price_range": "50-200", "number_of_results": 3 }}

    - Chat: "I'm looking for headphones under $100"
      Output: {{ "item": "headphones", "type": "electronics", "price_range": "0 - 100", "number_of_results": 3 }}

    - Chat: "I'm looking for 5 pairs of shoes"
      Output: {{ "item": "shoes", "type": "clothing", "price_range": "100-200", "number_of_results": 5 }}

    - Chat: "Anyone played Valorant today?"
      Output: {{ "item": null }}

    Now, analyze the conversation above and return the correct output.
    """

    try:
        response = await client.chat.completions.create(model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful shopping assistant."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7)

        result_text = response.choices[0].message.content.strip()
        query = json.loads(result_text)
        print(f"Interpret Chat Result: {query}")
        return query
    except Exception as e:
        print(f"Interpret Chat Error: {e}")
        return {"item": None}
