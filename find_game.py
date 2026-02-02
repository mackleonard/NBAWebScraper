from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
from nba_api.stats.endpoints import boxscoretraditionalv3, playergamelog
from find_player import get_player_id
import pandas as pd

def find_games_by_team_and_season(team_name, season):
    team_info = teams.find_teams_by_full_name(team_name)
    if not team_info:
        print(f"Team '{team_name}' not found.")
        return None

    team_id = team_info[0]['id']
    game_finder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id, season_nullable=season)
    games_df = game_finder.get_data_frames()[0]
    return games_df

def find_individual_game_stats(game_id, player_name):
    player_id = get_player_id(player_name)
    boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
    player_stats_df = pd.DataFrame(boxscore.get_data_frames()[0])
    player_stats = player_stats_df[player_stats_df['personId'] == player_id]
    relevant_stats = pd.DataFrame({
        'MIN': player_stats['minutes'],
        'PTS': player_stats['points'],
        'REB': player_stats['reboundsTotal'],
        'AST': player_stats['assists'],
        'BLK': player_stats['blocks'],
        'STL': player_stats['steals'],
        'TO': player_stats['turnovers'],
        'FG3M': player_stats['threePointersMade'],
        'OREB': player_stats['reboundsOffensive']
    }
    )
    return relevant_stats

def get_game_id(player_name, date):
    player_id = get_player_id(player_name)
    date = pd.to_datetime(date)
    date_from = (date - pd.Timedelta(days=1)).strftime("%m/%d/%Y")
    date_to = (date + pd.Timedelta(days=1)).strftime("%m/%d/%Y")
    game_log = playergamelog.PlayerGameLog(
        player_id=player_id,
        date_from_nullable=date_from,
        date_to_nullable=date_to
    )  
    df = game_log.get_data_frames()[0]
    if df.empty:
        raise ValueError(f"No games found for {player_name} around {date.date()}")
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="mixed")
    df["date_diff"] = (df["GAME_DATE"] - date).abs()
    game_row = df.sort_values("date_diff").iloc[0]
    return game_row["Game_ID"]

