from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from db.models import User, Query, RecommendedItem, Reaction
from PIL import Image, ImageDraw, ImageFont
import random
import numpy as np
import io

class UserProfileAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        
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
            formatted_items.append({
                'id': str(item.id),
                'query_id': str(item.query_id),
                'item_name': item.item_name,
                'vendor': item.vendor,
                'price': float(item.price),
                'link': item.link,
                'metadata': item.item_metadata,
                'created_at': item.created_at
            })
            
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
    
    def generate_personality_image(self, personality_data):
        """
        Creates a visual representation of the user's shopping personality
        """
        # Create a base image (500x200)
        img = Image.new('RGBA', (500, 200), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Define personality types and their colors
        personality_colors = {
            "Bargain Hunter": (76, 175, 80),     # Green
            "Luxury Seeker": (156, 39, 176),     # Purple
            "Practical Buyer": (3, 169, 244),    # Blue
            "Trendsetter": (255, 87, 34),        # Orange
            "Tech Enthusiast": (33, 150, 243),   # Light Blue
            "Fashion Forward": (233, 30, 99),    # Pink
            "Minimalist": (158, 158, 158),       # Gray
            "Impulse Shopper": (255, 193, 7),    # Amber
            "Research Master": (63, 81, 181),    # Indigo
            "Casual Browser": (139, 195, 74)     # Light Green
        }
        
        # Default color if personality not found
        personality_type = personality_data.get('type', 'Casual Browser')
        color = personality_colors.get(personality_type, (100, 100, 100))
        
        # Draw personality blob (abstract representation)
        center_x, center_y = 250, 100
        
        # Draw dots representing traits with randomness for visual interest
        traits = personality_data.get('traits', [])
        for i, trait in enumerate(traits[:5]):  # Limit to 5 traits
            angle = (i / 5) * 2 * np.pi
            distance = random.randint(50, 80)
            x = center_x + int(np.cos(angle) * distance)
            y = center_y + int(np.sin(angle) * distance)
            
            # Draw connecting line
            draw.line((center_x, center_y, x, y), fill=color, width=2)
            
            # Draw circle at trait point
            circle_size = 20
            draw.ellipse((x-circle_size/2, y-circle_size/2, x+circle_size/2, y+circle_size/2), 
                         fill=color, outline=(0, 0, 0))
        
        # Draw central personality circle
        draw.ellipse((center_x-40, center_y-40, center_x+40, center_y+40), 
                     fill=color, outline=(0, 0, 0, 128))
        
        return img
