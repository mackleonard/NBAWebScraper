"""
Advanced NBA Statistics Module

Provides:
1. Detailed game logs with advanced stats (3P%, 3PM, PER)
2. Fantasy rankings system
3. Mock draft utilities
"""

import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playergamelog, commonplayerinfo, leaguedashplayerstats
from find_player import get_player_id
from projections import get_all_projections
import time
from typing import List, Dict, Optional
from fantasy_settings_service import calculate_fantasy_points as calc_fantasy



# ---------------------------------------------------------------------------
# Type conversion helper - ensures all values are JSON-serializable
# ---------------------------------------------------------------------------
def _to_native_types(df):
    """
    Convert pandas DataFrame with numpy types to native Python types for JSON serialization.
    Handles: np.int64 → int, np.float64 → float, Timestamp → str
    """
    for col in df.columns:
        if df[col].dtype == 'object':
            continue  # Skip string columns
        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype(int)
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype(float)
    return df


# ---------------------------------------------------------------------------
# GAME LOGS WITH ADVANCED STATS
# ---------------------------------------------------------------------------

def calculate_per(stats: dict) -> float:
    """
    Calculate Player Efficiency Rating (PER) for a game
    Simplified formula: (PTS + REB + AST + STL + BLK - TO - (FGA-FGM) - (FTA-FTM)) / MIN
    
    Full PER is more complex and requires league averages, but this gives a good approximation.
    """
    try:
        minutes = stats.get('MIN', 0)
        if minutes == 0:
            return 0.0
        
        points = stats.get('PTS', 0)
        rebounds = stats.get('REB', 0)
        assists = stats.get('AST', 0)
        steals = stats.get('STL', 0)
        blocks = stats.get('BLK', 0)
        turnovers = stats.get('TOV', 0)
        fgm = stats.get('FGM', 0)
        fga = stats.get('FGA', 0)
        ftm = stats.get('FTM', 0)
        fta = stats.get('FTA', 0)
        
        # Positive contributions
        positive = points + rebounds + assists + steals + blocks
        
        # Negative contributions
        negative = turnovers + (fga - fgm) + (fta - ftm)
        
        # PER per minute, scaled to reasonable numbers
        per = ((positive - negative) / minutes) * 10
        
        return round(per, 1)
    except:
        return 0.0


