from nba_api.stats.endpoints import playercareerstats
from nba_api.live.nba.endpoints import scoreboard
from find_player import *
from player_calculations import *
from find_game import *
import pandas as pd
from fantasy import *
 
def player_mode():
    players = get_all_players()
    while True:
        while True:
            player_name = input("Enter player full name: ")
            if player_name is None or player_name.strip() == "":
                print("No player name provided.")
            elif player_name.isnumeric():
                print("Player name cannot be numeric.")
            elif player_name.count(" ") < 1:
                print("Please provide both first and last name of the player.")

            elif player_name.count(" ") > 3:
                print("Please provide a valid player name with first and last name only.")

            elif player_name.lower() not in [p['full_name'].lower() for p in list(players)]:
                print(f"Player '{player_name}' not found in the database.")
            else:
                break
        get_player_id(player_name)
        print(f"Player ID for {player_name}: {get_player_id(player_name)}")

        averages = calculate_averages(player_name)
        print(f"Averages for {player_name}:\n{averages}")

        if input("Do you want to look up another player? (yes/no): ").strip().lower() != 'yes':
            break


def game_mode():
    players = get_all_players()
    while True:
        player_name = input("Enter player full name for game lookup: ")
        if player_name is None or player_name.strip() == "":
            print("No player name provided.")
            continue
        elif player_name.isnumeric():
            print("Player name cannot be numeric.")
            continue
        elif player_name.count(" ") < 1:
            print("Please provide both first and last name of the player.")
            continue
        elif player_name.count(" ") > 3:
            print("Please provide a valid player name with first and last name only.")
            continue
        elif player_name.lower() not in [p['full_name'].lower() for p in list(players)]:
            print(f"Player '{player_name}' not found in the database.")
            continue

        date_input = input("Enter game date (YYYY-MM-DD): ")
        try:
            date = pd.to_datetime(date_input)
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            continue

        try:
            game_id = get_game_id(player_name, date)

            find_individual_game_stats_df = find_individual_game_stats(game_id, player_name)
            print(f"Game stats for {player_name} on {date.date()} (Game ID  {game_id}):\n{find_individual_game_stats_df}")
        except ValueError as e:
            print(e)

        if input("Do you want to look up another game? (yes/no): ").strip().lower() != 'yes':
            break

def fantasy_mode():
    while True:
        mode = input("Select fantasy mode (single/full/exit): ").strip().lower()
        if mode == 'single':
            player_name = input("Enter player full name: ")
            game_date = input("Enter game date (YYYY-MM-DD): ")
            fantasy_points_value = calculate_fantasy_points_single_game(player_name, game_date)
            if fantasy_points_value is not None:
                print(f"Fantasy points for {player_name} on {game_date}: {fantasy_points_value}")
            else:
                print(f"Could not calculate fantasy points for {player_name} on {game_date}.")
        elif mode == 'full':
            player_name = input("Enter player full name: ")
            total_fantasy_points = calculate_fantasy_points_full_season(player_name)
            if total_fantasy_points is not None:
                print(f"Total fantasy points for {player_name} in the season:\n {total_fantasy_points}")
            else:
                print(f"Could not calculate total fantasy points for {player_name} by season.")
        elif mode == 'exit':
            print("Exiting fantasy mode.")
            break
        else:
            print("Invalid mode selected. Please choose 'single', 'full', or 'exit'.")

def main():
    while True:
        mode = input("Select mode (player/game/fantasy/exit): ").strip().lower()
        if mode == 'player':
            player_mode()
        elif mode == 'game':
            game_mode()
        elif mode == 'fantasy':
            fantasy_mode()
        elif mode == 'exit':
            print("Exiting the program.")
            break
        else:
            print("Invalid mode selected. Please choose 'player', 'game', or 'exit'.")


if __name__ == "__main__":
    main()
