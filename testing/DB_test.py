# DB_test.py

from db.database import SessionLocal, engine
from db.models import Base
from db.repositories import (
    create_or_get_user, get_user_by_discord_id,
    create_query, create_recommended_item, create_reaction
)

def main():
    # Optionally create tables if needed:
    # Base.metadata.create_all(bind=engine)

    # Create a new session
    db = SessionLocal()
    try:
        print("trying to create user")
        user = create_or_get_user(db, discord_id="123456789", username="testuser")
        print("User:", user.id, user.discord_id, user.username)

        # Create a prompted query
        new_query = create_query(
            db,
            user_id=user.id,
            query_type="prompted",  # Allowed value: 'prompted'
            raw_query="find me a gaming laptop",
            interpreted_query={"category": "electronics", "type": "laptop", "purpose": "gaming"}
        )
        print("Created query:", new_query.id, new_query.query_type, new_query.raw_query)

        # Create a recommended item tied to the query
        rec_item = create_recommended_item(
            db,
            query_id=new_query.id,
            item_name="Gaming Laptop",
            vendor="VendorX",
            link="https://example.com",
            price=999.99,
            metadata={"color": "black"}  # This will be stored in the 'metadata' column as JSONB
        )
        print("Created recommended item:", rec_item.id, rec_item.item_name, rec_item.price)

        # Create a reaction tied to both the query and the recommended item
        reaction = create_reaction(
            db,
            query_id=new_query.id,
            recommended_item_id=rec_item.id,
            reaction_type="wishlist"  # Allowed value: 'wishlist'
        )
        print("Created reaction:", reaction.id, reaction.reaction_type)

        # Fetch back the user for verification
        same_user = get_user_by_discord_id(db, "123456789")
        print("Fetched user by discord_id:", same_user)
    finally:
        db.close()

if __name__ == "__main__":
    main()