def get_game_logs(player_name: str, season: str = "2025-26", last_n_games: int = None, 
                  fantasy_settings=None) -> Optional[pd.DataFrame]:
    """
    Get detailed game logs with advanced stats including 3P%, 3PM, PER
    
    Args:
        player_name: Full name of player
        season: NBA season (e.g., "2025-26")
        last_n_games: If specified, return only the last N games
    
    Returns:
        DataFrame with columns: date, opponent, result, minutes, points, rebounds, 
        assists, steals, blocks, turnovers, fgm, fga, fg_pct, three_pm, three_pa, 
        three_pct, ftm, fta, ft_pct, plus_minus, fantasy_points, per
    """
    try:
        player_id = get_player_id(player_name)
        if player_id is None:
            print(f"Player '{player_name}' not found")
            return None
        
        time.sleep(0.6)
        game_log = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season
        )
        
        df = game_log.get_data_frames()[0]
        
        if df.empty:
            return None
        
        # Limit to last N games if specified
        if last_n_games:
            df = df.head(last_n_games)
        
        # Process and calculate advanced stats
        processed = pd.DataFrame({
            'date': pd.to_datetime(df['GAME_DATE']).dt.strftime('%Y-%m-%d'),  # Convert to string for JSON
            'opponent': df['MATCHUP'],
            'result': df['WL'],
            'minutes': pd.to_numeric(df['MIN'], errors='coerce'),
            'points': pd.to_numeric(df['PTS'], errors='coerce'),
            'rebounds': pd.to_numeric(df['REB'], errors='coerce'),
            'assists': pd.to_numeric(df['AST'], errors='coerce'),
            'steals': pd.to_numeric(df['STL'], errors='coerce'),
            'blocks': pd.to_numeric(df['BLK'], errors='coerce'),
            'turnovers': pd.to_numeric(df['TOV'], errors='coerce'),
            'fgm': pd.to_numeric(df['FGM'], errors='coerce'),
            'fga': pd.to_numeric(df['FGA'], errors='coerce'),
            'three_pm': pd.to_numeric(df['FG3M'], errors='coerce'),
            'three_pa': pd.to_numeric(df['FG3A'], errors='coerce'),
            'ftm': pd.to_numeric(df['FTM'], errors='coerce'),
            'fta': pd.to_numeric(df['FTA'], errors='coerce'),
            'oreb': pd.to_numeric(df['OREB'], errors='coerce'),
            'plus_minus': pd.to_numeric(df['PLUS_MINUS'], errors='coerce'),
        }).fillna(0)
        
        # Calculate percentages
        processed['fg_pct'] = ((processed['fgm'] / processed['fga'].replace(0, 1)) * 100).round(1)
        processed['three_pct'] = ((processed['three_pm'] / processed['three_pa'].replace(0, 1)) * 100).round(1)
        processed['ft_pct'] = ((processed['ftm'] / processed['fta'].replace(0, 1)) * 100).round(1)
        
        # Calculate fantasy points (standard scoring)
        processed['fantasy_points'] = processed.apply(
        lambda row: calc_fantasy({
            'points': row['points'],
            'rebounds': row['rebounds'],
            'assists': row['assists'],
            'steals': row['steals'],
            'blocks': row['blocks'],
            'turnovers': row['turnovers'],
            'three_pm': row['three_pm'],
            'oreb': row.get('oreb', 0),
            'fgm': row.get('fgm', 0),
            'fga': row.get('fga', 0),
            'ftm': row.get('ftm', 0),
            'fta': row.get('fta', 0)
    }, fantasy_settings),
    axis=1
)
        
        # Calculate PER for each game
        processed['per'] = processed.apply(
            lambda row: calculate_per({
                'MIN': row['minutes'],
                'PTS': row['points'],
                'REB': row['rebounds'],
                'AST': row['assists'],
                'STL': row['steals'],
                'BLK': row['blocks'],
                'TOV': row['turnovers'],
                'FGM': row['fgm'],
                'FGA': row['fga'],
                'FTM': row['ftm'],
                'FTA': row['fta']
            }),
            axis=1
        )
        
        # Convert all numpy types to native Python types for JSON serialization
        processed = _to_native_types(processed)
        
        return processed
        
    except Exception as e:
        print(f"Error getting game logs: {e}")
        return None


def get_season_averages_with_advanced_stats(player_name: str, season: str = "2025-26") -> Optional[dict]:
    """
    Get season averages including ALL stats (basic + advanced)
    """
    game_logs = get_game_logs(player_name, season)
    
    if game_logs is None or game_logs.empty:
        return None
    
    games_played = len(game_logs)
    
    # Helper to ensure native float type
    def to_float(val):
        return float(round(val, 1)) if pd.notna(val) else 0.0
    
    # Calculate win percentage
    wins = len(game_logs[game_logs['result'] == 'W']) if 'result' in game_logs.columns else 0
    win_pct = to_float((wins / games_played * 100)) if games_played > 0 else 0.0
    
    return {
        # Basic info
        'games_played': int(games_played),
        'wins': int(wins),
        'win_pct': win_pct,
        
        # Per-game averages
        'minutes': to_float(game_logs['minutes'].mean()),
        'points': to_float(game_logs['points'].mean()),
        'rebounds': to_float(game_logs['rebounds'].mean()),
        'assists': to_float(game_logs['assists'].mean()),
        'steals': to_float(game_logs['steals'].mean()),
        'blocks': to_float(game_logs['blocks'].mean()),
        'turnovers': to_float(game_logs['turnovers'].mean()),
        
        # Shooting stats
        'fgm': to_float(game_logs['fgm'].mean()),
        'fga': to_float(game_logs['fga'].mean()),
        'fg_pct': to_float(game_logs['fg_pct'].mean()),
        'three_pm': to_float(game_logs['three_pm'].mean()),
        'three_pa': to_float(game_logs['three_pa'].mean()),
        'three_pct': to_float(game_logs['three_pct'].mean()),
        'ftm': to_float(game_logs['ftm'].mean()),
        'fta': to_float(game_logs['fta'].mean()),
        'ft_pct': to_float(game_logs['ft_pct'].mean()),
        
        # Additional stats
        'oreb': to_float(game_logs['oreb'].mean()) if 'oreb' in game_logs.columns else 0.0,
        'plus_minus': to_float(game_logs['plus_minus'].mean()),
        
        # Advanced/Fantasy
        'fantasy_points': to_float(game_logs['fantasy_points'].mean()),
        'per': to_float(game_logs['per'].mean()),
        
        # Season totals
        'total_points': to_float(game_logs['points'].sum()),
        'total_rebounds': to_float(game_logs['rebounds'].sum()),
        'total_assists': to_float(game_logs['assists'].sum()),
        'total_fantasy': to_float(game_logs['fantasy_points'].sum())
    }


