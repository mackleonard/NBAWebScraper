import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from find_game import *
from find_player import *
import pandas as pd
import unittest


class TestFindGame(unittest.TestCase):

    def test_find_games_by_team_and_season(self):
        team_name = "Los Angeles Lakers"
        season = "2020-21"
        games_df = find_games_by_team_and_season(team_name, season)
        print(games_df)

        self.assertIsNotNone(games_df, "Games DataFrame should not be None")
        self.assertFalse(games_df.empty, "Games DataFrame should not be empty")
        self.assertIn('TEAM_NAME', games_df.columns, "Games DataFrame should contain 'TEAM_NAME' column")
        self.assertTrue(all(games_df['TEAM_NAME'] == team_name), f"All games should be for team '{team_name}'")

    def test_find_individual_game_stats(self):
        player_name = "Dorian Finney-Smith"
        player_id = get_player_id(player_name)
        game_id = "0022001071"  # Example game ID

        player_stats = find_individual_game_stats(game_id, player_name)

        self.assertIsNotNone(player_stats, "Player stats should not be None")
        self.assertFalse(player_stats.empty, "Player stats should not be empty")
        self.assertTrue(all(player_stats['personId'] == player_id), f"Stats should be for player ID '{player_id}'")

    def test_get_game_id(self):

        player_name = "Dorian Finney-Smith"
        date = pd.to_datetime("2026-01-28")

        game_id = get_game_id(player_name, date)
        print(f"Game ID for {player_name} on {date.date()}: {game_id}")

        self.assertIsNotNone(game_id, "Game ID should not be None")
        self.assertIsInstance(game_id, str, "Game ID should be a string")
        self.assertEqual(len(game_id), 10, "Game ID should be 10 characters long")


if __name__ == '__main__':
    unittest.main()