from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class TokenUsage(Base):
    """Track OpenAI token usage"""
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)