# ---------------------------------------------------------------------------
# FANTASY RANKINGS SYSTEM
# ---------------------------------------------------------------------------

def rank_players_by_projections(player_names: List[str], season: str = "2025-26", fantasy_settings=None) -> List[dict]:
    """
    Rank multiple players by their projected fantasy points
    
    Args:
        player_names: List of player names to rank
        season: Season for projections
    
    Returns:
        List of dicts with player info and rankings, sorted by projected fantasy points
    """
    rankings = []
    
    for name in player_names:
        try:
            # Get projections
            projections = get_all_projections(name, season)
            
            if projections is None:
                continue
            
            # Use recent_seasons method as primary ranking metric
            season_proj = projections.get('season_projections', {}).get('recent_seasons')
            
            if season_proj:
                fantasy_ppg = season_proj.get('projected_fantasy_points_per_game', 0)
                fantasy_season = season_proj.get('projected_fantasy_points_season', 0)
                
                # Get next game projection for trend
                next_game = projections.get('next_game', {})
                trend = next_game.get('recent_performance', {}).get('trend', 'stable') if next_game else 'stable'
                
                rankings.append({
                    'player': name,
                    'fantasy_ppg': fantasy_ppg,
                    'fantasy_season_total': fantasy_season,
                    'projected_points': season_proj['projected_per_game'].get('points', 0),
                    'projected_rebounds': season_proj['projected_per_game'].get('rebounds', 0),
                    'projected_assists': season_proj['projected_per_game'].get('assists', 0),
                    'trend': trend
                })
            
            # Rate limit between API calls
            time.sleep(0.7)
            
        except Exception as e:
            print(f"Error ranking {name}: {e}")
            continue
    
    # Sort by fantasy points per game (descending)
    rankings.sort(key=lambda x: x['fantasy_ppg'], reverse=True)
    
    # Add rank numbers
    for i, player in enumerate(rankings, 1):
        player['rank'] = i
    
    return rankings


def get_top_fantasy_players(position: str = None, limit: int = 50, season: str = "2025-26", fantasy_settings=None) -> List[dict]:
    """
    Get top fantasy players with custom scoring
    """
    from fantasy_settings_service import calculate_fantasy_points as calc_fantasy
    
    pos_map = {'G': 'G', 'F': 'F', 'C': 'C', 'ALL': None}
    api_pos = pos_map.get(position.upper()) if position else None

    stats_req = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        per_mode_detailed='PerGame',
        player_position_abbreviation_nullable=api_pos
    )
    df = stats_req.get_data_frames()[0]

    # Calculate fantasy points using custom settings
    df['fantasy_ppg'] = df.apply(lambda row: calc_fantasy({
        'points': row['PTS'],
        'rebounds': row['REB'],
        'assists': row['AST'],
        'steals': row['STL'],
        'blocks': row['BLK'],
        'turnovers': row['TOV'],
        'three_pm': row['FG3M'],
        'oreb': row['OREB'],
    }, fantasy_settings), axis=1)

    df['fantasy_season_total'] = df['fantasy_ppg'] * df['GP']

    df = df.sort_values(by='fantasy_ppg', ascending=False).reset_index(drop=True)
    df['rank'] = df.index + 1

    output = df.head(limit).rename(columns={
        'PLAYER_NAME': 'player',
        'REB': 'rpg',
        'AST': 'apg',
        'PTS': 'ppg',
        'STL': 'stl',
        'BLK': 'blk',
        'TOV': 'tov'
    })
    return output[['rank', 'player', 'fantasy_ppg', 'fantasy_season_total', 'ppg', 'rpg', 'apg', 'stl', 'blk', 'tov']].to_dict(orient='records')


# ---------------------------------------------------------------------------
# MOCK DRAFT UTILITIES
# ---------------------------------------------------------------------------

class MockDraft:
    """
    Simple mock draft simulator
    """
    def __init__(self, num_teams: int = 12, rounds: int = 15):
        self.num_teams = num_teams
        self.rounds = rounds
        self.draft_order = []
        self.teams = {i: [] for i in range(1, num_teams + 1)}
        self.available_players = []
        self.current_pick = 0
        
        # Generate snake draft order
        for round_num in range(1, rounds + 1):
            if round_num % 2 == 1:  # Odd rounds: 1, 2, 3...
                self.draft_order.extend(range(1, num_teams + 1))
            else:  # Even rounds: ...3, 2, 1 (snake)
                self.draft_order.extend(range(num_teams, 0, -1))
    
    def load_available_players(self, rankings: List[dict]):
        """Load ranked players as available for draft"""
        self.available_players = rankings.copy()
    
    def draft_player(self, team_num: int, player_name: str) -> bool:
        """
        Draft a player to a team
        Returns True if successful, False if player not available
        """
        # Find player in available list
        player_data = None
        for i, p in enumerate(self.available_players):
            if p['player'].lower() == player_name.lower():
                player_data = self.available_players.pop(i)
                break
        
        if player_data is None:
            return False
        
        # Add to team
        self.teams[team_num].append(player_data)
        self.current_pick += 1
        return True
    
    def auto_draft_next(self) -> dict:
        """
        Automatically draft the highest-ranked available player for the next team
        """
        if self.current_pick >= len(self.draft_order):
            return None
        
        team_num = self.draft_order[self.current_pick]
        
        if not self.available_players:
            return None
        
        # Draft best available player
        player = self.available_players.pop(0)
        self.teams[team_num].append(player)
        
        result = {
            'pick': self.current_pick + 1,
            'round': (self.current_pick // self.num_teams) + 1,
            'team': team_num,
            'player': player['player'],
            'fantasy_ppg': player['fantasy_ppg']
        }
        
        self.current_pick += 1
        return result
    
    def get_team_roster(self, team_num: int) -> List[dict]:
        """Get a team's drafted players"""
        return self.teams.get(team_num, [])
    
    def get_draft_summary(self) -> dict:
        """Get summary of entire draft"""
        return {
            'total_picks': self.current_pick,
            'picks_remaining': len(self.draft_order) - self.current_pick,
            'teams': {
                team_num: {
                    'roster': players,
                    'total_projected_fantasy': sum(p['fantasy_ppg'] for p in players)
                }
                for team_num, players in self.teams.items()
            }
        }


def simulate_mock_draft(player_rankings: List[dict], num_teams: int = 12, rounds: int = 15) -> dict:
    """
    Simulate a complete mock draft
    
    Args:
        player_rankings: List of ranked players from rank_players_by_projections()
        num_teams: Number of teams in the draft
        rounds: Number of rounds
    
    Returns:
        Complete draft results
    """
    draft = MockDraft(num_teams, rounds)
    draft.load_available_players(player_rankings)
    
    picks = []
    while draft.current_pick < len(draft.draft_order) and draft.available_players:
        pick_result = draft.auto_draft_next()
        if pick_result:
            picks.append(pick_result)
    
    return {
        'draft_picks': picks,
        'summary': draft.get_draft_summary()
    }


# ---------------------------------------------------------------------------
# COMPARISON UTILITIES
# ---------------------------------------------------------------------------

def compare_players(player_names: List[str], season: str = "2025-26", fantasy_settings=None) -> dict:
    """
    Compare multiple players side-by-side with projections and advanced stats
    """
    comparisons = []
    
    for name in player_names:
        try:
            # Get projections
            projections = get_all_projections(name, season)
            
            # Get current season stats
            current_stats = get_season_averages_with_advanced_stats(name, "2025-26")
            
            if projections:
                season_proj = projections.get('season_projections', {}).get('recent_seasons', {})
                
                player_data = {
                    'player': name,
                    'current_season': current_stats,
                    'projected_next_season': {
                        'ppg': season_proj.get('projected_per_game', {}).get('points', 0),
                        'rpg': season_proj.get('projected_per_game', {}).get('rebounds', 0),
                        'apg': season_proj.get('projected_per_game', {}).get('assists', 0),
                        'fantasy_ppg': season_proj.get('projected_fantasy_points_per_game', 0)
                    }
                }
                
                comparisons.append(player_data)
            
            time.sleep(0.7)
            
        except Exception as e:
            print(f"Error comparing {name}: {e}")
            continue
    
    return {'players': comparisons}