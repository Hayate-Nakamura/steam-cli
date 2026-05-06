import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.scanner import find_installed_games, find_libraries


class ScannerTest(unittest.TestCase):
    def test_find_libraries_reads_libraryfolders(self):
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            steam_path = tmp_path / "Steam"
            second_library = tmp_path / "Library"
            steamapps = steam_path / "steamapps"
            steamapps.mkdir(parents=True)
            second_library.mkdir()
            (steamapps / "libraryfolders.vdf").write_text(
                f'''
                "libraryfolders"
                {{
                    "0" {{ "path" "{steam_path}" }}
                    "1" {{ "path" "{second_library}" }}
                }}
                ''',
                encoding="utf-8",
            )

            self.assertEqual(
                [library.path for library in find_libraries(steam_path)],
                [steam_path, second_library],
            )

    def test_find_installed_games_reads_appmanifests(self):
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            steam_path = tmp_path / "Steam"
            steamapps = steam_path / "steamapps"
            steamapps.mkdir(parents=True)
            (steamapps / "appmanifest_123.acf").write_text(
                '''
                "AppState"
                {
                    "appid" "123"
                    "name" "Example Game"
                    "installdir" "ExampleGame"
                    "SizeOnDisk" "1073741824"
                    "LastUpdated" "1700000000"
                }
                ''',
                encoding="utf-8",
            )

            games = find_installed_games(steam_path)

            self.assertEqual(len(games), 1)
            self.assertEqual(games[0].app_id, "123")
            self.assertEqual(games[0].name, "Example Game")
            self.assertEqual(games[0].install_path, Path(steamapps / "common" / "ExampleGame"))
            self.assertEqual(games[0].install_size_bytes, 1073741824)
            self.assertEqual(int(games[0].last_updated_at.timestamp()), 1700000000)
            self.assertEqual(games[0].appmanifest_name, "Example Game")
            self.assertEqual(games[0].steam_store_name, None)
            self.assertEqual(games[0].name_source, "appmanifest")


if __name__ == "__main__":
    unittest.main()
