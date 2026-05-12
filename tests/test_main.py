import sys
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.main import build_parser, main


class MainTest(unittest.TestCase):
    def test_filter_accepts_playtime_options(self):
        parser = build_parser()

        args = parser.parse_args(["filter", "--played", "--min-playtime", "60", "--max-playtime", "120"])

        self.assertTrue(args.played)
        self.assertEqual(args.min_playtime, 60)
        self.assertEqual(args.max_playtime, 120)

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

    def test_filter_rejects_min_greater_than_max_before_scanning(self):
        with patch("steam_cli.main.find_installed_games") as find_installed_games:
            with redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as exc:
                    main(["filter", "--min-playtime", "120", "--max-playtime", "60"])

        self.assertEqual(exc.exception.code, 2)
        find_installed_games.assert_not_called()


if __name__ == "__main__":
    unittest.main()
