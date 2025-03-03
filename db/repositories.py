from sqlalchemy.orm import Session
from db.models import User, Query, RecommendedItem, Reaction

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
