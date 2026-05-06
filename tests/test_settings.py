import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.config import SteamCliConfig, load_config, save_config
from steam_cli.settings import (
    SteamCliConfigError,
    configure_settings,
    format_configuration_status,
    get_configuration_status,
    reset_configuration,
    resolve_language,
)


class SettingsTest(unittest.TestCase):
    def test_configure_settings_validates_and_saves_credentials(self):
        def fake_fetch_json(_url):
            return {"response": {"game_count": 0, "games": []}}

        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            saved_path = configure_settings(
                "76561198000000000",
                "key",
                "japanese",
                config_path,
                fake_fetch_json,
            )
            config = load_config(config_path)

        self.assertEqual(saved_path, config_path)
        self.assertEqual(config.steam_id, "76561198000000000")
        self.assertEqual(config.web_api_key, "key")
        self.assertEqual(config.language, "japanese")

    def test_configure_settings_rejects_invalid_credentials(self):
        def fake_fetch_json(_url):
            return {"error": "forbidden"}

        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            with self.assertRaises(SteamCliConfigError):
                configure_settings("76561198000000000", "bad-key", None, config_path, fake_fetch_json)

    def test_get_configuration_status_validates_saved_config(self):
        def fake_fetch_json(_url):
            return {"response": {"game_count": 0, "games": []}}

        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            configure_settings("76561198000000000", "secret-key", "japanese", config_path, fake_fetch_json)
            store_cache_path = Path(temp_dir) / "store_names.json"
            playtime_cache_path = Path(temp_dir) / "webapi_playtime.json"
            store_cache_path.write_text(
                json.dumps({"version": 1, "entries": {"japanese:123": {"fetched_at": 100}}}),
                encoding="utf-8",
            )
            playtime_cache_path.write_text(
                json.dumps({"version": 1, "entries": {"765": {"fetched_at": 100}}}),
                encoding="utf-8",
            )

            with patch("steam_cli.settings.default_store_name_cache_path", return_value=store_cache_path):
                with patch("steam_cli.settings.default_playtime_cache_path", return_value=playtime_cache_path):
                    result = get_configuration_status(config_path=config_path, fetch_json=fake_fetch_json)
            output = format_configuration_status(result)

        self.assertTrue(result.has_web_api_credentials)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.language, "japanese")
        self.assertIn("SteamID64: configured (config file)", output)
        self.assertIn("Steam Web API key: configured (config file)", output)
        self.assertIn("Language: japanese (config file)", output)
        self.assertIn("Steam Store name cache: 1 entries", output)
        self.assertIn("Steam Web API playtime cache: 1 entries", output)
        self.assertIn("Steam Web API validation: OK", output)
        self.assertNotIn("secret-key", output)

    def test_get_configuration_status_reports_missing_values(self):
        def fake_fetch_json(_url):
            raise AssertionError("validation should be skipped")

        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "missing-config.json"

            with patch("steam_cli.settings.detect_steam_language", return_value="japanese"):
                result = get_configuration_status(config_path=config_path, fetch_json=fake_fetch_json)
            output = format_configuration_status(result)

        self.assertFalse(result.has_web_api_credentials)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.language, "japanese")
        self.assertEqual(result.language_source, "OS locale")
        self.assertIn("SteamID64: missing", output)
        self.assertIn("Steam Web API key: missing", output)
        self.assertIn("Steam Web API validation: skipped", output)

    def test_get_configuration_status_reports_failed_validation(self):
        def fake_fetch_json(_url):
            return {"error": "forbidden"}

        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            result = get_configuration_status(
                "76561198000000000",
                "bad-key",
                "japanese",
                config_path,
                fake_fetch_json,
            )
            output = format_configuration_status(result)

        self.assertTrue(result.has_web_api_credentials)
        self.assertFalse(result.is_valid)
        self.assertIn("Steam Web API validation: failed", output)

    def test_resolve_language_precedence(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            save_config(SteamCliConfig(language="german"), config_path)
            stored_config = load_config(config_path)

            with patch.dict("os.environ", {"STEAM_CLI_LANGUAGE": "french"}):
                self.assertEqual(resolve_language("japanese", stored_config), ("japanese", "command-line option"))
                self.assertEqual(resolve_language(None, stored_config), ("french", "STEAM_CLI_LANGUAGE environment variable"))

            self.assertEqual(resolve_language(None, stored_config), ("german", "config file"))

    def test_resolve_language_uses_os_locale_when_not_configured(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("steam_cli.settings.detect_steam_language", return_value="japanese"):
                self.assertEqual(resolve_language(), ("japanese", "OS locale"))

    def test_reset_configuration_removes_config_file(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            save_config(SteamCliConfig("steam-id", "key", "japanese"), config_path)

            removed_path = reset_configuration(config_path)

            self.assertEqual(removed_path, config_path)
            self.assertFalse(config_path.exists())


if __name__ == "__main__":
    unittest.main()
