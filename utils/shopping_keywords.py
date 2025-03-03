import re

# A more comprehensive list of shopping-related keywords and phrases.
SHOPPING_KEYWORDS = [
  # General shopping and purchase terms
    "buy", "buying", "bought", "buys", "buyer", "buyers",
    "purchase", "purchasing", "purchased", "purchases", "purchaser",
    "order", "ordering", "ordered", "orders",
    "shop", "shopping", "shopped", "shops", "shopper", "shoppers",
    "ecommerce", "e-commerce", "retail", "retailing", "retailer", "retailers",
    "wholesale", "wholesaler", "wholesalers", "wholesaling",
    "online shopping", "order online", "buy online", "ordering online", "purchasing online",
    "cart", "shopping cart", "add to cart", "added to cart", "checkout", "checking out",
    "transaction", "transactional", "browse", "browsing", "browsed",
    "merchant", "merchants", "vendor", "vendors", "seller", "sellers", "selling",
    
    # Price and deals
    "deal", "deals", "price", "prices", "pricing", "priced",
    "discount", "discounted", "discounting", "discounts",
    "sale", "sales", "on sale", "for sale", "selling",
    "offer", "offering", "offered", "offers", "special offer",
    "bargain", "bargaining", "bargained", "bargains", 
    "cheap", "cheaper", "cheapest", "inexpensive",
    "affordable", "affordability", "low cost", "low-cost", "budget",
    "clearance", "markdown", "marked down", "reduced",
    "coupon", "coupons", "promo", "promo code", "promotional", "promotion", "promotions",
    "best price", "price comparison", "comparing prices",
    "save", "saving", "savings", "saved", "saves", "saver",
    "coupon code", "flash sale", "daily deal", "special discount", 
    "price drop", "dropped price", "clearance sale", "rebate", "rebates",
    
    # Specific product categories and types
    "headphones", "laptop", "laptops", "phone", "phones", "smartphone", "smartphones",
    "tablet", "tablets", "TV", "TVs", "television", "televisions", 
    "camera", "cameras", "shoes", "apparel", "clothing", "clothes", "dress", "dresses",
    "accessory", "accessories", "furniture", "kitchenware", "gadget", "gadgets",
    "electronics", "electronic", "wearable", "wearables", "device", "devices",
    "appliance", "appliances", "home goods", "housewares", "jewelry", "watch", "watches",
    "boat", "boats", "vehicle", "vehicles", "car", "cars", "truck", "trucks",
    
    # Style and quality indicators
    "luxury", "luxurious", "designer", "premium", "high-end", "high end",
    "budget", "budgeting", "economical", "value", "valuable", "quality",
    "brand", "branded", "brands", "name brand", "top-tier", "top tier",
    
    # Action phrases and intent signals
    "get a new", "getting a new", "need", "needs", "needing", "needed",
    "looking for", "look for", "searching for", "searched for", "search for",
    "in search of", "hunt for", "hunting for", "scouting", "scouting for",
    "seeking", "seek", "sought", "want", "wanting", "wanted", "wants",
    "buy now", "order now", "grab", "grabbing", "act now", "limited offer",
    "today only", "while supplies last", "exclusive deal", "must have",
    "don't miss", "shop now", "instant savings", "get it now", "final sale",
    "find", "finding", "found", "find a", "find a good", "find a good deal",
    "getting", "get", "got", "getting a", "getting a good", "getting a good deal",
    "thinking of buying", "thinking of getting", "planning to buy", "planning to purchase",
    "interested in buying", "interested in purchasing", "want to buy", "want to purchase",
    "considering buying", "considering purchasing", "thinking about buying",
    
    # Additional phrases indicating shopping interest
    "compare", "comparing", "compared", "compares", "comparison",
    "review", "reviewing", "reviewed", "reviews", "reviewer",
    "shop around", "shopping around", "find a good deal", "found a good deal",
    "sale event", "flash sale", "daily deals", "offer", "offering",
    "discounted", "discounting", "limited time", "special offer",
    "clearance sale", "save money", "saving money", "saved money",
    "affordable price", "reasonable price", "best deal", "better deal"
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

    if message.startswith("!"):
        return False

    return bool(pattern.search(message))
