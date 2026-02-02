"""
Database service layer - handles all database operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional
import json

from database_models import (
    Player, SeasonStats, Projection, SearchHistory, 
    FavoritePlayer, CachedData
)


# ==================== PLAYER OPERATIONS ====================

def get_or_create_player(db: Session, nba_id: int, full_name: str, 
                         first_name: str = None, last_name: str = None) -> Player:
    """Get existing player or create new one"""
    player = db.query(Player).filter(Player.nba_id == nba_id).first()
    
    if not player:
        player = Player(
            nba_id=nba_id,
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        db.add(player)
        db.commit()
        db.refresh(player)
    
    return player


def get_player_by_name(db: Session, name: str) -> Optional[Player]:
    """Find player by name (case-insensitive)"""
    return db.query(Player).filter(
        func.lower(Player.full_name) == func.lower(name)
    ).first()


def get_all_players(db: Session, active_only: bool = True) -> List[Player]:
    """Get all players"""
    query = db.query(Player)
    if active_only:
        query = query.filter(Player.is_active == True)
    return query.all()


def search_players(db: Session, query: str, limit: int = 10) -> List[Player]:
    """Search players by name"""
    search_term = f"%{query}%"
    return db.query(Player).filter(
        or_(
            Player.full_name.ilike(search_term),
            Player.first_name.ilike(search_term),
            Player.last_name.ilike(search_term)
        )
    ).limit(limit).all()


# ==================== SEASON STATS OPERATIONS ====================

def save_season_stats(db: Session, player_id: int, season: str, stats: dict) -> SeasonStats:
    """Save or update season statistics"""
    # Check if stats already exist
    existing = db.query(SeasonStats).filter(
        and_(
            SeasonStats.player_id == player_id,
            SeasonStats.season == season
        )
    ).first()
    
    if existing:
        # Update existing
        for key, value in stats.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        season_stats = SeasonStats(
            player_id=player_id,
            season=season,
            **stats
        )
        db.add(season_stats)
        db.commit()
        db.refresh(season_stats)
        return season_stats


def get_player_seasons(db: Session, player_id: int) -> List[SeasonStats]:
    """Get all season stats for a player"""
    return db.query(SeasonStats).filter(
        SeasonStats.player_id == player_id
    ).order_by(SeasonStats.season.desc()).all()


def get_season_stats(db: Session, player_id: int, season: str) -> Optional[SeasonStats]:
    """Get specific season stats"""
    return db.query(SeasonStats).filter(
        and_(
            SeasonStats.player_id == player_id,
            SeasonStats.season == season
        )
    ).first()


# ==================== PROJECTION OPERATIONS ====================

def save_projection(db: Session, player_id: int, season: str, 
                   projection_type: str, projection_data: dict) -> Projection:
    """Save player projection"""
    # Check if projection exists
    existing = db.query(Projection).filter(
        and_(
            Projection.player_id == player_id,
            Projection.season == season,
            Projection.projection_type == projection_type
        )
    ).first()
    
    if existing:
        # Update existing
        for key, value in projection_data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        projection = Projection(
            player_id=player_id,
            season=season,
            projection_type=projection_type,
            **projection_data
        )
        db.add(projection)
        db.commit()
        db.refresh(projection)
        return projection


def get_player_projections(db: Session, player_id: int, season: str = None) -> List[Projection]:
    """Get projections for a player"""
    query = db.query(Projection).filter(Projection.player_id == player_id)
    
    if season:
        query = query.filter(Projection.season == season)
    
    return query.order_by(Projection.created_at.desc()).all()


def get_latest_projection(db: Session, player_id: int, 
                         season: str, projection_type: str) -> Optional[Projection]:
    """Get the most recent projection of a specific type"""
    return db.query(Projection).filter(
        and_(
            Projection.player_id == player_id,
            Projection.season == season,
            Projection.projection_type == projection_type
        )
    ).order_by(Projection.created_at.desc()).first()


# ==================== SEARCH HISTORY OPERATIONS ====================

def log_search(db: Session, player_id: int, ip_address: str = None, 
              user_agent: str = None) -> SearchHistory:
    """Log a player search"""
    # Check if recent search exists (within last hour)
    recent = db.query(SearchHistory).filter(
        and_(
            SearchHistory.player_id == player_id,
            SearchHistory.ip_address == ip_address,
            SearchHistory.last_searched > datetime.utcnow() - timedelta(hours=1)
        )
    ).first()
    
    if recent:
        # Update count
        recent.search_count += 1
        recent.last_searched = datetime.utcnow()
        db.commit()
        db.refresh(recent)
        return recent
    else:
        # Create new entry
        search = SearchHistory(
            player_id=player_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(search)
        db.commit()
        db.refresh(search)
        return search


def get_popular_players(db: Session, limit: int = 10) -> List[tuple]:
    """Get most searched players"""
    return db.query(
        Player,
        func.sum(SearchHistory.search_count).label('total_searches')
    ).join(SearchHistory).group_by(Player.id).order_by(
        func.sum(SearchHistory.search_count).desc()
    ).limit(limit).all()


def get_recent_searches(db: Session, limit: int = 10) -> List[SearchHistory]:
    """Get recent player searches"""
    return db.query(SearchHistory).order_by(
        SearchHistory.last_searched.desc()
    ).limit(limit).all()


# ==================== CACHE OPERATIONS ====================

def get_cached_data(db: Session, cache_key: str) -> Optional[dict]:
    """Get cached data if not expired"""
    cache = db.query(CachedData).filter(
        and_(
            CachedData.cache_key == cache_key,
            CachedData.expires_at > datetime.utcnow()
        )
    ).first()
    
    if cache:
        return json.loads(cache.cache_value)
    return None


def set_cached_data(db: Session, cache_key: str, data: dict, 
                   ttl_minutes: int = 60) -> CachedData:
    """Cache data with expiration time"""
    expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
    
    # Check if cache key exists
    existing = db.query(CachedData).filter(
        CachedData.cache_key == cache_key
    ).first()
    
    if existing:
        # Update existing
        existing.cache_value = json.dumps(data)
        existing.expires_at = expires_at
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        cache = CachedData(
            cache_key=cache_key,
            cache_value=json.dumps(data),
            expires_at=expires_at
        )
        db.add(cache)
        db.commit()
        db.refresh(cache)
        return cache


def clear_expired_cache(db: Session) -> int:
    """Remove expired cache entries"""
    count = db.query(CachedData).filter(
        CachedData.expires_at < datetime.utcnow()
    ).delete()
    db.commit()
    return count


# ==================== FAVORITE OPERATIONS ====================

def add_favorite(db: Session, user_id: str, player_id: int, notes: str = None) -> FavoritePlayer:
    """Add player to favorites"""
    # Check if already favorited
    existing = db.query(FavoritePlayer).filter(
        and_(
            FavoritePlayer.user_id == user_id,
            FavoritePlayer.player_id == player_id
        )
    ).first()
    
    if existing:
        return existing
    
    favorite = FavoritePlayer(
        user_id=user_id,
        player_id=player_id,
        notes=notes
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def remove_favorite(db: Session, user_id: str, player_id: int) -> bool:
    """Remove player from favorites"""
    count = db.query(FavoritePlayer).filter(
        and_(
            FavoritePlayer.user_id == user_id,
            FavoritePlayer.player_id == player_id
        )
    ).delete()
    db.commit()
    return count > 0


def get_user_favorites(db: Session, user_id: str) -> List[FavoritePlayer]:
    """Get user's favorite players"""
    return db.query(FavoritePlayer).filter(
        FavoritePlayer.user_id == user_id
    ).order_by(FavoritePlayer.added_at.desc()).all()


# ==================== ANALYTICS ====================

def get_stats_summary(db: Session) -> dict:
    """Get database statistics"""
    return {
        "total_players": db.query(Player).count(),
        "active_players": db.query(Player).filter(Player.is_active == True).count(),
        "total_seasons": db.query(SeasonStats).count(),
        "total_projections": db.query(Projection).count(),
        "total_searches": db.query(func.sum(SearchHistory.search_count)).scalar() or 0,
        "cached_entries": db.query(CachedData).filter(
            CachedData.expires_at > datetime.utcnow()
        ).count()
    }