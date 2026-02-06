from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List
from app.models.token_usage import TokenUsage


class TokenUsageRepository:
    """Database operations for token usage tracking"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        agent_name: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ) -> TokenUsage:
        """Log token usage"""
        usage = TokenUsage(
            agent_name=agent_name,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        return usage

    def get_stats(self) -> Dict[str, int]:
        """Get aggregated token usage statistics"""
        stats = self.db.query(
            func.sum(TokenUsage.prompt_tokens).label('total_prompt'),
            func.sum(TokenUsage.completion_tokens).label('total_completion'),
            func.sum(TokenUsage.total_tokens).label('total'),
            func.count(TokenUsage.id).label('request_count')
        ).first()

        # Handle case where no records exist
        if not stats:
            return {
                'total_prompt_tokens': 0,
                'total_completion_tokens': 0,
                'total_tokens': 0,
                'total_requests': 0
            }

        return {
            'total_prompt_tokens': int(stats.total_prompt or 0),
            'total_completion_tokens': int(stats.total_completion or 0),
            'total_tokens': int(stats.total or 0),
            'total_requests': int(stats.request_count or 0)
        }

    def get_recent(self, limit: int = 100) -> List[TokenUsage]:
        """Get recent token usage history"""
        return self.db.query(TokenUsage).order_by(
            TokenUsage.created_at.desc()
        ).limit(limit).all()

    def get_by_agent(self, agent_name: str) -> List[TokenUsage]:
        """Get token usage for specific agent"""
        return self.db.query(TokenUsage).filter(
            TokenUsage.agent_name == agent_name
        ).order_by(TokenUsage.created_at.desc()).all()
