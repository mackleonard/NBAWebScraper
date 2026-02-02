import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from find_game import *
from find_player import *
import pandas as pd
import unittest
from fantasy import *


class TestFantasy(unittest.TestCase):

    def test_calculate_fantasy_points(self):
        player_name = "Victor Wembanyama"
        game_date = "2026-01-28"
        fantasy_points_value = calculate_fantasy_points_single_game(player_name, game_date)
        
        print(f"Fantasy points for {player_name} on {game_date}: {fantasy_points_value}")
        self.assertIsNotNone(fantasy_points_value)

    def test_calculate_fantasy_points_full_season(self):
        player_name = "Jalen Johnson"
        total_fantasy_points = calculate_fantasy_points_full_season(player_name)
        
        print(f"Total fantasy points for {player_name} by season:\n {total_fantasy_points}")
        self.assertIsNotNone(total_fantasy_points)

if __name__ == '__main__':
    unittest.main()