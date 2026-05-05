import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.parser import parse_key_values


class ParseKeyValuesTest(unittest.TestCase):
    def test_parse_appmanifest_acf(self):
        data = parse_key_values(
            '''
            "AppState"
            {
                "appid" "123"
                "name" "Example Game"
                "installdir" "ExampleGame"
            }
            '''
        )

        self.assertEqual(
            data,
            {
                "AppState": {
                    "appid": "123",
                    "name": "Example Game",
                    "installdir": "ExampleGame",
                }
            },
        )

    def test_parse_libraryfolders_vdf(self):
        data = parse_key_values(
            r'''
            "libraryfolders"
            {
                "0"
                {
                    "path" "C:\\Program Files (x86)\\Steam"
                }
                "1"
                {
                    "path" "D:\\SteamLibrary"
                }
            }
            '''
        )

        self.assertEqual(data["libraryfolders"]["1"]["path"], "D:\\SteamLibrary")


if __name__ == "__main__":
    unittest.main()
