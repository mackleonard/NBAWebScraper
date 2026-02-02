from nba_api.stats.endpoints import playercareerstats, cumestatsplayergames
from nba_api.live.nba.endpoints import scoreboard
from find_player import *
from player_calculations import *
from find_game import *
import pandas as pd

def calculate_fantasy_points_single_game(player_name, game_date):
    fantasy_points_value = 0
    try:
        game_id = get_game_id(player_name, game_date)
        player_stats_df = find_individual_game_stats(game_id, player_name)
        if player_stats_df.empty:
            print(f"No stats found for {player_name} in the game on {game_date}.")
            return None
        fantasy_points_df = pd.DataFrame({
            'PTS': player_stats_df['PTS'],
            'REB': player_stats_df['REB'],
            'AST': player_stats_df['AST'],
            'STL': player_stats_df['STL'],
            'BLK': player_stats_df['BLK'],
            'TO': player_stats_df['TO'],
            'FG3M': player_stats_df['FG3M'],
            'OREB': player_stats_df['OREB']
        })
        fantasy_points_value += fantasy_points_df['PTS'] + \
                                fantasy_points_df['REB'] * 1 + \
                                fantasy_points_df['AST'] * 1.5 + \
                                fantasy_points_df['STL'] * 2 + \
                                fantasy_points_df['BLK'] * 2 - \
                                fantasy_points_df['TO'] * 2 + \
                                fantasy_points_df['FG3M'] * 1 + \
                                fantasy_points_df['OREB'] * 0.5

                                
        return fantasy_points_value.to_string(index=False)
    except ValueError as e:
        print(e)
        return None
    
def calculate_fantasy_points_full_season(player_name):
    career_stats = calculate_player_career_stats_regular_season(player_name)
    if career_stats is None:
        print(f"No career stats found for {player_name}.")
        return None
    fantasy_points_df = pd.DataFrame({
        'Season': career_stats['SEASON_ID'].astype(str),
        'PTS': pd.to_numeric(career_stats['PTS'], errors='coerce'),
        'REB': pd.to_numeric(career_stats['REB'], errors='coerce'),
        'AST': pd.to_numeric(career_stats['AST'], errors='coerce'),
        'STL': pd.to_numeric(career_stats['STL'], errors='coerce'),
        'BLK': pd.to_numeric(career_stats['BLK'], errors='coerce'),
        'TO': pd.to_numeric(career_stats['TOV'], errors='coerce'),
        'FG3M': pd.to_numeric(career_stats['FG3M'], errors='coerce'),
        'OREB': pd.to_numeric(career_stats['OREB'], errors='coerce'),
    }).fillna(0.0)

    fantasy_points_df['Total Fantasy Points'] = (
    fantasy_points_df['PTS']
    + fantasy_points_df['REB']
    + fantasy_points_df['AST'] * 1.5
    + fantasy_points_df['STL'] * 2
    + fantasy_points_df['BLK'] * 2
    - fantasy_points_df['TO'] * 2
    + fantasy_points_df['FG3M']
    + fantasy_points_df['OREB'] * 0.5
    )

    return fantasy_points_df[['Season', 'Total Fantasy Points']].to_string(index=False,
        col_space=20,
        justify="left")