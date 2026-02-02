"""
NBA Player Projections Module

This module provides various projection methods for NBA players:
1. Season projections based on career trends
2. Game-by-game projections based on recent performance
3. Fantasy points projections
"""

import pandas as pd
import numpy as np
from player_calculations import calculate_player_career_stats_regular_season
from find_player import get_player_id
from nba_api.stats.endpoints import playergamelog
import time
from datetime import datetime

def get_recent_games(player_name, num_games=10, season="2025-26"):
    """
    Get a player's most recent games for short-term projections
    """
    try:
        player_id = get_player_id(player_name)
        if player_id is None:
            return None
        
        time.sleep(0.6)
        game_log = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season
        )
        
        df = game_log.get_data_frames()[0]
        
        if df.empty:
            return None
        
        # Get most recent games
        recent = df.head(num_games)
        
        return pd.DataFrame({
            'game_date': pd.to_datetime(recent['GAME_DATE']),
            'matchup': recent['MATCHUP'],
            'minutes': pd.to_numeric(recent['MIN'], errors='coerce'),
            'points': pd.to_numeric(recent['PTS'], errors='coerce'),
            'rebounds': pd.to_numeric(recent['REB'], errors='coerce'),
            'assists': pd.to_numeric(recent['AST'], errors='coerce'),
            'steals': pd.to_numeric(recent['STL'], errors='coerce'),
            'blocks': pd.to_numeric(recent['BLK'], errors='coerce'),
            'turnovers': pd.to_numeric(recent['TOV'], errors='coerce'),
            'fgm': pd.to_numeric(recent['FGM'], errors='coerce'),
            'fga': pd.to_numeric(recent['FGA'], errors='coerce'),
            'fg3m': pd.to_numeric(recent['FG3M'], errors='coerce'),
            'fg3a': pd.to_numeric(recent['FG3A'], errors='coerce'),
        }).fillna(0)
        
    except Exception as e:
        print(f"Error getting recent games: {e}")
        return None

def calculate_weighted_average(values, weights=None):
    """
    Calculate weighted average giving more weight to recent games
    """
    if weights is None:
        # Exponential decay: most recent game has highest weight
        weights = np.exp(np.linspace(0, 1, len(values)))
    
    if len(values) == 0 or np.sum(weights) == 0:
        return 0
    
    return np.average(values, weights=weights)

def project_next_game(player_name, num_recent_games=10, season="2025-26"):
    """
    Project stats for the player's next game based on recent performance
    Uses weighted average favoring recent games
    """
    try:
        recent_games = get_recent_games(player_name, num_recent_games, season)
        
        if recent_games is None or recent_games.empty:
            return None
        
        # Create exponential weights (more recent = higher weight)
        weights = np.exp(np.linspace(0, 2, len(recent_games)))[::-1]  # Reverse for chronological order
        
        projection = {
            'method': 'weighted_recent_games',
            'games_analyzed': len(recent_games),
            'projected_stats': {
                'minutes': round(calculate_weighted_average(recent_games['minutes'], weights), 1),
                'points': round(calculate_weighted_average(recent_games['points'], weights), 1),
                'rebounds': round(calculate_weighted_average(recent_games['rebounds'], weights), 1),
                'assists': round(calculate_weighted_average(recent_games['assists'], weights), 1),
                'steals': round(calculate_weighted_average(recent_games['steals'], weights), 1),
                'blocks': round(calculate_weighted_average(recent_games['blocks'], weights), 1),
                'turnovers': round(calculate_weighted_average(recent_games['turnovers'], weights), 1),
                'three_pointers_made': round(calculate_weighted_average(recent_games['fg3m'], weights), 1),
            },
            'recent_performance': {
                'last_5_avg': {
                    'points': round(recent_games['points'].head(5).mean(), 1),
                    'rebounds': round(recent_games['rebounds'].head(5).mean(), 1),
                    'assists': round(recent_games['assists'].head(5).mean(), 1),
                },
                'last_10_avg': {
                    'points': round(recent_games['points'].mean(), 1),
                    'rebounds': round(recent_games['rebounds'].mean(), 1),
                    'assists': round(recent_games['assists'].mean(), 1),
                },
                'trend': calculate_trend(recent_games)
            }
        }
        
        # Calculate projected fantasy points
        stats = projection['projected_stats']
        projection['projected_fantasy_points'] = round(
            stats['points'] +
            stats['rebounds'] +
            stats['assists'] * 1.5 +
            stats['steals'] * 2 +
            stats['blocks'] * 2 -
            stats['turnovers'] * 2 +
            stats['three_pointers_made'] +
            0  # OREB not in game log, using 0
        , 1)
        
        return projection
        
    except Exception as e:
        print(f"Error projecting next game: {e}")
        return None

