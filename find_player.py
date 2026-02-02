from nba_api.stats.static.players import find_players_by_full_name, find_players_by_first_name, find_players_by_last_name, _get_players
import pandas as pd
from nba_api.stats.endpoints import playerindex

def find_player_by_first_and_last(player_name):
    return find_players_by_full_name(player_name)

def find_player_by_first_name(first_name):
    return find_players_by_first_name(first_name)

def find_player_by_last_name(last_name):
    return find_players_by_last_name(last_name)

def get_all_players():
    return _get_players()

def get_active_players():
    return get_active_players()

def get_player_id(player_name):
    players = find_players_by_full_name(player_name)
    if players:
        return players[0]['id']
    else:
        return None
    
def get_player_team(player_name):
    player_id = get_player_id(player_name)
    if player_id is not None:
        career_stats = playerindex.PlayerIndex(player_id)
        return career_stats.get_data_frames()[0]['TEAM_NAME'].iloc[0]
    return None 