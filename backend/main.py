from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import time

from fantasy import calculate_fantasy_points_single_game, calculate_fantasy_points_full_season
from player_calculations import calculate_player_career_stats_regular_season
from find_player import get_player_id
from projections import project_next_game, project_season, get_all_projections

# Database imports
from database import get_db, init_db, get_db_info
from database_service import (
    get_or_create_player, get_player_by_name, save_season_stats,
    get_player_seasons, save_projection, get_player_projections,
    log_search, get_popular_players, get_cached_data, set_cached_data,
    get_stats_summary
)

app = FastAPI(title="NBA Fantasy Points API with Database")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost",
        "http://127.0.0.1:5173",
        "http://frontend",
        "null"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    print("🚀 Starting up...")
    init_db()
    print("📊 Database initialized")

@app.get("/")
def health():
    return {"status": "API is running", "database": "connected"}

@app.get("/db/info")
def database_info():
    """Get database connection info"""
    return get_db_info()

@app.get("/db/stats")
def database_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    return get_stats_summary(db)

# ==================== PLAYER ENDPOINTS ====================

@app.get("/player/career-summary")
def get_career_summary(player: str, db: Session = Depends(get_db), request: Request = None):
    """Get career totals and averages with database caching"""
    try:
        time.sleep(0.6)
        
        # Check cache first
        cache_key = f"career_summary:{player.lower()}"
        cached = get_cached_data(db, cache_key)
        if cached:
            print(f"✅ Cache hit for {player}")
            return cached
        
        # Get from NBA API
        career_stats = calculate_player_career_stats_regular_season(player)
        if career_stats is None or career_stats.empty:
            raise HTTPException(status_code=404, detail=f"Player {player} not found.")
        
        # Calculate summary
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
        
        result = {
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
        
        # Save to database
        nba_id = get_player_id(player)
        if nba_id:
            db_player = get_or_create_player(db, nba_id, player)
            # Log search
            client_ip = request.client.host if request else None
            user_agent = request.headers.get("user-agent") if request else None
            log_search(db, db_player.id, client_ip, user_agent)
        
        # Cache for 1 hour
        set_cached_data(db, cache_key, result, ttl_minutes=60)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/player/detailed-stats")
def get_detailed_stats(player: str, db: Session = Depends(get_db)):
    """Get detailed career statistics with database caching"""
    try:
        time.sleep(0.6)
        
        # Check cache
        cache_key = f"detailed_stats:{player.lower()}"
        cached = get_cached_data(db, cache_key)
        if cached:
            print(f"✅ Cache hit for {player} detailed stats")
            return cached
        
        career_stats = calculate_player_career_stats_regular_season(player)
        if career_stats is None or career_stats.empty:
            raise HTTPException(status_code=404, detail=f"Could not find stats for {player}")
        
        # Process stats (same as before)
        import pandas as pd
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
            'offensive_rebounds': pd.to_numeric(career_stats['OREB'], errors='coerce'),
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
        
        df['fantasy_points'] = (
            df['points'] + df['rebounds'] + df['assists'] * 1.5 +
            df['steals'] * 2 + df['blocks'] * 2 - df['turnovers'] * 2 +
            df['three_pointers_made'] + df['offensive_rebounds'] * 0.5
        )
        
        df['fantasy_ppg'] = (df['fantasy_points'] / games).round(1)
        
        result = df.to_dict(orient="records")
        
        # Save to database
        nba_id = get_player_id(player)
        if nba_id:
            db_player = get_or_create_player(db, nba_id, player)
            # Save each season's stats
            for season_data in result:
                save_season_stats(db, db_player.id, season_data['season'], {
                    'games_played': int(season_data['games_played']),
                    'minutes_per_game': float(season_data['mpg']),
                    'points_per_game': float(season_data['ppg']),
                    'rebounds_per_game': float(season_data['rpg']),
                    'assists_per_game': float(season_data['apg']),
                    'steals_per_game': float(season_data['spg']),
                    'blocks_per_game': float(season_data['bpg']),
                    'turnovers_per_game': float(season_data['tpg']),
                    'field_goal_percentage': float(season_data['fg_pct']),
                    'three_point_percentage': float(season_data['three_pt_pct']),
                    'fantasy_points_per_game': float(season_data['fantasy_ppg']),
                    'fantasy_points_total': float(season_data['fantasy_points']),
                })
        
        # Cache for 1 hour
        set_cached_data(db, cache_key, result, ttl_minutes=60)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# ==================== PROJECTION ENDPOINTS ====================

@app.get("/projections/all")
def get_all_player_projections(player: str, season: str = "2025-26", db: Session = Depends(get_db)):
    """Get comprehensive projections with database caching"""
    try:
        # Check cache first
        cache_key = f"projections:{player.lower()}:{season}"
        cached = get_cached_data(db, cache_key)
        if cached:
            print(f"✅ Cache hit for {player} projections")
            return cached
        
        projections = get_all_projections(player, season)
        
        if projections is None:
            raise HTTPException(status_code=404, detail=f"Could not generate projections for {player}")
        
        # Save to database
        nba_id = get_player_id(player)
        if nba_id and projections:
            db_player = get_or_create_player(db, nba_id, player)
            
            # Save next game projection
            if projections.get('next_game'):
                ng = projections['next_game']
                if ng.get('projected_stats'):
                    save_projection(db, db_player.id, season, 'next_game', {
                        'projected_points_per_game': ng['projected_stats'].get('points', 0),
                        'projected_rebounds_per_game': ng['projected_stats'].get('rebounds', 0),
                        'projected_assists_per_game': ng['projected_stats'].get('assists', 0),
                        'projected_fantasy_points_per_game': ng.get('projected_fantasy_points', 0),
                        'trend': ng.get('recent_performance', {}).get('trend'),
                        'method': ng.get('method')
                    })
            
            # Save season projections
            if projections.get('season_projections'):
                for method, data in projections['season_projections'].items():
                    if data:
                        save_projection(db, db_player.id, season, f'season_{method}', {
                            'projected_games': 82,
                            'projected_points_per_game': data['projected_per_game'].get('points', 0),
                            'projected_rebounds_per_game': data['projected_per_game'].get('rebounds', 0),
                            'projected_assists_per_game': data['projected_per_game'].get('assists', 0),
                            'projected_fantasy_points_per_game': data.get('projected_fantasy_points_per_game', 0),
                            'projected_fantasy_points_season': data.get('projected_fantasy_points_season', 0),
                            'method': method
                        })
        
        # Cache for 30 minutes (projections change more frequently)
        set_cached_data(db, cache_key, projections, ttl_minutes=30)
        
        return projections
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/analytics/popular-players")
def popular_players(limit: int = 10, db: Session = Depends(get_db)):
    """Get most searched players"""
    popular = get_popular_players(db, limit=limit)
    return [
        {
            "player_name": player.full_name,
            "nba_id": player.nba_id,
            "search_count": count
        }
        for player, count in popular
    ]

@app.get("/test")
def test():
    return {"message": "API with Database is working!", "timestamp": time.time()}