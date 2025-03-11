from sqlalchemy.orm import Session
from db.models import User, Query, RecommendedItem, Reaction
from sqlalchemy.sql import text
import json
import traceback

# --------------- USER REPOSITORY ---------------
def create_or_get_user(db: Session, discord_id: str, username: str) -> User:
    existing = db.query(User).filter(User.discord_id == discord_id).first()
    if existing:
        return existing
    user = User(discord_id=discord_id, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_discord_id(db: Session, discord_id: str) -> User:
    return db.query(User).filter(User.discord_id == discord_id).first()


# --------------- QUERIES REPOSITORY ---------------
def create_query(db: Session, user_id: str, query_type: str, raw_query: str, interpreted_query: dict) -> Query:
    query = Query(
        user_id=user_id,
        query_type=query_type,
        raw_query=raw_query,
        interpreted_query=interpreted_query
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query

def get_queries_for_user(db: Session, user_id: str):
    return db.query(Query).filter(Query.user_id == user_id).all()


# --------------- RECOMMENDED ITEMS REPOSITORY ---------------
def create_recommended_item(db: Session, query_id: str, item_name: str, vendor: str, link: str, price: float, metadata: dict) -> RecommendedItem:
    item = RecommendedItem(
        query_id=query_id,
        item_name=item_name,
        vendor=vendor,
        link=link,
        price=price,
        item_metadata=metadata  # Use the attribute name "item_metadata"
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def get_recommended_items(db: Session):
    return db.query(RecommendedItem).all()


# --------------- REACTIONS REPOSITORY ---------------
def create_reaction(db: Session, query_id: str, recommended_item_id: str, reaction_type: str) -> Reaction:
    reaction = Reaction(
        query_id=query_id,
        recommended_item_id=recommended_item_id,
        reaction_type=reaction_type
    )
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction

def get_reactions_for_query(db: Session, query_id: str):
    return db.query(Reaction).filter(Reaction.query_id == query_id).all()


# Add this function to retrieve wishlist items
def get_wishlist_items_for_user(db: Session, user_id: str, limit: int = None):
    """
    Get all items that a user has added to their wishlist.
    
    Args:
        db: Database session
        user_id: The user's ID to get wishlist items for
        limit: Optional maximum number of items to return
        
    Returns:
        List of RecommendedItem objects in the user's wishlist
    """
    # Join queries, reactions, and recommended_items tables to get all wishlist items
    wishlist_items = (
        db.query(RecommendedItem)
        .join(Reaction, Reaction.recommended_item_id == RecommendedItem.id)
        .join(Query, Query.id == Reaction.query_id)
        .filter(Query.user_id == user_id)
        .filter(Reaction.reaction_type == "wishlist")
        .order_by(RecommendedItem.created_at.desc())
    )
    
    # Apply limit if provided
    if limit is not None:
        wishlist_items = wishlist_items.limit(limit)
        
    return wishlist_items.all()

def get_recent_queries_by_user(db: Session, user_id: str, limit: int = 5):
    """
    Get the most recent queries for a specific user.
    """
    from db.models import Query
    
    return db.query(Query)\
        .filter(Query.user_id == user_id)\
        .order_by(Query.created_at.desc())\
        .limit(limit)\
        .all()

def delete_all_recommendations_for_user(db: Session, user_id: str):
    """
    Deletes all existing recommendations for a user.
    """
    db.execute(
        text("""
        DELETE FROM recommendation_service_table 
        WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    db.commit()

def insert_recommendation_for_user(db: Session, user_id: str, item_name: str, vendor: str, 
                                  link: str, price: float, metadata: dict):
    """
    Inserts a new recommendation for a user.
    """
    db.execute(
        text("""
        INSERT INTO recommendation_service_table
        (user_id, item_name, vendor, link, price, metadata)
        VALUES (:user_id, :item_name, :vendor, :link, :price, :metadata)
        """),
        {
            "user_id": user_id,
            "item_name": item_name,
            "vendor": vendor,
            "link": link,
            "price": price,
            "metadata": json.dumps(metadata)
        }
    )
    db.commit()

def get_latest_recommendations_for_user(db: Session, user_id: str, limit: int = 6):
    """
    Get the most recent recommendations for a specific user from the recommendation_service_table
    """
    try:
        # Use text() function to properly declare the SQL query
        query = text("""
            SELECT * FROM recommendation_service_table
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        result = db.execute(query, {"user_id": user_id, "limit": limit})
        
        # Fixed conversion approach for Row objects
        recommendations = []
        for row in result:
            # Convert each row to a dictionary using the proper _mapping attribute
            row_dict = {key: value for key, value in row._mapping.items()}
            recommendations.append(row_dict)
        
        return recommendations
    except Exception as e:
        print(f"Database error in get_latest_recommendations_for_user: {e}")
        traceback.print_exc()  
        return []
