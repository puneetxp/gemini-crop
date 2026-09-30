"""
SQLAlchemy ORM model for users table
Used for authentication and user management
Matches the schema generated from database/Model/user.json
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, BigInteger, SmallInteger, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import synonym
from app.core.database import Base


class User(Base):
    """SQLAlchemy ORM model for users table - matches generated schema"""
    
    __tablename__ = "users"
    
    # Primary key - BIGINT auto-increment (matches generated schema)
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    
    # Standard auto-generated fields
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    enable = Column(SmallInteger, nullable=False, server_default='1')
    
    # Authentication fields (from user.json)
    cognito_user_id = Column(String(255), unique=True, nullable=True, index=True)
    firebase_id = Column(String(255), unique=True, nullable=True, index=True)
    username = Column(String(100), nullable=False, index=True)  # Display username (distinct from email)
    name = Column(String(255), nullable=False)  # Full name (called 'name' in JSON model)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(255), unique=True, nullable=True, index=True)  # Called 'phone' in JSON model
    
    # OAuth fields
    google_id = Column(String(255), nullable=True)
    facebook_id = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)  # Hashed password for traditional login
    
    # User information
    user_type = Column(String(255), nullable=True, server_default='farmer')  # farmer, buyer, admin
    preferred_language = Column(String(255), nullable=True, server_default='en')  # en, hi, ta, te, mr, bn
    mfa_enabled = Column(SmallInteger, nullable=True, server_default='0')
    
    # Address fields
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    pincode = Column(String(10), nullable=True)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    village = Column(String(100), nullable=True)
    address_line = Column(String(255), nullable=True)
    
    # Additional fields for authentication (not in JSON model, but needed by auth code)
    # Underlying schema stores these as SMALLINT (0/1), so keep types aligned to avoid casting errors
    is_active = Column(SmallInteger, nullable=True, server_default='1')
    is_verified = Column(SmallInteger, nullable=True, server_default='0')
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', user_type='{self.user_type}')>"
