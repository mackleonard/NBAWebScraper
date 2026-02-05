"""
Fantasy Settings Service - Manage user fantasy scoring preferences
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from database_models import FantasySettings


# Default fantasy scoring (standard settings)
DEFAULT_SCORING = {
    'points': 1.0,
    'rebounds': 1.0,
    'assists': 1.5,
    'steals': 2.0,
    'blocks': 2.0,
    'turnovers': -2.0,
    'three_pointers': 1.0,
    'offensive_rebounds': 0.5,
    'field_goals_made': 0.0,
    'field_goals_missed': 0.0,
    'free_throws_made': 0.0,
    'free_throws_missed': 0.0,
    'double_double': 0.0,
    'triple_double': 0.0
}


def get_default_settings() -> dict:
    """Get default fantasy scoring settings"""
    return DEFAULT_SCORING.copy()


def get_user_settings(db: Session, user_id: str) -> Optional[FantasySettings]:
    """Get user's fantasy settings, or None if not set"""
    return db.query(FantasySettings).filter(
        FantasySettings.user_id == user_id
    ).first()


def get_or_create_user_settings(db: Session, user_id: str) -> FantasySettings:
    """Get user settings or create with defaults"""
    settings = get_user_settings(db, user_id)
    
    if not settings:
        settings = FantasySettings(
            user_id=user_id,
            name="My Settings",
            **{f"{k}_weight": v for k, v in DEFAULT_SCORING.items() if '_' not in k},
            **{f"{k.replace('_', '_')}_bonus" if 'double' in k or 'triple' in k 
               else f"{k}_weight": v for k, v in DEFAULT_SCORING.items() if '_' in k}
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


def update_user_settings(db: Session, user_id: str, scoring_weights: dict, name: str = None) -> FantasySettings:
    """Update user's fantasy settings"""
    settings = get_or_create_user_settings(db, user_id)
    
    # Update name if provided
    if name:
        settings.name = name
    
    # Update scoring weights
    if 'points' in scoring_weights:
        settings.points_weight = float(scoring_weights['points'])
    if 'rebounds' in scoring_weights:
        settings.rebounds_weight = float(scoring_weights['rebounds'])
    if 'assists' in scoring_weights:
        settings.assists_weight = float(scoring_weights['assists'])
    if 'steals' in scoring_weights:
        settings.steals_weight = float(scoring_weights['steals'])
    if 'blocks' in scoring_weights:
        settings.blocks_weight = float(scoring_weights['blocks'])
    if 'turnovers' in scoring_weights:
        settings.turnovers_weight = float(scoring_weights['turnovers'])
    if 'three_pointers' in scoring_weights:
        settings.three_pointers_weight = float(scoring_weights['three_pointers'])
    if 'offensive_rebounds' in scoring_weights:
        settings.offensive_rebounds_weight = float(scoring_weights['offensive_rebounds'])
    if 'field_goals_made' in scoring_weights:
        settings.field_goals_made_weight = float(scoring_weights['field_goals_made'])
    if 'field_goals_missed' in scoring_weights:
        settings.field_goals_missed_weight = float(scoring_weights['field_goals_missed'])
    if 'free_throws_made' in scoring_weights:
        settings.free_throws_made_weight = float(scoring_weights['free_throws_made'])
    if 'free_throws_missed' in scoring_weights:
        settings.free_throws_missed_weight = float(scoring_weights['free_throws_missed'])
    if 'double_double' in scoring_weights:
        settings.double_double_bonus = float(scoring_weights['double_double'])
    if 'triple_double' in scoring_weights:
        settings.triple_double_bonus = float(scoring_weights['triple_double'])
    
    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    
    return settings


def reset_to_default(db: Session, user_id: str) -> FantasySettings:
    """Reset user settings to default"""
    return update_user_settings(db, user_id, DEFAULT_SCORING, "Default Settings")


def calculate_fantasy_points(stats: dict, settings: FantasySettings = None) -> float:
    """
    Calculate fantasy points based on stats and settings
    
    Args:
        stats: Dictionary with keys like 'points', 'rebounds', 'assists', etc.
        settings: FantasySettings object (if None, uses default scoring)
    
    Returns:
        Total fantasy points
    """
    if settings is None:
        weights = DEFAULT_SCORING
    else:
        weights = {
            'points': settings.points_weight,
            'rebounds': settings.rebounds_weight,
            'assists': settings.assists_weight,
            'steals': settings.steals_weight,
            'blocks': settings.blocks_weight,
            'turnovers': settings.turnovers_weight,
            'three_pointers': settings.three_pointers_weight,
            'offensive_rebounds': settings.offensive_rebounds_weight,
            'field_goals_made': settings.field_goals_made_weight,
            'field_goals_missed': settings.field_goals_missed_weight,
            'free_throws_made': settings.free_throws_made_weight,
            'free_throws_missed': settings.free_throws_missed_weight,
            'double_double': settings.double_double_bonus,
            'triple_double': settings.triple_double_bonus
        }
    
    total = 0.0
    
    # Basic stats
    total += stats.get('points', 0) * weights['points']
    total += stats.get('rebounds', 0) * weights['rebounds']
    total += stats.get('assists', 0) * weights['assists']
    total += stats.get('steals', 0) * weights['steals']
    total += stats.get('blocks', 0) * weights['blocks']
    total += stats.get('turnovers', 0) * weights['turnovers']
    
    # Bonus stats
    total += stats.get('three_pm', 0) * weights['three_pointers']
    total += stats.get('oreb', 0) * weights['offensive_rebounds']
    total += stats.get('fgm', 0) * weights['field_goals_made']
    total += stats.get('fga', 0) * weights['field_goals_missed'] - stats.get('fgm', 0) * weights['field_goals_missed']
    total += stats.get('ftm', 0) * weights['free_throws_made']
    total += stats.get('fta', 0) * weights['free_throws_missed'] - stats.get('ftm', 0) * weights['free_throws_missed']
    
    # Double-double and triple-double bonuses
    if weights['double_double'] != 0 or weights['triple_double'] != 0:
        double_digit_stats = sum([
            1 if stats.get('points', 0) >= 10 else 0,
            1 if stats.get('rebounds', 0) >= 10 else 0,
            1 if stats.get('assists', 0) >= 10 else 0,
            1 if stats.get('steals', 0) >= 10 else 0,
            1 if stats.get('blocks', 0) >= 10 else 0
        ])
        
        if double_digit_stats >= 3:
            total += weights['triple_double']
        elif double_digit_stats >= 2:
            total += weights['double_double']
    
    return round(total, 1)


def get_settings_dict(settings: FantasySettings = None) -> dict:
    """Convert settings to dictionary"""
    if settings is None:
        return DEFAULT_SCORING.copy()
    return settings.to_dict()