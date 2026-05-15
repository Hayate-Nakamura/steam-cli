import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.config import SteamCliConfig, load_config, save_config


class ConfigTest(unittest.TestCase):
    def test_save_and_load_config(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            save_config(
                SteamCliConfig(
                    steam_id="76561198000000000",
                    web_api_key="key",
                    language="japanese",
                ),
                config_path,
            )

            config = load_config(config_path)

        self.assertEqual(config.steam_id, "76561198000000000")
        self.assertEqual(config.web_api_key, "key")
        self.assertEqual(config.language, "japanese")

    def test_load_config_ignores_invalid_json(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text("{", encoding="utf-8")

            config = load_config(config_path)

        self.assertIsNone(config.steam_id)
        self.assertIsNone(config.web_api_key)
        self.assertIsNone(config.language)

    def test_save_config_writes_versioned_json(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            save_config(SteamCliConfig("steam-id", "key"), config_path)

            data = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(data["version"], 2)

    def test_load_config_reads_legacy_plaintext_web_api_key(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "steam_id": "76561198000000000",
                        "web_api_key": "legacy-key",
                        "language": "japanese",
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(config_path)

        self.assertEqual(config.web_api_key, "legacy-key")

    def test_save_config_protects_web_api_key_when_dpapi_is_available(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            with patch("steam_cli.config._protect_windows_secret", return_value="encrypted-key"):
                save_config(SteamCliConfig("steam-id", "secret-key"), config_path)

            data = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertNotIn("web_api_key", data)
        self.assertEqual(
            data["web_api_key_protected"],
            {"scheme": "windows-dpapi", "ciphertext": "encrypted-key"},
        )

    def test_load_config_unprotects_web_api_key(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "steam_id": "76561198000000000",
                        "web_api_key_protected": {
                            "scheme": "windows-dpapi",
                            "ciphertext": "encrypted-key",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch("steam_cli.config._unprotect_windows_secret", return_value="secret-key"):
                config = load_config(config_path)

        self.assertEqual(config.web_api_key, "secret-key")


if __name__ == "__main__":
    unittest.main()
