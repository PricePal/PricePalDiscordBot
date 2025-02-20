import requests
import json
from serpapi.google_search import GoogleSearch

SERP_API_KEY = 'fc6dac52bcb0783e08a89abc7a2f4ab4d1282554e3b70eeab6098fb55d607641' 


#old working verion
"""
def web_search_tool(item, region):
    # Set up the parameters for the search
    api_key = SERP_API_KEY
    params = {
        "engine": "google_shopping",
        "q": item,
        "gl": region,       
        "api_key": api_key
    }
    
    # Create the search object and retrieve results
    search = GoogleSearch(params)
    results = search.get_dict()
    
    # Get the shopping results; if none exist, default to an empty list.
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
    result =  "\n".join(output)
    return result

"""

#new verison:

def web_search_tool(item: str, region: str) -> str:

    #Searches Google Shopping for the given item and returns a formatted string with purchase options.
 
    print("entered web_search_tool")
    params = {
        "engine": "google_shopping",
        "q": item,
        "gl": region,
        "api_key": SERP_API_KEY
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

  # Example usage:
if __name__ == "__main__":
    item = "Gaming Mouse"
    region = "United States"  # Change to your desired region code
    check = web_search_tool(item, region)
    print(check)
    
