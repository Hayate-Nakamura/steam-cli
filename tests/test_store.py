import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.models import SteamGame
from steam_cli.store import detect_steam_language, fetch_store_app_names, localize_game_names


class StoreTest(unittest.TestCase):
    def test_fetch_store_app_names_extracts_successful_names(self):
        requested_app_ids = []

        def fake_fetch_json(url):
            app_id = parse_qs(urlparse(url).query)["appids"][0]
            requested_app_ids.append(app_id)
            payloads = {
                "132520": {
                    "132520": {
                        "success": True,
                        "data": {"name": "仁王 Complete Edition"},
                    }
                },
                "999": {"999": {"success": False}},
            }
            return payloads[app_id]

        with TemporaryDirectory() as temp_dir:
            names = fetch_store_app_names(
                ["132520", "999"],
                "japanese",
                fake_fetch_json,
                cache_path=Path(temp_dir) / "store_names.json",
            )

        self.assertEqual(names, {"132520": "仁王 Complete Edition"})
        self.assertEqual(requested_app_ids, ["132520", "999"])

    def test_localize_game_names_falls_back_to_manifest_name(self):
        games = [
            SteamGame(
                app_id="132520",
                name="Nioh: Complete Edition",
                install_path=Path("C:/Steam/steamapps/common/Nioh"),
            ),
            SteamGame(
                app_id="999",
                name="Manifest Name",
                install_path=Path("C:/Steam/steamapps/common/ManifestName"),
            ),
        ]

        def fake_fetch_json(_url):
            return {
                "132520": {
                    "success": True,
                    "data": {"name": "仁王 Complete Edition"},
                }
            }

        with TemporaryDirectory() as temp_dir:
            localized = localize_game_names(
                games,
                "japanese",
                fake_fetch_json,
                cache_path=Path(temp_dir) / "store_names.json",
            )

        self.assertEqual(localized[0].name, "仁王 Complete Edition")
        self.assertEqual(localized[0].appmanifest_name, None)
        self.assertEqual(localized[0].steam_store_name, "仁王 Complete Edition")
        self.assertEqual(localized[0].name_source, "steam_store")
        self.assertEqual(localized[1].name, "Manifest Name")
        self.assertEqual(localized[1].steam_store_name, None)
        self.assertEqual(localized[1].name_source, "appmanifest")

    def test_detect_steam_language_maps_japanese_locale(self):
        with patch("locale.getlocale", return_value=("ja_JP", "cp932")):
            self.assertEqual(detect_steam_language(), "japanese")

    def test_detect_steam_language_maps_windows_japanese_locale_name(self):
        with patch("locale.getlocale", return_value=("Japanese_Japan", "932")):
            self.assertEqual(detect_steam_language(), "japanese")

    def test_fetch_store_app_names_uses_fresh_cache(self):
        with TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "store_names.json"

            def first_fetch_json(_url):
                return {
                    "132520": {
                        "success": True,
                        "data": {"name": "仁王 Complete Edition"},
                    }
                }

            first_names = fetch_store_app_names(
                ["132520"],
                "japanese",
                first_fetch_json,
                cache_path=cache_path,
                now=1_700_000_000,
            )

            def failing_fetch_json(_url):
                raise AssertionError("fresh cache should avoid Steam Store API calls")

            cached_names = fetch_store_app_names(
                ["132520"],
                "japanese",
                failing_fetch_json,
                cache_path=cache_path,
                now=1_700_000_100,
            )

            self.assertEqual(first_names, {"132520": "仁王 Complete Edition"})
            self.assertEqual(cached_names, {"132520": "仁王 Complete Edition"})

    def test_fetch_store_app_names_refreshes_expired_cache(self):
        with TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "store_names.json"

            def first_fetch_json(_url):
                return {
                    "132520": {
                        "success": True,
                        "data": {"name": "Old Name"},
                    }
                }

            fetch_store_app_names(
                ["132520"],
                "japanese",
                first_fetch_json,
                cache_path=cache_path,
                cache_ttl_seconds=10,
                now=100,
            )

            def second_fetch_json(_url):
                return {
                    "132520": {
                        "success": True,
                        "data": {"name": "New Name"},
                    }
                }

            names = fetch_store_app_names(
                ["132520"],
                "japanese",
                second_fetch_json,
                cache_path=cache_path,
                cache_ttl_seconds=10,
                now=111,
            )

            self.assertEqual(names, {"132520": "New Name"})


if __name__ == "__main__":
    unittest.main()
