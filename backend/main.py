from fastapi import FastAPI, HTTPException
from fantasy import calculate_fantasy_points_single_game, calculate_fantasy_points_full_season
from player_calculations import calculate_player_career_stats_regular_season, calculate_averages
from find_player import get_player_id
from projections import (
    project_next_game,
    project_season,
    get_all_projections,
    compare_projection_accuracy
)
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import time

app = FastAPI(title="NBA Fantasy Points API with Projections")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Local dev
        "http://localhost:3000",       # Alternative local port
        "http://localhost",            # Docker frontend
        "http://frontend",             # Docker service name
        "http://127.0.0.1:5173",
        "null"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "API is running"}

@app.get("/fantasy/single")
def fantasy_single(player: str, date: str):
    """Get fantasy points for a single game"""
    try:
        points = calculate_fantasy_points_single_game(player, date)
        if points is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Could not calculate fantasy points for {player} on {date}. Player or game not found."
            )
        return {
            "player_name": player, 
            "game_date": date, 
            "fantasy_points": points
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/fantasy/full")
def fantasy_full_season(player: str):
    """Get fantasy points for all seasons"""
    try:
        df = calculate_fantasy_points_full_season(player)
        if df is None or df.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"Could not calculate fantasy points for {player}. Player not found."
            )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/player/detailed-stats")
def get_detailed_stats(player: str):
    """Get detailed career statistics including all major stats by season"""
    try:
        time.sleep(0.6)
        
        career_stats = calculate_player_career_stats_regular_season(player)
        if career_stats is None or career_stats.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Could not find stats for {player}. Player not found."
            )
        
        df = pd.DataFrame({
            'season': career_stats['SEASON_ID'].astype(str),
            'games_played': pd.to_numeric(career_stats['GP'], errors='coerce'),
            'minutes': pd.to_numeric(career_stats['MIN'], errors='coerce'),
            'points': pd.to_numeric(career_stats['PTS'], errors='coerce'),
            'rebounds': pd.to_numeric(career_stats['REB'], errors='coerce'),
            'assists': pd.to_numeric(career_stats['AST'], errors='coerce'),
            'steals': pd.to_numeric(career_stats['STL'], errors='coerce'),
            'blocks': pd.to_numeric(career_stats['BLK'], errors='coerce'),
            'turnovers': pd.to_numeric(career_stats['TOV'], errors='coerce'),
            'field_goals_made': pd.to_numeric(career_stats['FGM'], errors='coerce'),
            'field_goals_attempted': pd.to_numeric(career_stats['FGA'], errors='coerce'),
            'three_pointers_made': pd.to_numeric(career_stats['FG3M'], errors='coerce'),
            'three_pointers_attempted': pd.to_numeric(career_stats['FG3A'], errors='coerce'),
            'free_throws_made': pd.to_numeric(career_stats['FTM'], errors='coerce'),
            'free_throws_attempted': pd.to_numeric(career_stats['FTA'], errors='coerce'),
            'offensive_rebounds': pd.to_numeric(career_stats['OREB'], errors='coerce'),
            'defensive_rebounds': pd.to_numeric(career_stats['DREB'], errors='coerce'),
            'personal_fouls': pd.to_numeric(career_stats['PF'], errors='coerce'),
        }).fillna(0)
        
        games = df['games_played'].replace(0, 1)
        
        df['mpg'] = (df['minutes'] / games).round(1)
        df['ppg'] = (df['points'] / games).round(1)
        df['rpg'] = (df['rebounds'] / games).round(1)
        df['apg'] = (df['assists'] / games).round(1)
        df['spg'] = (df['steals'] / games).round(1)
        df['bpg'] = (df['blocks'] / games).round(1)
        df['tpg'] = (df['turnovers'] / games).round(1)
        
        df['fg_pct'] = ((df['field_goals_made'] / df['field_goals_attempted'].replace(0, 1)) * 100).round(1)
        df['three_pt_pct'] = ((df['three_pointers_made'] / df['three_pointers_attempted'].replace(0, 1)) * 100).round(1)
        df['ft_pct'] = ((df['free_throws_made'] / df['free_throws_attempted'].replace(0, 1)) * 100).round(1)
        
        df['fantasy_points'] = (
            df['points'] +
            df['rebounds'] +
            df['assists'] * 1.5 +
            df['steals'] * 2 +
            df['blocks'] * 2 -
            df['turnovers'] * 2 +
            df['three_pointers_made'] +
            df['offensive_rebounds'] * 0.5
        )
        
        df['fantasy_ppg'] = (df['fantasy_points'] / games).round(1)
        
        return df.to_dict(orient="records")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/player/career-summary")
