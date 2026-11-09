#!/usr/bin/env python3
"""Apply the published-URL fix and a distinct plugin identity, failing closed."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config.json").read_text())
ORIGINAL_GUID = "33EBA9CD-7DA1-4720-967F-DD7DAE7B74A1"
OLD_URI = '            var uri = new UriBuilder("http", intf.Address.ToString(), httpBindPort, descriptorUri);'
NEW_URI = '''            var publishedUrl = Environment.GetEnvironmentVariable("JELLYFIN_PublishedServerUrl");
            var uri = string.IsNullOrWhiteSpace(publishedUrl)
                ? new UriBuilder("http", intf.Address.ToString(), httpBindPort, descriptorUri)
                : new UriBuilder(publishedUrl.TrimEnd('/') + descriptorUri);'''


def replace_once(text, old, new, label):
    if new in text and old not in text:
        return text
    if text.count(old) != 1:
        raise ValueError(f"{label}: upstream source changed; refusing to publish an unverified patch")
    return text.replace(old, new, 1)


def apply(root):
    root = Path(root)
    host = root / "src/Jellyfin.Plugin.Dlna/Main/DlnaHost.cs"
    plugin = root / "src/Jellyfin.Plugin.Dlna/DlnaPlugin.cs"
    spec = root / "build.yaml"
    host_text = replace_once(host.read_text(), OLD_URI, NEW_URI, "SSDP publisher")
    plugin_text = replace_once(
        plugin.read_text(), f'new("{ORIGINAL_GUID}")',
        f'new("{CONFIG["plugin_guid"]}")', "Plugin GUID")
    plugin_text = replace_once(
        plugin_text, 'public override string Name => "DLNA";',
        f'public override string Name => "{CONFIG["plugin_name"]}";', "Plugin name")
    if "Address = intf.Address," not in host_text:
        raise ValueError("Socket address handling changed; refusing to publish")
    spec_text = replace_once(spec.read_text(), 'name: "DLNA"',
                             f'name: "{CONFIG["plugin_name"]}"', "Package name")
    spec_text = replace_once(spec_text, f'guid: "{ORIGINAL_GUID}"',
                             f'guid: "{CONFIG["plugin_guid"]}"', "Package GUID")
    # Validate every replacement before writing any source file.
    host.write_text(host_text)
    plugin.write_text(plugin_text)
    spec.write_text(spec_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    apply(parser.parse_args().source)
    print("Published URL patch and separate plugin identity applied.")
