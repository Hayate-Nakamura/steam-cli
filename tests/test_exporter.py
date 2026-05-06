import json
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.exporter import format_games_csv, format_games_json, format_games_table
from steam_cli.models import SteamGame


class ExporterTest(unittest.TestCase):
    def test_format_games_table_includes_phase_two_fields(self):
        game = SteamGame(
            app_id="123",
            name="Example Game",
            install_path=Path("C:/Steam/steamapps/common/ExampleGame"),
            install_size_bytes=1073741824,
            last_updated_at=datetime.fromtimestamp(1700000000).astimezone(),
        )

        output = format_games_table([game])

        self.assertIn("Size", output)
        self.assertIn("Last Updated", output)
        self.assertIn("1.0 GB", output)
        self.assertIn("2023/11/15 07:13:20", output)
        self.assertIn("Example Game", output)
        self.assertNotIn("Name Source", output)

    def test_format_games_table_includes_details(self):
        game = SteamGame(
            app_id="132520",
            name="仁王 Complete Edition",
            install_path=Path("C:/Steam/steamapps/common/Nioh"),
            appmanifest_name="Nioh: Complete Edition",
            steam_store_name="仁王 Complete Edition",
            name_source="steam_store",
        )

        output = format_games_table([game], details=True)

        self.assertIn("AppManifest Name", output)
        self.assertIn("Steam Store Name", output)
        self.assertIn("Name Source", output)
        self.assertIn("Nioh: Complete Edition", output)
        self.assertIn("仁王 Complete Edition", output)
        self.assertIn("steam_store", output)

    def test_format_games_table_includes_playtime_when_requested(self):
        game = SteamGame(
            app_id="123",
            name="Example Game",
            install_path=Path("C:/Steam/steamapps/common/ExampleGame"),
            playtime_forever_minutes=125,
        )

        output = format_games_table([game], show_playtime=True)

        self.assertIn("Playtime", output)
        self.assertIn("2h 5m", output)

    def test_format_games_json(self):
        game = SteamGame(
            app_id="123",
            name="Example Game",
            install_path=Path("C:/Steam/steamapps/common/ExampleGame"),
            install_size_bytes=1073741824,
            last_updated_at=datetime.fromtimestamp(1700000000).astimezone(),
        )

        data = json.loads(format_games_json([game]))

        self.assertEqual(data[0]["app_id"], "123")
        self.assertEqual(data[0]["install_size_bytes"], 1073741824)
        self.assertEqual(data[0]["last_updated_at"], "2023/11/15 07:13:20")
        self.assertNotIn("name_source", data[0])

    def test_format_games_json_includes_details(self):
        game = SteamGame(
            app_id="132520",
            name="仁王 Complete Edition",
            install_path=Path("C:/Steam/steamapps/common/Nioh"),
            appmanifest_name="Nioh: Complete Edition",
            steam_store_name="仁王 Complete Edition",
            name_source="steam_store",
        )

        data = json.loads(format_games_json([game], details=True))

        self.assertEqual(data[0]["appmanifest_name"], "Nioh: Complete Edition")
        self.assertEqual(data[0]["steam_store_name"], "仁王 Complete Edition")
        self.assertEqual(data[0]["name_source"], "steam_store")

    def test_format_games_json_includes_playtime_when_requested(self):
        game = SteamGame(
            app_id="123",
            name="Example Game",
            install_path=Path("C:/Steam/steamapps/common/ExampleGame"),
            playtime_forever_minutes=125,
        )

        data = json.loads(format_games_json([game], show_playtime=True))

        self.assertEqual(data[0]["playtime_forever_minutes"], 125)

    def test_format_games_csv(self):
        game = SteamGame(
            app_id="123",
            name="Example Game",
            install_path=Path("C:/Steam/steamapps/common/ExampleGame"),
            install_size_bytes=1073741824,
        )

        output = format_games_csv([game])

        self.assertIn("app_id,name,install_path,install_size_bytes,last_updated_at", output)
        self.assertIn("123,Example Game,C:\\Steam\\steamapps\\common\\ExampleGame,1073741824,", output)
        self.assertNotIn("name_source", output)

    def test_format_games_csv_includes_details(self):
        game = SteamGame(
            app_id="132520",
            name="仁王 Complete Edition",
            install_path=Path("C:/Steam/steamapps/common/Nioh"),
            appmanifest_name="Nioh: Complete Edition",
            steam_store_name="仁王 Complete Edition",
            name_source="steam_store",
        )

        output = format_games_csv([game], details=True)

        self.assertIn("appmanifest_name,steam_store_name,name_source", output)
        self.assertIn("Nioh: Complete Edition", output)
        self.assertIn("仁王 Complete Edition", output)
        self.assertIn("steam_store", output)

    def test_format_games_csv_includes_playtime_when_requested(self):
        game = SteamGame(
            app_id="123",
            name="Example Game",
            install_path=Path("C:/Steam/steamapps/common/ExampleGame"),
            playtime_forever_minutes=125,
        )

        output = format_games_csv([game], show_playtime=True)

        self.assertIn("playtime_forever_minutes", output)
        self.assertIn("125", output)


if __name__ == "__main__":
    unittest.main()
