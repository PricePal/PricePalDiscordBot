#V0 (Cold start functions)
#Function To Get Top trends 

from supabase import create_client
from dotenv import load_dotenv 
import os


# Keep only one client initialization

load_dotenv()

supabase = create_client(
    #os.getenv("DATABASE_URL"),
    "https://pmmrezxcyemynydfiatc.supabase.co",
    os.getenv("DATABASE_KEY")
)



#V0 (Cold start functions)
# Function To Get Top Trends (with hardcoded URL and key)

def get_top_trending_items():
    """
    Calls the Supabase RPC function 'get_top_trending' and returns the result.
    Returns: List of trending items (max 10 items as defined in the SQL function)
    """
    try:
        response = supabase.rpc('get_top_trending').execute()
        return response.data
    except Exception as e:
        print("Error fetching trending items:", str(e))
        return None
  
"""
Example call of get_top_trending_items:
    top_items = get_top_trending_items()
    for item in top_items:
            print(item)
"""


