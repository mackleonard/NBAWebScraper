"""
Database models for NBA Analytics
Uses SQLAlchemy ORM for database operations
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Player(Base):
    """Store player information"""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True, index=True)
    nba_id = Column(Integer, unique=True, index=True)  # NBA API ID
    full_name = Column(String(100), nullable=False, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    season_stats = relationship("SeasonStats", back_populates="player", cascade="all, delete-orphan")
    projections = relationship("Projection", back_populates="player", cascade="all, delete-orphan")
    search_history = relationship("SearchHistory", back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.full_name}', active={self.is_active})>"


class SeasonStats(Base):
    """Store season statistics for players"""
    __tablename__ = 'season_stats'
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    season = Column(String(10), nullable=False, index=True)  # e.g., "2025-26"
    
    # Game stats
    games_played = Column(Integer)
    minutes_per_game = Column(Float)
    points_per_game = Column(Float)
    rebounds_per_game = Column(Float)
    assists_per_game = Column(Float)
    steals_per_game = Column(Float)
    blocks_per_game = Column(Float)
    turnovers_per_game = Column(Float)
    
    # Shooting stats
    field_goal_percentage = Column(Float)
    three_point_percentage = Column(Float)
    free_throw_percentage = Column(Float)
    three_pointers_made_per_game = Column(Float)
    
    # Totals
    total_points = Column(Integer)
    total_rebounds = Column(Integer)
    total_assists = Column(Integer)
    
    # Fantasy
    fantasy_points_per_game = Column(Float)
    fantasy_points_total = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    player = relationship("Player", back_populates="season_stats")
    
    def __repr__(self):
        return f"<SeasonStats(player_id={self.player_id}, season='{self.season}', ppg={self.points_per_game})>"


class Projection(Base):
    """Store AI-generated projections for players"""
    __tablename__ = 'projections'
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    season = Column(String(10), nullable=False)  # e.g., "2025-26"
    projection_type = Column(String(50))  # "next_game", "season", "career_average", etc.
    
    # Projected stats
    projected_games = Column(Integer)
    projected_minutes_per_game = Column(Float)
    projected_points_per_game = Column(Float)
    projected_rebounds_per_game = Column(Float)
    projected_assists_per_game = Column(Float)
    projected_steals_per_game = Column(Float)
    projected_blocks_per_game = Column(Float)
    projected_turnovers_per_game = Column(Float)
    projected_three_pointers_per_game = Column(Float)
    
    # Fantasy projection
    projected_fantasy_points_per_game = Column(Float)
    projected_fantasy_points_season = Column(Float)
    
    # Metadata
    confidence_score = Column(Float)  # 0-100
    method = Column(String(50))  # "weighted_average", "age_adjusted", etc.
    trend = Column(String(20))  # "trending_up", "trending_down", "stable"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    player = relationship("Player", back_populates="projections")
    
    def __repr__(self):
        return f"<Projection(player_id={self.player_id}, season='{self.season}', type='{self.projection_type}')>"


class SearchHistory(Base):
    """Track user search history and popular players"""
    __tablename__ = 'search_history'
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    search_count = Column(Integer, default=1)
    last_searched = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    
    # Relationship
    player = relationship("Player", back_populates="search_history")
    
    def __repr__(self):
        return f"<SearchHistory(player_id={self.player_id}, count={self.search_count})>"


class FavoritePlayer(Base):
    """Store user favorite players (for future user accounts)"""
    __tablename__ = 'favorite_players'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)  # Can be session ID or user ID
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    def __repr__(self):
        return f"<FavoritePlayer(user_id='{self.user_id}', player_id={self.player_id})>"


class CachedData(Base):
    """Cache API responses to reduce NBA API calls"""
    __tablename__ = 'cached_data'
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, index=True, nullable=False)
    cache_value = Column(Text, nullable=False)  # JSON string
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CachedData(key='{self.cache_key}', expires={self.expires_at})>"


class FantasySettings(Base):
    """Store user's custom fantasy scoring settings"""
    __tablename__ = 'fantasy_settings'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)  # Session ID or user ID
    
    # Scoring weights
    points_weight = Column(Float, default=1.0)
    rebounds_weight = Column(Float, default=1.0)
    assists_weight = Column(Float, default=1.5)
    steals_weight = Column(Float, default=2.0)
    blocks_weight = Column(Float, default=2.0)
    turnovers_weight = Column(Float, default=-2.0)
    three_pointers_weight = Column(Float, default=1.0)  # Bonus
    offensive_rebounds_weight = Column(Float, default=0.5)  # Bonus
    
    # Additional optional stats
    field_goals_made_weight = Column(Float, default=0.0)
    field_goals_missed_weight = Column(Float, default=0.0)
    free_throws_made_weight = Column(Float, default=0.0)
    free_throws_missed_weight = Column(Float, default=0.0)
    double_double_bonus = Column(Float, default=0.0)
    triple_double_bonus = Column(Float, default=0.0)
    
    # Settings metadata
    name = Column(String(100), default="Custom Settings")  # User-defined name
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FantasySettings(user_id='{self.user_id}', name='{self.name}')>"
    
    def to_dict(self):
        """Convert to dictionary for easy JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'points': self.points_weight,
            'rebounds': self.rebounds_weight,
            'assists': self.assists_weight,
            'steals': self.steals_weight,
            'blocks': self.blocks_weight,
            'turnovers': self.turnovers_weight,
            'three_pointers': self.three_pointers_weight,
            'offensive_rebounds': self.offensive_rebounds_weight,
            'field_goals_made': self.field_goals_made_weight,
            'field_goals_missed': self.field_goals_missed_weight,
            'free_throws_made': self.free_throws_made_weight,
            'free_throws_missed': self.free_throws_missed_weight,
            'double_double': self.double_double_bonus,
            'triple_double': self.triple_double_bonus,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }