from nba_api.stats.endpoints import playercareerstats, cumestatsplayergames
from nba_api.live.nba.endpoints import scoreboard
from find_player import *
from player_calculations import *
from find_game import *
import pandas as pd
import time

def calculate_fantasy_points_single_game(player_name, game_date):
    """
    Calculate fantasy points for a single game.
    
    Fantasy scoring:
    - Points: 1 point each
    - Rebounds: 1 point each
    - Assists: 1.5 points each
    - Steals: 2 points each
    - Blocks: 2 points each
    - Turnovers: -2 points each
    - 3-pointers made: 1 bonus point each
    - Offensive rebounds: 0.5 bonus points each
    """
    try:
        # Add delay to avoid rate limiting
        time.sleep(0.6)
        game_id = get_game_id(player_name, game_date)
        
        time.sleep(0.6)
        player_stats_df = find_individual_game_stats(game_id, player_name)

        if player_stats_df.empty:
            print(f"No stats found for {player_name} in game {game_id}")
            return None

        fantasy_points = (
            player_stats_df['PTS'].iloc[0]
            + player_stats_df['REB'].iloc[0]
            + player_stats_df['AST'].iloc[0] * 1.5
            + player_stats_df['STL'].iloc[0] * 2
            + player_stats_df['BLK'].iloc[0] * 2
            - player_stats_df['TO'].iloc[0] * 2
            + player_stats_df['FG3M'].iloc[0]
            + player_stats_df['OREB'].iloc[0] * 0.5
        )

        return float(fantasy_points)

    except ValueError as e:
        print(f"ValueError in calculate_fantasy_points_single_game: {e}")
        return None
    except Exception as e:
        print(f"Error in calculate_fantasy_points_single_game: {e}")
        return None
    
def calculate_fantasy_points_full_season(player_name):
    """
    Calculate fantasy points for all seasons in a player's career.
    Returns a DataFrame with season and total fantasy points.
    """
    try:
        career_stats = calculate_player_career_stats_regular_season(player_name)
        if career_stats is None or career_stats.empty:
            print(f"No career stats found for {player_name}")
            return None

        df = pd.DataFrame({
            'season': career_stats['SEASON_ID'].astype(str),
            'pts': pd.to_numeric(career_stats['PTS'], errors='coerce'),
            'reb': pd.to_numeric(career_stats['REB'], errors='coerce'),
            'ast': pd.to_numeric(career_stats['AST'], errors='coerce'),
            'stl': pd.to_numeric(career_stats['STL'], errors='coerce'),
            'blk': pd.to_numeric(career_stats['BLK'], errors='coerce'),
            'to': pd.to_numeric(career_stats['TOV'], errors='coerce'),
            'fg3m': pd.to_numeric(career_stats['FG3M'], errors='coerce'),
            'oreb': pd.to_numeric(career_stats['OREB'], errors='coerce'),
        }).fillna(0)

        df['fantasy_points'] = (
            df['pts']
            + df['reb']
            + df['ast'] * 1.5
            + df['stl'] * 2
            + df['blk'] * 2
            - df['to'] * 2
            + df['fg3m']
            + df['oreb'] * 0.5
        )

        return df[['season', 'fantasy_points']]
    except Exception as e:
        print(f"Error in calculate_fantasy_points_full_season: {e}")
        return None