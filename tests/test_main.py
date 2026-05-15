import sys
import unittest
from contextlib import redirect_stderr
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.main import build_parser, main
from steam_cli.models import SteamGame


class MainTest(unittest.TestCase):
    def test_filter_accepts_playtime_options(self):
        parser = build_parser()

        args = parser.parse_args(["filter", "--played", "--min-playtime", "60", "--max-playtime", "120"])

        self.assertTrue(args.played)
        self.assertEqual(args.min_playtime, 60)
        self.assertEqual(args.max_playtime, 120)

    def test_filter_accepts_metadata_options(self):
        parser = build_parser()

        args = parser.parse_args(
            ["filter", "--app-id", "123", "--name", "example", "--install-path", "common"]
        )

        self.assertEqual(args.app_id, "123")
        self.assertEqual(args.name, "example")
        self.assertEqual(args.install_path, "common")

    def test_filter_rejects_negative_playtime(self):
        parser = build_parser()

        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["filter", "--min-playtime", "-1"])

    def test_filter_requires_at_least_one_filter_before_scanning(self):
        with patch("steam_cli.main.find_installed_games") as find_installed_games:
            with redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as exc:
                    main(["filter"])

        self.assertEqual(exc.exception.code, 2)
        find_installed_games.assert_not_called()

    def test_filter_rejects_invalid_regex_before_scanning(self):
        with patch("steam_cli.main.find_installed_games") as find_installed_games:
            with redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as exc:
                    main(["filter", "--name", "["])

        self.assertEqual(exc.exception.code, 2)
        find_installed_games.assert_not_called()

    def test_filter_by_app_id_does_not_require_playtime(self):
        games = [
            SteamGame(app_id="123", name="Example Game", install_path=Path("C:/Steam/common/ExampleGame")),
            SteamGame(app_id="456", name="Other Game", install_path=Path("C:/Steam/common/OtherGame")),
        ]

        with patch("steam_cli.main.find_installed_games", return_value=games):
            with patch("steam_cli.main.localize_game_names", return_value=games):
                with patch("steam_cli.main.add_playtime") as add_playtime:
                    output = StringIO()
                    with redirect_stdout(output):
                        exit_code = main(["filter", "--app-id", "123", "--json"])

        self.assertEqual(exit_code, 0)
        add_playtime.assert_not_called()
        self.assertIn('"app_id": "123"', output.getvalue())
        self.assertNotIn('"app_id": "456"', output.getvalue())
        self.assertNotIn("playtime_forever_minutes", output.getvalue())

    def test_filter_by_name_and_install_path_uses_regex(self):
        games = [
            SteamGame(app_id="123", name="Example Game", install_path=Path("C:/Steam/common/ExampleGame")),
            SteamGame(app_id="456", name="Other Game", install_path=Path("D:/Games/OtherGame")),
        ]

        with patch("steam_cli.main.find_installed_games", return_value=games):
            with patch("steam_cli.main.localize_game_names", return_value=games):
                output = StringIO()
                with redirect_stdout(output):
                    exit_code = main(["filter", "--name", "example", "--install-path", "steam", "--json"])

        self.assertEqual(exit_code, 0)
        self.assertIn('"app_id": "123"', output.getvalue())
        self.assertNotIn('"app_id": "456"', output.getvalue())

    def test_filter_rejects_min_greater_than_max_before_scanning(self):
        with patch("steam_cli.main.find_installed_games") as find_installed_games:
            with redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as exc:
                    main(["filter", "--min-playtime", "120", "--max-playtime", "60"])

        self.assertEqual(exc.exception.code, 2)
        find_installed_games.assert_not_called()


if __name__ == "__main__":
    unittest.main()
