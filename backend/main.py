from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import time

from fantasy import calculate_fantasy_points_single_game, calculate_fantasy_points_full_season
from player_calculations import calculate_player_career_stats_regular_season
from find_player import get_player_id
from projections import project_next_game, project_season, get_all_projections
from advanced_stats import (
    get_game_logs, get_season_averages_with_advanced_stats,
    rank_players_by_projections, get_top_fantasy_players,
    simulate_mock_draft, compare_players, MockDraft
)

# Database imports
from database import get_db, init_db, get_db_info
from database_service import (
    get_or_create_player, get_player_by_name, save_season_stats,
    get_player_seasons, save_projection, get_player_projections,
    log_search, get_popular_players, get_cached_data, set_cached_data,
    get_stats_summary
)

from fantasy_settings_service import (
    get_user_settings,
    update_user_settings,
    reset_to_default,
    get_default_settings,
    calculate_fantasy_points
)
from database_models import FantasySettings
from fantasy_settings_service import (
    get_user_settings,
    calculate_fantasy_points,
    get_default_settings,
    update_user_settings,
    reset_to_default
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
def get_career_summary(player: str, user_id: str = "default", db: Session = Depends(get_db)):
    """Get career summary with custom fantasy scoring"""
    try:
        cache_key = f"career_summary:{player.lower()}:{user_id}"
        cached = get_cached_data(db, cache_key)
        if cached:
            return cached
        
        # Get user's fantasy settings
        from fantasy_settings_service import get_user_settings, calculate_fantasy_points as calc_fantasy
        settings = get_user_settings(db, user_id)
        
        time.sleep(0.6)
        career_stats = calculate_player_career_stats_regular_season(player)
        
        if career_stats is None or career_stats.empty:
            raise HTTPException(status_code=404, detail=f"Player '{player}' not found")
        
        # Calculate career totals
        career_totals = {
            'points': int(career_stats['PTS'].sum()),
            'rebounds': int(career_stats['REB'].sum()),
            'assists': int(career_stats['AST'].sum()),
            'steals': int(career_stats['STL'].sum()),
            'blocks': int(career_stats['BLK'].sum()),
            'games_played': int(career_stats['GP'].sum()),
        }
        
        # Calculate career averages
        total_games = career_stats['GP'].sum()
        career_averages = {
            'ppg': round(career_stats['PTS'].sum() / total_games, 1),
            'rpg': round(career_stats['REB'].sum() / total_games, 1),
            'apg': round(career_stats['AST'].sum() / total_games, 1),
            'spg': round(career_stats['STL'].sum() / total_games, 1),
            'bpg': round(career_stats['BLK'].sum() / total_games, 1),
        }
        
        # Calculate fantasy points with custom settings
        total_fantasy = 0
        for _, season in career_stats.iterrows():
            season_fantasy = calc_fantasy({
                'points': season['PTS'],
                'rebounds': season['REB'],
                'assists': season['AST'],
                'steals': season['STL'],
                'blocks': season['BLK'],
                'turnovers': season['TOV'],
                'three_pm': season['FG3M'],
                'oreb': season['OREB'],
            }, settings)
            total_fantasy += season_fantasy
        
        result = {
            'player_name': player,
            'seasons_played': len(career_stats),
            'career_totals': career_totals,
            'career_averages': career_averages,
            'fantasy_total': round(total_fantasy, 1),
            'fantasy_ppg': round(total_fantasy / total_games, 1)
        }
        
        # Don't cache user-specific data (or use very short TTL)
        ttl = 0 if user_id != "default" else 360
        set_cached_data(db, cache_key, result, ttl_minutes=ttl)
                
        # Log search
        nba_id = get_player_id(player)
        if nba_id:
            db_player = get_or_create_player(db, nba_id, player)
            log_search(db, db_player.id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    
@app.get("/player/detailed-stats")
def get_detailed_stats(player: str, user_id: str = "default", db: Session = Depends(get_db)):
    """Get detailed career statistics with database caching and custom fantasy scoring"""
    try:
        # Include user_id in cache key
        cache_key = f"detailed_stats:{player.lower()}:{user_id}"
        cached = get_cached_data(db, cache_key)
        if cached:
            print(f"✅ Cache hit for {player} detailed stats")
            return cached
        
        time.sleep(0.6)  # rate-limit guard only when we're about to hit the NBA API
        
        # Get user's fantasy settings
        from fantasy_settings_service import get_user_settings, calculate_fantasy_points as calc_fantasy
        settings = get_user_settings(db, user_id)
        
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
        
        # Calculate fantasy points per game using custom settings
        df['fantasy_ppg'] = df.apply(lambda row: calc_fantasy({
            'points': row['ppg'],
            'rebounds': row['rpg'],
            'assists': row['apg'],
            'steals': row['spg'],
            'blocks': row['bpg'],
            'turnovers': row['tpg'],
            'three_pm': row['three_pointers_made'] / games.loc[row.name],
            'oreb': row['offensive_rebounds'] / games.loc[row.name],
            'fgm': row['field_goals_made'] / games.loc[row.name],
            'fga': row['field_goals_attempted'] / games.loc[row.name],
        }, settings), axis=1)
        
        df['fantasy_points'] = df['fantasy_ppg'] * games
        
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
        
        # Don't cache user-specific data (or use very short TTL)
        ttl = 0 if user_id != "default" else 360
        set_cached_data(db, cache_key, result, ttl_minutes=ttl)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

def _to_native(v):
    """Convert np.float64 / np.int64 → plain Python float/int. No-op on everything else."""
    return v.item() if hasattr(v, 'item') else v


# ==================== PROJECTION ENDPOINTS ====================

@app.get("/projections/all")
def get_all_player_projections(player: str, season: str = "2025-26", 
                               user_id: str = "default", db: Session = Depends(get_db)):
    """Get comprehensive projections with custom fantasy scoring"""
    try:
        print(f"🔮 Getting projections for {player}, season {season}, user {user_id}")
        
        cache_key = f"projections:{player.lower()}:{season}:{user_id}"
        cached = get_cached_data(db, cache_key)
        if cached:
            print(f"✅ Cache hit for {player} projections")
            return cached
        
        # Get user's fantasy settings
        from fantasy_settings_service import get_user_settings, calculate_fantasy_points as calc_fantasy
        settings = get_user_settings(db, user_id)
        print(f"📊 Using fantasy settings: {settings.to_dict() if settings else 'default'}")
        
        # Get projections from NBA API
        print(f"📡 Fetching projections from NBA API...")
        # Get projections from NBA API
        projections = get_all_projections(player, season)
        
        print(f"✅ Got projections, recalculating fantasy points...")
        # Recalculate fantasy points with custom settings
        if projections.get('next_game') and projections['next_game'].get('projected_stats'):
            proj = projections['next_game']['projected_stats']
            projections['next_game']['projected_fantasy_points'] = calc_fantasy({
                'points': proj.get('points', 0),
                'rebounds': proj.get('rebounds', 0),
                'assists': proj.get('assists', 0),
                'steals': proj.get('steals', 0),
                'blocks': proj.get('blocks', 0),
                'turnovers': proj.get('turnovers', 0),
                'three_pm': proj.get('three_pointers', 0),
            }, settings)
            print(f"✅ Next game fantasy: {projections['next_game']['projected_fantasy_points']}")
        
        # Update season projections
        if projections.get('season_projections'):
            for method, proj_data in projections['season_projections'].items():
                if proj_data and proj_data.get('projected_per_game'):
                    stats = proj_data['projected_per_game']
                    proj_data['projected_fantasy_points_per_game'] = calc_fantasy({
                        'points': stats.get('points', 0),
                        'rebounds': stats.get('rebounds', 0),
                        'assists': stats.get('assists', 0),
                        'steals': stats.get('steals', 0),
                        'blocks': stats.get('blocks', 0),
                        'turnovers': stats.get('turnovers', 0),
                        'three_pm': stats.get('three_pointers', 0),
                    }, settings)
                    proj_data['projected_fantasy_points_season'] = proj_data['projected_fantasy_points_per_game'] * 82
        
        print(f"✅ Caching projections...")
        set_cached_data(db, cache_key, projections, ttl_minutes=30)
        
        print(f"✅ Returning projections for {player}")
        return projections
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in projections endpoint: {e}")
        # Return a basic structure so the tab doesn't break
        projections = {
            'next_game': {
                'projected_stats': {
                    'points': 0,
                    'rebounds': 0,
                    'assists': 0,
                    'steals': 0,
                    'blocks': 0,
                    'turnovers': 0,
                    'three_pointers': 0
                },
                'projected_fantasy_points': 0,
                'method': 'error',
                'error': str(e)
            },
            'season_projections': {}
        }
        import traceback
        traceback.print_exc()
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

# ==================== GAME LOGS & ADVANCED STATS ====================

@app.get("/player/game-logs")
def get_player_game_logs(player: str, season: str = "2025-26", last_n: int = None, 
                         user_id: str = "default", db: Session = Depends(get_db)):
    """Get detailed game logs with advanced stats (3P%, PER, etc.) using custom fantasy scoring"""
    try:
        # Include user_id in cache key so different users get different fantasy scores
        cache_key = f"game_logs:{player.lower()}:{season}:{last_n or 'all'}:{user_id}"
        cached = get_cached_data(db, cache_key)
        if cached:
            return cached
        
        # Get user's fantasy settings
        from fantasy_settings_service import get_user_settings, calculate_fantasy_points as calc_fantasy
        settings = get_user_settings(db, user_id)
        
        # Get game logs from NBA API
        logs = get_game_logs(player, season, last_n)
        
        if logs is None or logs.empty:
            raise HTTPException(status_code=404, detail=f"No game logs found for {player} in {season}")
        
        result = logs.to_dict(orient="records")
        
        # Recalculate fantasy points with user's custom settings
        for game in result:
            game['fantasy_points'] = calc_fantasy({
                'points': game.get('points', 0),
                'rebounds': game.get('rebounds', 0),
                'assists': game.get('assists', 0),
                'steals': game.get('steals', 0),
                'blocks': game.get('blocks', 0),
                'turnovers': game.get('turnovers', 0),
                'three_pm': game.get('three_pm', 0),
                'oreb': game.get('oreb', 0),
                'fgm': game.get('fgm', 0),
                'fga': game.get('fga', 0),
                'ftm': game.get('ftm', 0),
                'fta': game.get('fta', 0)
            }, settings)
        
        # Don't cache user-specific data (or use very short TTL)
        ttl = 0 if user_id != "default" else 360
        set_cached_data(db, cache_key, result, ttl_minutes=ttl)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/player/season-advanced")
def get_player_season_advanced(player: str, season: str = "2025-26", 
                               user_id: str = "default", db: Session = Depends(get_db)):
    """Get season averages with advanced stats (PER, 3P%, etc.) using custom fantasy scoring"""
    try:
        # Include user_id in cache key
        cache_key = f"season_advanced:{player.lower()}:{season}:{user_id}"
        cached = get_cached_data(db, cache_key)
        if cached:
            return cached
        
        # Get user's fantasy settings
        from fantasy_settings_service import get_user_settings, calculate_fantasy_points as calc_fantasy
        settings = get_user_settings(db, user_id)
        
        # Get season averages from NBA API
        stats = get_season_averages_with_advanced_stats(player, season)
        
        if stats is None:
            raise HTTPException(status_code=404, detail=f"No stats found for {player} in {season}")
        
        # Recalculate fantasy points average with user's custom settings
        stats['fantasy_points'] = calc_fantasy({
            'points': stats.get('points', 0),
            'rebounds': stats.get('rebounds', 0),
            'assists': stats.get('assists', 0),
            'steals': stats.get('steals', 0),
            'blocks': stats.get('blocks', 0),
            'turnovers': stats.get('turnovers', 0),
            'three_pm': stats.get('three_pm', 0),
            'oreb': stats.get('oreb', 0),
            'fgm': stats.get('fgm', 0),
            'fga': stats.get('fga', 0),
            'ftm': stats.get('ftm', 0),
            'fta': stats.get('fta', 0)
        }, settings)
        
        # Recalculate total fantasy for the season
        if 'games_played' in stats:
            stats['total_fantasy'] = stats['fantasy_points'] * stats['games_played']
        
        # Don't cache user-specific data (or use very short TTL)
        ttl = 0 if user_id != "default" else 360
        set_cached_data(db, cache_key, result, ttl_minutes=ttl)
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# ==================== FANTASY RANKINGS ====================

@app.post("/rankings/players")
def rank_players(player_list: dict, season: str = "2025-26", db: Session = Depends(get_db)):
    """
    Rank multiple players by fantasy projections
    Body: {"players": ["LeBron James", "Stephen Curry", ...]}
    """
    try:
        players = player_list.get("players", [])
        if not players:
            raise HTTPException(status_code=400, detail="Must provide list of players")
        
        # Check cache for this exact player list
        cache_key = f"rankings:{'_'.join(sorted([p.lower().replace(' ', '') for p in players]))}:{season}"
        cached = get_cached_data(db, cache_key)
        if cached:
            return cached
        
        rankings = rank_players_by_projections(players, season)
        
        # Cache for 1 hour
        set_cached_data(db, cache_key, rankings, ttl_minutes=60)
        
        return {"rankings": rankings}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/rankings/top")
def get_top_rankings(position: str = None, limit: int = 50, season: str = "2025-26",
                     user_id: str = "default", db: Session = Depends(get_db)):
    """
    Get top fantasy players with custom scoring, optionally filtered by position
    Position: PG, SG, SF, PF, C (optional)
    """
    try:
        # Get user's fantasy settings
        from fantasy_settings_service import get_user_settings
        settings = get_user_settings(db, user_id)
        
        # Get rankings (this function will need to be updated to accept settings)
        rankings = get_top_fantasy_players(position, limit, season, settings)
        
        return {"rankings": rankings, "position": position, "season": season}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# ==================== MOCK DRAFT ====================

@app.post("/draft/simulate")
def simulate_draft(draft_config: dict):
    """
    Simulate a mock draft
    Body: {
        "players": ["Player1", "Player2", ...],  # Players to rank and draft
        "num_teams": 12,
        "rounds": 15,
        "season": "2025-26"
    }
    """
    try:
        players = draft_config.get("players", [])
        num_teams = draft_config.get("num_teams", 12)
        rounds = draft_config.get("rounds", 15)
        season = draft_config.get("season", "2025-26")
        
        if not players:
            raise HTTPException(status_code=400, detail="Must provide list of players to draft from")
        
        # First rank the players
        rankings = rank_players_by_projections(players, season)
        
        # Simulate the draft
        draft_results = simulate_mock_draft(rankings, num_teams, rounds)
        
        return draft_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# ==================== PLAYER COMPARISON ====================

@app.post("/compare")
def compare_multiple_players(player_list: dict, season: str = "2025-26", 
                             user_id: str = "default", db: Session = Depends(get_db)):
    """
    Compare multiple players side-by-side with custom fantasy scoring
    Body: {"players": ["Player1", "Player2", ...]}
    """
    try:
        players = player_list.get("players", [])
        if not players:
            raise HTTPException(status_code=400, detail="Must provide list of players to compare")
        
        # Include user_id in cache key
        cache_key = f"compare:{'_'.join(sorted([p.lower().replace(' ', '') for p in players]))}:{season}:{user_id}"
        cached = get_cached_data(db, cache_key)
        if cached:
            return cached
        
        # Get user's fantasy settings
        from fantasy_settings_service import get_user_settings
        settings = get_user_settings(db, user_id)
        
        # Compare with custom settings
        comparison = compare_players(players, season, settings)
        
        # Don't cache user-specific data (or use very short TTL)
        ttl = 0 if user_id != "default" else 360
        set_cached_data(db, cache_key, result, ttl_minutes=ttl)
        
        return comparison
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    
# ==================== FANTASY SETTINGS ====================

@app.get("/fantasy/settings")
def get_fantasy_settings(user_id: str = "default", db: Session = Depends(get_db)):
    """
    Get user's fantasy scoring settings
    If no custom settings exist, returns default
    """
    try:
        settings = get_user_settings(db, user_id)
        
        if settings:
            return settings.to_dict()
        else:
            # Return default settings
            return {
                "user_id": user_id,
                "name": "Default Settings",
                "is_default": True,
                **get_default_settings()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/fantasy/settings")
def save_fantasy_settings(settings_data: dict, user_id: str = "default", db: Session = Depends(get_db)):
    """Save user's fantasy scoring settings and FORCE clear all related cache"""
    try:
        from database_models import CachedData
        
        name = settings_data.pop('name', 'Custom Settings')
        
        # Save the new settings
        settings = update_user_settings(db, user_id, settings_data, name)
        
        # AGGRESSIVE CACHE CLEARING
        # Clear ALL cache entries (not just user-specific)
        # This ensures no stale data remains
        try:
            total_count = db.query(CachedData).count()
            print(f"🗑️ Cache before clear: {total_count} entries")
            db.query(CachedData).delete()
            db.commit()
            print(f"🗑️ Cache after clear: {db.query(CachedData).count()} entries")  # Should be 0
            print(f"✅ FORCE CLEARED ALL {total_count} cache entries after settings change")
        except Exception as cache_err:
            print(f"⚠️ Cache clear error: {cache_err}")
            db.rollback()
            # Continue anyway - settings are saved
        
        return {
            **settings.to_dict(),
            "cache_cleared": True,
            "message": "Settings saved and cache cleared"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/fantasy/settings/reset")
def reset_fantasy_settings(user_id: str = "default", db: Session = Depends(get_db)):
    """Reset user's fantasy settings to default"""
    try:
        settings = reset_to_default(db, user_id)
        return settings.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/fantasy/settings/presets")
def get_fantasy_presets():
    """
    Get common fantasy scoring presets
    """
    return {
        "standard": {
            "name": "Standard",
            "points": 1.0,
            "rebounds": 1.0,
            "assists": 1.5,
            "steals": 2.0,
            "blocks": 2.0,
            "turnovers": -2.0,
            "three_pointers": 1.0,
            "offensive_rebounds": 0.5
        },
        "points_heavy": {
            "name": "Points Heavy",
            "points": 1.5,
            "rebounds": 1.0,
            "assists": 1.0,
            "steals": 2.0,
            "blocks": 2.0,
            "turnovers": -1.0,
            "three_pointers": 1.5,
            "offensive_rebounds": 0.0
        },
        "balanced": {
            "name": "Balanced",
            "points": 1.0,
            "rebounds": 1.2,
            "assists": 1.5,
            "steals": 3.0,
            "blocks": 3.0,
            "turnovers": -2.0,
            "three_pointers": 1.0,
            "offensive_rebounds": 1.0
        },
        "category_based": {
            "name": "9-Cat Style",
            "points": 1.0,
            "rebounds": 1.0,
            "assists": 1.0,
            "steals": 1.0,
            "blocks": 1.0,
            "turnovers": -1.0,
            "three_pointers": 1.0,
            "field_goals_made": 1.0,
            "field_goals_missed": -1.0,
            "free_throws_made": 1.0,
            "free_throws_missed": -1.0
        }
    }


# ==================== ADMIN ENDPOINTS ====================

@app.post("/admin/clear-cache")
def clear_all_cache(db: Session = Depends(get_db)):
    """Clear all cached data - use after changing fantasy settings"""
    try:
        from database_models import CachedData
        
        # Delete all cache entries
        count = db.query(CachedData).delete()
        db.commit()
        
        return {
            "message": f"Successfully cleared {count} cache entries",
            "cleared": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.delete("/admin/clear-user-cache/{user_id}")
def clear_user_cache(user_id: str, db: Session = Depends(get_db)):
    """Clear cache for specific user only"""
    try:
        from database_models import CachedData
        
        # Delete cache entries containing this user_id
        count = db.query(CachedData).filter(
            CachedData.cache_key.like(f'%:{user_id}')
        ).delete(synchronize_session=False)
        db.commit()
        
        return {
            "message": f"Cleared {count} cache entries for user {user_id}",
            "user_id": user_id,
            "cleared": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear user cache: {str(e)}")