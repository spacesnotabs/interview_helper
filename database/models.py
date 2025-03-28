"""
Database models for the interview helper application.
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
import enum
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from .database import Base


class LlmProvider(enum.Enum):
    """Available LLM providers."""
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    GEMINI = "Gemini"


class User(Base):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with LlmApiKey
    api_keys = relationship("LlmApiKey", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, username, password):
        self.username = username
        self.set_password(password)
    
    def set_password(self, password):
        """Hash password and store it."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user object to dictionary (without password)."""
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class LlmApiKey(Base):
    """Model for storing LLM API keys."""
    __tablename__ = 'llm_api_keys'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    llm_provider = Column(Enum(LlmProvider), nullable=False)
    api_key = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with User
    user = relationship("User", back_populates="api_keys")
    
    def __init__(self, user_id, llm_provider, api_key):
        self.user_id = user_id
        self.llm_provider = llm_provider
        self.api_key = api_key
    
    def to_dict(self):
        """Convert API key object to dictionary (with masked key for safety)."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'llm_provider': self.llm_provider.value,
            'api_key': '••••••' + self.api_key[-4:] if self.api_key else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<LlmApiKey {self.llm_provider.value} for user {self.user_id}>'