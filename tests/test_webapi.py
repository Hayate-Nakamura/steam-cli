import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.models import SteamGame
from steam_cli.webapi import (
    SteamWebApiConfigError,
    add_playtime,
    fetch_owned_game_playtimes,
    filter_unplayed_games,
    resolve_steam_id,
    resolve_web_api_key,
    validate_credentials,
)


class WebApiTest(unittest.TestCase):
    def test_fetch_owned_game_playtimes_extracts_minutes(self):
        requested = {}

        def fake_fetch_json(url):
            query = parse_qs(urlparse(url).query)
            requested["steamid"] = query["steamid"][0]
            requested["include_played_free_games"] = query["include_played_free_games"][0]
            return {
                "response": {
                    "games": [
                        {"appid": 123, "playtime_forever": 0},
                        {"appid": 456, "playtime_forever": 125},
                    ]
                }
            }

        with TemporaryDirectory() as temp_dir:
            playtimes = fetch_owned_game_playtimes(
                "76561198000000000",
                "key",
                fake_fetch_json,
                cache_path=Path(temp_dir) / "playtime.json",
            )

        self.assertEqual(playtimes, {"123": 0, "456": 125})
        self.assertEqual(requested["steamid"], "76561198000000000")
        self.assertEqual(requested["include_played_free_games"], "true")

    def test_fetch_owned_game_playtimes_uses_fresh_cache(self):
        with TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "playtime.json"

            def first_fetch_json(_url):
                return {"response": {"games": [{"appid": 123, "playtime_forever": 125}]}}

            fetch_owned_game_playtimes(
                "76561198000000000",
                "key",
                first_fetch_json,
                cache_path=cache_path,
                now=100,
            )

            def failing_fetch_json(_url):
                raise AssertionError("fresh cache should avoid Steam Web API calls")

            playtimes = fetch_owned_game_playtimes(
                "76561198000000000",
                "key",
                failing_fetch_json,
                cache_path=cache_path,
                now=101,
            )

        self.assertEqual(playtimes, {"123": 125})

    def test_fetch_owned_game_playtimes_refreshes_cache_when_requested(self):
        with TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "playtime.json"

            def first_fetch_json(_url):
                return {"response": {"games": [{"appid": 123, "playtime_forever": 125}]}}

            fetch_owned_game_playtimes(
                "76561198000000000",
                "key",
                first_fetch_json,
                cache_path=cache_path,
                now=100,
            )

            def second_fetch_json(_url):
                return {"response": {"games": [{"appid": 123, "playtime_forever": 130}]}}

            playtimes = fetch_owned_game_playtimes(
                "76561198000000000",
                "key",
                second_fetch_json,
                cache_path=cache_path,
                now=101,
                refresh=True,
            )

        self.assertEqual(playtimes, {"123": 130})

    def test_add_playtime_sets_matching_games(self):
        games = [
            SteamGame(app_id="123", name="Unplayed", install_path=Path("C:/Steam/A")),
            SteamGame(app_id="456", name="Played", install_path=Path("C:/Steam/B")),
        ]

        def fake_fetch_json(_url):
            return {
                "response": {
                    "games": [
                        {"appid": 123, "playtime_forever": 0},
                        {"appid": 456, "playtime_forever": 125},
                    ]
                }
            }

        with TemporaryDirectory() as temp_dir:
            enriched = add_playtime(
                games,
                "76561198000000000",
                "key",
                fake_fetch_json,
                cache_path=Path(temp_dir) / "playtime.json",
            )

        self.assertEqual(enriched[0].playtime_forever_minutes, 0)
        self.assertEqual(enriched[1].playtime_forever_minutes, 125)

    def test_filter_unplayed_games_keeps_zero_only(self):
        games = [
            SteamGame(app_id="123", name="Unplayed", install_path=Path("C:/Steam/A"), playtime_forever_minutes=0),
            SteamGame(app_id="456", name="Played", install_path=Path("C:/Steam/B"), playtime_forever_minutes=125),
            SteamGame(app_id="789", name="Unknown", install_path=Path("C:/Steam/C"), playtime_forever_minutes=None),
        ]

        unplayed = filter_unplayed_games(games)

        self.assertEqual([game.app_id for game in unplayed], ["123"])

    def test_resolve_credentials_from_environment(self):
        with patch.dict(
            "os.environ",
            {"STEAM_ID": "76561198000000000", "STEAM_WEB_API_KEY": "key"},
        ):
            self.assertEqual(resolve_steam_id(), "76561198000000000")
            self.assertEqual(resolve_web_api_key(), "key")

    def test_resolve_credentials_from_config(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                '{"version": 1, "steam_id": "76561198000000000", "web_api_key": "key", "language": null}',
                encoding="utf-8",
            )

            with patch.dict("os.environ", {}, clear=True):
                with patch("steam_cli.config.default_config_path", return_value=config_path):
                    self.assertEqual(resolve_steam_id(), "76561198000000000")
                    self.assertEqual(resolve_web_api_key(), "key")

    def test_resolve_credentials_require_values(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "missing-config.json"
            with patch.dict("os.environ", {}, clear=True):
                with patch("steam_cli.config.default_config_path", return_value=config_path):
                    with self.assertRaises(SteamWebApiConfigError):
                        resolve_steam_id()
                    with self.assertRaises(SteamWebApiConfigError):
                        resolve_web_api_key()

    def test_validate_credentials_accepts_response_object(self):
        def fake_fetch_json(_url):
            return {"response": {"game_count": 0, "games": []}}

        self.assertTrue(validate_credentials("76561198000000000", "key", fake_fetch_json))

    def test_validate_credentials_rejects_invalid_response(self):
        def fake_fetch_json(_url):
            return {"error": "forbidden"}

        self.assertFalse(validate_credentials("76561198000000000", "key", fake_fetch_json))


if __name__ == "__main__":
    unittest.main()
