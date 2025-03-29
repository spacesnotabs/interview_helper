"""
Database models for the interview helper application.
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
import enum
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from .database import Base


class LlmModel(enum.Enum):
    """Available LLM models."""
    # Gemini models
    GEMINI_2_FLASH = "gemini-2.0-flash"
    GEMINI_2_PRO = "gemini-2.0-pro"
    GEMINI_15_PRO = "gemini-1.5-pro"
    GEMINI_1_PRO = "gemini-1.0-pro"
    # Claude models
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    CLAUDE_2_1 = "claude-2.1"
    # OpenAI models
    GPT_4O = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"


class LlmProvider(enum.Enum):
    """Available LLM providers."""
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    GEMINI = "Gemini"

    def get_models(self):
        """Get available models for this provider."""
        models_map = {
            self.GEMINI: [
                {"value": LlmModel.GEMINI_2_FLASH.value, "label": "Gemini 2.0 Flash"},
                {"value": LlmModel.GEMINI_2_PRO.value, "label": "Gemini 2.0 Pro"},
                {"value": LlmModel.GEMINI_15_PRO.value, "label": "Gemini 1.5 Pro"},
                {"value": LlmModel.GEMINI_1_PRO.value, "label": "Gemini 1.0 Pro"}
            ],
            self.ANTHROPIC: [
                {"value": LlmModel.CLAUDE_3_OPUS.value, "label": "Claude 3 Opus"},
                {"value": LlmModel.CLAUDE_3_SONNET.value, "label": "Claude 3 Sonnet"},
                {"value": LlmModel.CLAUDE_3_HAIKU.value, "label": "Claude 3 Haiku"},
                {"value": LlmModel.CLAUDE_2_1.value, "label": "Claude 2.1"}
            ],
            self.OPENAI: [
                {"value": LlmModel.GPT_4O.value, "label": "GPT-4o"},
                {"value": LlmModel.GPT_4_TURBO.value, "label": "GPT-4 Turbo"},
                {"value": LlmModel.GPT_4.value, "label": "GPT-4"},
                {"value": LlmModel.GPT_35_TURBO.value, "label": "GPT-3.5 Turbo"}
            ]
        }
        return models_map[self]


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