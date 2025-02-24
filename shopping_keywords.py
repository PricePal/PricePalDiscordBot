import re

# A more comprehensive list of shopping-related keywords and phrases.
SHOPPING_KEYWORDS = [
  # General shopping and purchase terms
    "buy", "purchase", "order", "shop", "shopping", "ecommerce", "e-commerce", 
    "retail", "wholesale", "online shopping", "order online", "buy online", "cart", "checkout",
    
     # Price and deals
    "deal", "price", "discount", "sale", "offer", "bargain", "cheap", "affordable",
    "low cost", "clearance", "markdown", "coupon", "promo code", "best price", "price comparison",
    "save money", "coupon code", "flash sale", "daily deal", "special discount", "price drop", "clearance sale",
    
    # Specific product categories and types
    "headphones", "laptop", "phone", "smartphone", "tablet", "TV", "television", "camera", "shoes",
    "apparel", "clothing", "accessory", "furniture", "kitchenware", "gadget", "electronics", "wearable",
    
    # Style and quality indicators
    "luxury", "designer", "premium", "high-end", "budget", "economical", "value", "quality",
    
       # Action phrases and intent signals
    "get a new", "need", "looking for", "in search of", "hunt for", "scouting", "seeking", "want",
    "buy now", "order now", "grab yours", "act now", "limited offer", "today only", "while supplies last",
    "exclusive deal", "must have", "don’t miss", "shop now", "instant savings", "get it now", "final sale",
    "find", "find a", "find a good", "find a good deal", "find a good deal on", "find a good deal on", "getting",
    "getting a", "getting a good", "getting a good deal", "getting a good deal on", "getting a good deal on",
    
    # Additional phrases indicating shopping interest
    "compare", "review", "shop around", "find a good deal", "sale event", "flash sale", "daily deals",
    "offer", "discounted", "limited time", "special offer", "clearance sale", "save money", "affordable price"
]

# Compile a regex pattern using word boundaries for robust matching.
pattern = re.compile(
    r'\b(' + '|'.join(map(re.escape, SHOPPING_KEYWORDS)) + r')\b',
    re.IGNORECASE
)

def is_potential_shopping_message(message: str) -> bool:
    """
    Returns True if the message contains any shopping-related keywords.
    This uses a regex for robust matching.
    """
    return bool(pattern.search(message))