def calculate_trend(recent_games):
    """
    Calculate if player is trending up, down, or stable
    """
    if len(recent_games) < 5:
        return "insufficient_data"
    
    # Compare first half vs second half of recent games
    mid_point = len(recent_games) // 2
    first_half = recent_games.iloc[mid_point:][['points', 'rebounds', 'assists']].mean()
    second_half = recent_games.iloc[:mid_point][['points', 'rebounds', 'assists']].mean()
    
    # Calculate percentage change
    pct_change = ((second_half - first_half) / first_half * 100).mean()
    
    if pct_change > 10:
        return "trending_up"
    elif pct_change < -10:
        return "trending_down"
    else:
        return "stable"

def project_season(player_name, method="career_average"):
    """
    Project full season stats based on various methods
    
    Methods:
    - career_average: Use career averages
    - recent_seasons: Weight recent 3 seasons more heavily
    - age_adjusted: Adjust based on player age and career stage
    """
    try:
        career_stats = calculate_player_career_stats_regular_season(player_name)
        
        if career_stats is None or career_stats.empty:
            return None
        
        # Prepare data
        df = pd.DataFrame({
            'season': career_stats['SEASON_ID'].astype(str),
            'games': pd.to_numeric(career_stats['GP'], errors='coerce'),
            'minutes': pd.to_numeric(career_stats['MIN'], errors='coerce'),
            'points': pd.to_numeric(career_stats['PTS'], errors='coerce'),
            'rebounds': pd.to_numeric(career_stats['REB'], errors='coerce'),
            'assists': pd.to_numeric(career_stats['AST'], errors='coerce'),
            'steals': pd.to_numeric(career_stats['STL'], errors='coerce'),
            'blocks': pd.to_numeric(career_stats['BLK'], errors='coerce'),
            'turnovers': pd.to_numeric(career_stats['TOV'], errors='coerce'),
            'fg3m': pd.to_numeric(career_stats['FG3M'], errors='coerce'),
            'fgm': pd.to_numeric(career_stats['FGM'], errors='coerce'),
            'fga': pd.to_numeric(career_stats['FGA'], errors='coerce'),
        }).fillna(0)
        
        # Calculate per-game stats
        games = df['games'].replace(0, 1)
        df['ppg'] = df['points'] / games
        df['rpg'] = df['rebounds'] / games
        df['apg'] = df['assists'] / games
        df['spg'] = df['steals'] / games
        df['bpg'] = df['blocks'] / games
        df['tpg'] = df['turnovers'] / games
        df['three_pg'] = df['fg3m'] / games
        df['mpg'] = df['minutes'] / games
        
        projection = {
            'method': method,
            'seasons_analyzed': len(df),
        }
        
        if method == "career_average":
            # Simple career average
            projection['projected_per_game'] = {
                'minutes': round(df['mpg'].mean(), 1),
                'points': round(df['ppg'].mean(), 1),
                'rebounds': round(df['rpg'].mean(), 1),
                'assists': round(df['apg'].mean(), 1),
                'steals': round(df['spg'].mean(), 1),
                'blocks': round(df['bpg'].mean(), 1),
                'turnovers': round(df['tpg'].mean(), 1),
                'three_pointers': round(df['three_pg'].mean(), 1),
            }
            
        elif method == "recent_seasons":
            # Weight last 3 seasons more heavily
            recent = df.tail(3)
            weights = np.array([1, 2, 3])[:len(recent)]  # More weight to recent
            
            projection['projected_per_game'] = {
                'minutes': round(np.average(recent['mpg'], weights=weights), 1),
                'points': round(np.average(recent['ppg'], weights=weights), 1),
                'rebounds': round(np.average(recent['rpg'], weights=weights), 1),
                'assists': round(np.average(recent['apg'], weights=weights), 1),
                'steals': round(np.average(recent['spg'], weights=weights), 1),
                'blocks': round(np.average(recent['bpg'], weights=weights), 1),
                'turnovers': round(np.average(recent['tpg'], weights=weights), 1),
                'three_pointers': round(np.average(recent['three_pg'], weights=weights), 1),
            }
            
        elif method == "age_adjusted":
            # Adjust based on career trajectory
            recent = df.tail(3)
            
            # Calculate trend
            if len(df) >= 3:
                recent_avg = recent[['ppg', 'rpg', 'apg']].mean()
                career_avg = df[['ppg', 'rpg', 'apg']].mean()
                
                # If recent performance is declining, adjust down
                adjustment = (recent_avg / career_avg).mean()
                adjustment = min(1.0, max(0.85, adjustment))  # Cap between 85% and 100%
            else:
                adjustment = 1.0
            
            base_projection = {
                'minutes': round(recent['mpg'].mean() * adjustment, 1),
                'points': round(recent['ppg'].mean() * adjustment, 1),
                'rebounds': round(recent['rpg'].mean() * adjustment, 1),
                'assists': round(recent['apg'].mean() * adjustment, 1),
                'steals': round(recent['spg'].mean() * adjustment, 1),
                'blocks': round(recent['bpg'].mean() * adjustment, 1),
                'turnovers': round(recent['tpg'].mean() * adjustment, 1),
                'three_pointers': round(recent['three_pg'].mean() * adjustment, 1),
            }
            
            projection['projected_per_game'] = base_projection
            projection['adjustment_factor'] = round(adjustment, 3)
        
        # Calculate season totals (assuming 82 games)
        ppg = projection['projected_per_game']
        projection['projected_season_totals'] = {
            'games': 82,
            'minutes': round(ppg['minutes'] * 82, 0),
            'points': round(ppg['points'] * 82, 0),
            'rebounds': round(ppg['rebounds'] * 82, 0),
            'assists': round(ppg['assists'] * 82, 0),
            'steals': round(ppg['steals'] * 82, 0),
            'blocks': round(ppg['blocks'] * 82, 0),
            'turnovers': round(ppg['turnovers'] * 82, 0),
            'three_pointers': round(ppg['three_pointers'] * 82, 0),
        }
        
        # Fantasy points
        projection['projected_fantasy_points_per_game'] = round(
            ppg['points'] +
            ppg['rebounds'] +
            ppg['assists'] * 1.5 +
            ppg['steals'] * 2 +
            ppg['blocks'] * 2 -
            ppg['turnovers'] * 2 +
            ppg['three_pointers']
        , 1)
        
        projection['projected_fantasy_points_season'] = round(
            projection['projected_fantasy_points_per_game'] * 82, 1
        )
        
        return projection
        
    except Exception as e:
        print(f"Error projecting season: {e}")
        return None

