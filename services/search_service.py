from serpapi import GoogleSearch

class SearchService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def search_shopping(self, item_name: str, region: str, price_range: str = None) -> str:
        """
        Searches Google Shopping for the given item and returns formatted results.
        """
        q = item_name
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
            "api_key": self.api_key
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
        return "\n".join(output) 