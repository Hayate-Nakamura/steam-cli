import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steam_cli.cache import get_cache_status


class CacheTest(unittest.TestCase):
    def test_get_cache_status_reports_missing_cache(self):
        with TemporaryDirectory() as temp_dir:
            status = get_cache_status(Path(temp_dir) / "missing.json", ttl_seconds=10, now=100)

        self.assertFalse(status.exists)
        self.assertEqual(status.entry_count, 0)

    def test_get_cache_status_counts_fresh_and_expired_entries(self):
        with TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache.json"
            cache_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "entries": {
                            "fresh": {"fetched_at": 95},
                            "expired": {"fetched_at": 80},
                        },
                    }
                ),
                encoding="utf-8",
            )

            status = get_cache_status(cache_path, ttl_seconds=10, now=100)

        self.assertTrue(status.exists)
        self.assertEqual(status.entry_count, 2)
        self.assertEqual(status.fresh_count, 1)
        self.assertEqual(status.expired_count, 1)


if __name__ == "__main__":
    unittest.main()