def get_all_projections(player_name, season="2025-26"):
    """
    Get comprehensive projections including multiple methods
    """
    try:
        projections = {
            'player': player_name,
            'next_game': project_next_game(player_name, num_recent_games=10, season=season),
            'season_projections': {
                'career_average': project_season(player_name, method="career_average"),
                'recent_seasons': project_season(player_name, method="recent_seasons"),
                'age_adjusted': project_season(player_name, method="age_adjusted"),
            }
        }
        
        return projections
        
    except Exception as e:
        print(f"Error getting all projections: {e}")
        return None

def compare_projection_accuracy(player_name, num_games_back=10, season="2025-26"):
    """
    Test projection accuracy by comparing predictions to actual results
    Uses historical data to validate projection methods
    """
    try:
        recent_games = get_recent_games(player_name, num_games_back * 2, season)
        
        if recent_games is None or len(recent_games) < num_games_back * 2:
            return None
        
        # Use first half to project, second half to validate
        training_data = recent_games.iloc[num_games_back:]
        validation_data = recent_games.iloc[:num_games_back]
        
        # Calculate projection based on training data
        weights = np.exp(np.linspace(0, 2, len(training_data)))[::-1]
        
        projected = {
            'points': calculate_weighted_average(training_data['points'], weights),
            'rebounds': calculate_weighted_average(training_data['rebounds'], weights),
            'assists': calculate_weighted_average(training_data['assists'], weights),
        }
        
        # Compare to actual
        actual = {
            'points': validation_data['points'].mean(),
            'rebounds': validation_data['rebounds'].mean(),
            'assists': validation_data['assists'].mean(),
        }
        
        # Calculate accuracy
        accuracy = {}
        for stat in projected:
            error = abs(projected[stat] - actual[stat])
            pct_error = (error / actual[stat] * 100) if actual[stat] > 0 else 0
            accuracy[stat] = {
                'projected': round(projected[stat], 1),
                'actual': round(actual[stat], 1),
                'error': round(error, 1),
                'accuracy': round(100 - pct_error, 1)
            }
        
        return {
            'validation_games': num_games_back,
            'accuracy': accuracy,
            'overall_accuracy': round(np.mean([accuracy[s]['accuracy'] for s in accuracy]), 1)
        }
        
    except Exception as e:
        print(f"Error comparing accuracy: {e}")
        return None