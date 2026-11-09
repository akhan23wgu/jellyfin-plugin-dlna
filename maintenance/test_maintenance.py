import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from apply_patch import apply, CONFIG
from update_manifest import update


class UpgradeSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        upstream = Path(os.environ["UPSTREAM_SOURCE"])
        for relative in ["src/Jellyfin.Plugin.Dlna/Main/DlnaHost.cs", "src/Jellyfin.Plugin.Dlna/DlnaPlugin.cs", "build.yaml"]:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(upstream / relative, target)

    def tearDown(self):
        self.temp.cleanup()

    def test_upstream_drift_does_not_partially_change_the_publisher(self):
        plugin = self.root / "src/Jellyfin.Plugin.Dlna/DlnaPlugin.cs"
        plugin.write_text("// Incompatible upstream identity layout\n")
        host = self.root / "src/Jellyfin.Plugin.Dlna/Main/DlnaHost.cs"
        original = host.read_bytes()
        with self.assertRaises(ValueError):
            apply(self.root)
        self.assertEqual(host.read_bytes(), original)

    def test_catalog_keeps_an_older_server_compatible_version(self):
        manifest = self.root / "manifest.json"
        old = {"version": "14.0.0.1", "targetAbi": "12.4.0.0", "sourceUrl": "https://example.com/old.zip"}
        manifest.write_text(json.dumps([{"guid": CONFIG["plugin_guid"], "versions": [old]}]))
        release = {"version": "15.0.0.1", "targetAbi": "13.0.0.0", "sourceUrl": "https://example.com/new.zip",
                   "checksum": "a" * 32, "changelog": "New upstream", "timestamp": "2026-11-09T00:00:00Z"}
        update(manifest, release, CONFIG)
        versions = json.loads(manifest.read_text())[0]["versions"]
        self.assertEqual([x["version"] for x in versions], ["15.0.0.1", "14.0.0.1"])
        update(manifest, release, CONFIG)
        self.assertEqual(len(json.loads(manifest.read_text())[0]["versions"]), 2)


if __name__ == "__main__":
    unittest.main()