def get_career_summary(player: str):
    """Get career totals and averages summary"""
    try:
        time.sleep(0.6)
        
        career_stats = calculate_player_career_stats_regular_season(player)
        if career_stats is None or career_stats.empty:
            raise HTTPException(status_code=404, detail=f"Player {player} not found.")
        
        total_games = career_stats['GP'].sum()
        total_points = career_stats['PTS'].sum()
        total_rebounds = career_stats['REB'].sum()
        total_assists = career_stats['AST'].sum()
        total_steals = career_stats['STL'].sum()
        total_blocks = career_stats['BLK'].sum()
        
        career_ppg = round(total_points / total_games, 1) if total_games > 0 else 0
        career_rpg = round(total_rebounds / total_games, 1) if total_games > 0 else 0
        career_apg = round(total_assists / total_games, 1) if total_games > 0 else 0
        career_spg = round(total_steals / total_games, 1) if total_games > 0 else 0
        career_bpg = round(total_blocks / total_games, 1) if total_games > 0 else 0
        
        seasons_played = len(career_stats)
        
        return {
            "player": player,
            "seasons_played": seasons_played,
            "total_games": int(total_games),
            "career_totals": {
                "points": int(total_points),
                "rebounds": int(total_rebounds),
                "assists": int(total_assists),
                "steals": int(total_steals),
                "blocks": int(total_blocks),
            },
            "career_averages": {
                "ppg": career_ppg,
                "rpg": career_rpg,
                "apg": career_apg,
                "spg": career_spg,
                "bpg": career_bpg,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# ========== PROJECTION ENDPOINTS ==========

@app.get("/projections/next-game")
def get_next_game_projection(player: str, num_recent_games: int = 10, season: str = "2025-26"):
    """
    Project stats for the player's next game based on recent performance
    
    Parameters:
    - player: Player name
    - num_recent_games: Number of recent games to analyze (default: 10)
    - season: Season to analyze (default: 2025-26)
    """
    try:
        projection = project_next_game(player, num_recent_games, season)
        
        if projection is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not generate projection for {player}. Player or recent games not found."
            )
        
        return projection
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/projections/season")
def get_season_projection(player: str, method: str = "recent_seasons"):
    """
    Project full season stats based on various methods
    
    Parameters:
    - player: Player name
    - method: Projection method (career_average, recent_seasons, age_adjusted)
    """
    try:
        if method not in ["career_average", "recent_seasons", "age_adjusted"]:
            raise HTTPException(
                status_code=400,
                detail="Method must be one of: career_average, recent_seasons, age_adjusted"
            )
        
        projection = project_season(player, method=method)
        
        if projection is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not generate projection for {player}. Player not found."
            )
        
        return projection
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/projections/all")
def get_all_player_projections(player: str, season: str = "2025-26"):
    """
    Get comprehensive projections including:
    - Next game projection
    - Season projections (all methods)
    """
    try:
        projections = get_all_projections(player, season)
        
        if projections is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not generate projections for {player}. Player not found."
            )
        
        return projections
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/projections/accuracy")
def get_projection_accuracy(player: str, num_games_back: int = 10, season: str = "2025-26"):
    """
    Test projection accuracy by comparing predictions to actual results
    
    Parameters:
    - player: Player name
    - num_games_back: Number of games to use for validation (default: 10)
    - season: Season to analyze (default: 2025-26)
    """
    try:
        accuracy = compare_projection_accuracy(player, num_games_back, season)
        
        if accuracy is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not calculate accuracy for {player}. Not enough game data."
            )
        
        return accuracy
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/test")
def test():
    return {"message": "API is working!", "timestamp": time.time()}