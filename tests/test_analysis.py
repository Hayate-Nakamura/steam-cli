import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.analysis import sort_games, summarize_games
from steam_cli.models import SteamGame


class AnalysisTest(unittest.TestCase):
    def test_sort_games_by_size_keeps_unknown_values_last(self):
        games = [
            SteamGame(app_id="1", name="Unknown", install_path=Path("C:/Steam/steamapps/common/Unknown")),
            SteamGame(
                app_id="2",
                name="Small",
                install_path=Path("C:/Steam/steamapps/common/Small"),
                install_size_bytes=10,
            ),
            SteamGame(
                app_id="3",
                name="Large",
                install_path=Path("C:/Steam/steamapps/common/Large"),
                install_size_bytes=100,
            ),
        ]

        ascending = sort_games(games, "size")
        descending = sort_games(games, "size", descending=True)

        self.assertEqual([game.app_id for game in ascending], ["2", "3", "1"])
        self.assertEqual([game.app_id for game in descending], ["3", "2", "1"])

    def test_sort_games_by_last_updated(self):
        games = [
            SteamGame(
                app_id="1",
                name="Old",
                install_path=Path("C:/Steam/steamapps/common/Old"),
                last_updated_at=datetime(2023, 1, 1),
            ),
            SteamGame(
                app_id="2",
                name="New",
                install_path=Path("C:/Steam/steamapps/common/New"),
                last_updated_at=datetime(2024, 1, 1),
            ),
        ]

        sorted_games = sort_games(games, "last-updated", descending=True)

        self.assertEqual([game.app_id for game in sorted_games], ["2", "1"])

    def test_summarize_games_groups_by_library(self):
        games = [
            SteamGame(
                app_id="1",
                name="One",
                install_path=Path("C:/Steam/steamapps/common/One"),
                install_size_bytes=10,
                playtime_forever_minutes=30,
            ),
            SteamGame(
                app_id="2",
                name="Two",
                install_path=Path("D:/Library/steamapps/common/Two"),
                install_size_bytes=20,
                playtime_forever_minutes=None,
            ),
        ]

        summary = summarize_games(games, include_playtime=True)

        self.assertEqual(summary.game_count, 2)
        self.assertEqual(summary.install_size_bytes, 30)
        self.assertEqual(summary.playtime_forever_minutes, 30)
        self.assertEqual(summary.unknown_playtime_count, 1)
        self.assertEqual([library.path for library in summary.libraries], [Path("C:/Steam"), Path("D:/Library")])


if __name__ == "__main__":
    unittest.main()
