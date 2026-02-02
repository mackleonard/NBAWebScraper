from nba_api.stats.endpoints import playercareerstats
from find_player import *
import pandas as pd

def calculate_player_career_stats_regular_season(player_name):
    player_id = get_player_id(player_name)
    if player_id is None:
        print(f"Player '{player_name}' not found.")
        return None

    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_df = career_stats.season_totals_regular_season.get_data_frame()
    return career_df

def calculate_averages(player_name):
    career_df = calculate_player_career_stats_regular_season(player_name)
    if career_df is not None:
        season = career_df['SEASON_ID']
        average_minutes = round(career_df['MIN'] / career_df['GP'], 1)
        average_points = round(career_df['PTS'] / career_df['GP'], 1)
        average_rebounds = round(career_df['REB'] / career_df['GP'], 1)
        average_assists = round(career_df['AST'] / career_df['GP'], 1)
        average_blocks = round(career_df['BLK'] / career_df['GP'], 1)
        average_steals = round(career_df['STL'] / career_df['GP'], 1)
        averages = pd.DataFrame({
            'Season': season,
            'MPG': average_minutes,
            'PPG': average_points,
            'RPG': average_rebounds,
            'APG': average_assists,
            'BLK': average_blocks,
            'STL': average_steals
        })
        return averages
    return None