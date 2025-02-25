from sqlalchemy import (
    Column, String, Text, DateTime, func, ForeignKey, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    discord_id = Column(String, nullable=False, unique=True)
    username = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One user can have many queries
    queries = relationship("Query", back_populates="user")


class Query(Base):
    __tablename__ = "queries"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    query_type = Column(String, nullable=False)  # 'prompted' or 'unprompted'
    raw_query = Column(Text)  # For prompted queries
    interpreted_query = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="queries")
    # A query can have many recommended items:
    recommended_items = relationship("RecommendedItem", back_populates="query", cascade="all, delete")
    # A query can have many reactions:
    reactions = relationship("Reaction", back_populates="query", cascade="all, delete")


class RecommendedItem(Base):
    __tablename__ = "recommended_items"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id"), nullable=False)
    item_name = Column(Text, nullable=False)
    vendor = Column(Text, nullable=False)
    link = Column(Text, nullable=False)
    price = Column(Numeric, nullable=False)
    # Update the column mapping so that the Python attribute is the same as the DB column name.
    item_metadata = Column(JSONB)  # Now it will use the column name 'item_metadata'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    query = relationship("Query", back_populates="recommended_items")
    reactions = relationship("Reaction", back_populates="recommended_item", cascade="all, delete")



class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id"), nullable=False)
    recommended_item_id = Column(UUID(as_uuid=True), ForeignKey("recommended_items.id"), nullable=True)
    reaction_type = Column(String, nullable=False)  # 'wishlist' or 'dislike'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    query = relationship("Query", back_populates="reactions")
    recommended_item = relationship("RecommendedItem", back_populates="reactions")
