#!/usr/bin/env python3
"""Retain older compatible versions when adding a new fork release."""
import argparse
import json
from pathlib import Path


def update(manifest, release, config):
    old = json.loads(manifest.read_text()) if manifest.exists() else []
    plugins = [x for x in old if x["guid"] != config["plugin_guid"]]
    entry = next((x for x in old if x["guid"] == config["plugin_guid"]), {})
    version = {k: release[k] for k in ["version", "changelog", "targetAbi", "sourceUrl", "checksum", "timestamp"]}
    versions = [x for x in entry.get("versions", []) if x["version"] != version["version"]]
    versions.append(version)
    versions.sort(key=lambda x: tuple(map(int, x["version"].split("."))), reverse=True)
    plugins.append({"guid": config["plugin_guid"], "name": config["plugin_name"],
                    "description": "DLNA with published HTTP URL support; independently maintained fork.",
                    "overview": "DLNA published URL", "owner": config["repository"].split("/")[0],
                    "category": "General", "versions": versions})
    manifest.write_text(json.dumps(plugins, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    cfg = json.loads((Path(__file__).parent / "config.json").read_text())
    update(args.manifest, json.loads(args.release.read_text()), cfg)
