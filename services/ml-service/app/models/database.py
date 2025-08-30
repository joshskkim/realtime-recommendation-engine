"""
Database models and configuration
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://recuser:recpass123@postgres:5432/recommendations")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String(20))
    preferred_categories = Column(ARRAY(String))
    registration_date = Column(DateTime, server_default=func.now())
    is_premium = Column(Boolean, default=False)
    location = Column(String(10))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    interactions = relationship("Interaction", back_populates="user")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    recommendations = relationship("Recommendation", back_populates="user")


class Item(Base):
    """Item/Content model"""
    __tablename__ = "items"
    
    item_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), index=True)
    features = Column(JSON)
    created_date = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    interactions = relationship("Interaction", back_populates="item")
    item_features = relationship("ItemFeatures", back_populates="item", uselist=False)
    recommendations = relationship("Recommendation", back_populates="item")


class Interaction(Base):
    """User-Item interaction model"""
    __tablename__ = "interactions"
    
    interaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), index=True)
    item_id = Column(Integer, ForeignKey("items.item_id"), index=True)
    interaction_type = Column(String(20), nullable=False, index=True)
    rating = Column(Float)
    session_id = Column(String(50))
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    item = relationship("Item", back_populates="interactions")


class UserProfile(Base):
    """User profile with ML features"""
    __tablename__ = "user_profiles"
    
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    interaction_count = Column(Integer, default=0)
    avg_rating = Column(Float)
    favorite_categories = Column(ARRAY(String))
    last_activity = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")


class ItemFeatures(Base):
    """Item features for content-based filtering"""
    __tablename__ = "item_features"
    
    item_id = Column(Integer, ForeignKey("items.item_id"), primary_key=True)
    popularity_score = Column(Float, default=0.0)
    avg_rating = Column(Float)
    interaction_count = Column(Integer, default=0)
    feature_vector = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    item = relationship("Item", back_populates="item_features")


class Recommendation(Base):
    """Cached recommendations"""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), index=True)
    item_id = Column(Integer, ForeignKey("items.item_id"))
    score = Column(Float, index=True)
    algorithm = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    item = relationship("Item", back_populates="recommendations")


# Database dependency
def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()