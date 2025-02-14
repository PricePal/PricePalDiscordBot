import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def interpret_chat(messages):
    """
    Input: List of recent messages (strings)
    Output: Parsed query as a dictionary
    """

    # Join messages into a single string
    context = "\n".join(messages)

    # Define LLM prompt for extracting a search query
    prompt = f"""
    You are a shopping assistant that extracts product search queries from chat conversations.

    Here is the recent conversation:
    {context}

    If there is a shopping-related intent (e.g., someone wants to buy something), generate a search query with the following format:
    {{ "item": "<product name>", "type": "<category>", "price_range": "<price range or None>", "number_of_results": 3 }}

    If there is **no shopping intent**, simply return:
    {{ "item": null }}

    Examples:
    Chat: "I'm looking for wireless headphones, any suggestions?"
    Output: {{ "item": "wireless headphones", "type": "electronics", "price_range": "50-200", "number_of_results": 3 }}

    If the user mentions a specific price range, include it in the output.
    Chat: "I'm looking for headphones under $100"
    Output: {{ "item": "headphones", "type": "electronics", "price_range": "0 - 100", "number_of_results": 3 }}

    If the user mentions a specific amount of items, include it in the output.
    Chat: "I'm looking for 5 pairs of shoes"
    Output: {{ "item": "shoes", "type": "clothing", "price_range": "100-200", "number_of_results": 5 }}

    The number of results should be 3 by default and never 1
    
    Chat: "Anyone played Valorant today?"
    Output: {{ "item": null }}

    Now, analyze the chat above and return the correct output:
    """

    # Call LLM API
    response = openai.ChatCompletion.create(
        model="gpt-4", 
        messages=[
            {"role": "system", "content": "You are a helpful shopping assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    # Extract the result from the LLM response
    result_text = response['choices'][0]['message']['content'].strip()

    # You can improve parsing here later, but for now:
    try:
        query = eval(result_text)  # Quick and dirty for now, switch to json.loads() later
    except:
        query = {"item": None}

    return query
