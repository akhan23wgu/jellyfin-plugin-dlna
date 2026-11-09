#!/usr/bin/env python3
"""Build one official release with our patch and produce a Jellyfin package."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile
from apply_patch import apply

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config.json").read_text())
ARTIFACTS = ["Jellyfin.Plugin.Dlna.dll", "Jellyfin.Plugin.Dlna.Model.dll",
             "Jellyfin.Plugin.Dlna.Playback.dll", "Rssdp.dll"]


def build(source, output, upstream_tag, dotnet="dotnet"):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not re.fullmatch(r"v?\d+(?:\.\d+)*", upstream_tag):
        raise ValueError("Unsupported upstream release tag")
    apply(source)
    spec = (source / "build.yaml").read_text()
    match = re.search(r'^version:\s*["\x27]?([\d.]+)', spec, re.M)
    if not match:
        raise ValueError("Cannot determine upstream plugin version")
    numbers = [int(x) for x in match.group(1).split(".")]
    numbers += [0] * (4 - len(numbers))
    if len(numbers) != 4:
        raise ValueError("Unsupported plugin version")
    numbers[-1] += CONFIG["patch_revision"]
    version = ".".join(map(str, numbers))
    output.mkdir(parents=True, exist_ok=True)
    publish = output / "publish"
    project = source / "src/Jellyfin.Plugin.Dlna/Jellyfin.Plugin.Dlna.csproj"
    subprocess.run([dotnet, "publish", str(project), "-c", "Release", "-o", str(publish),
                    f"-p:Version={version}", f"-p:AssemblyVersion={version}",
                    f"-p:FileVersion={version}"], check=True)
    assets = json.loads((project.parent / "obj/project.assets.json").read_text())
    controller = [x.split("/", 1)[1] for x in assets["libraries"]
                  if x.startswith("Jellyfin.Controller/")]
    if len(controller) != 1 or not re.fullmatch(r"\d+\.\d+\.\d+(?:\.\d+)?", controller[0]):
        raise ValueError("Build must resolve one stable Jellyfin Controller version")
    abi_parts = controller[0].split(".")
    target_abi = ".".join(abi_parts + ["0"] * (4 - len(abi_parts)))
    package = output / f"dlna-published-url_{version}.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ARTIFACTS:
            file = publish / name
            if not file.is_file() or file.stat().st_size == 0:
                raise ValueError(f"Missing build artifact: {name}")
            archive.write(file, name)
        archive.write(source / "LICENSE", "LICENSE")
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    release_tag = f"published-url-{upstream_tag}-r{CONFIG['patch_revision']}"
    data = {"version": version, "tag": release_tag, "upstream_tag": upstream_tag,
            "upstream_commit": commit, "targetAbi": target_abi,
            "package": package.name, "checksum": hashlib.md5(package.read_bytes()).hexdigest(),
            "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "guid": CONFIG["plugin_guid"], "name": CONFIG["plugin_name"],
            "sourceUrl": f"https://github.com/{CONFIG['repository']}/releases/download/{release_tag}/{package.name}",
            "changelog": f"Official {upstream_tag} with published-URL discovery fix; independent plugin identity."}
    (output / "release.json").write_text(json.dumps(data, indent=2) + "\n")
    meta = {k: data[k] for k in ["guid", "name", "version", "targetAbi", "timestamp", "changelog"]}
    meta.update({"category": "General", "owner": CONFIG["repository"].split("/")[0],
                 "description": "DLNA with configurable advertised HTTP URL.",
                 "overview": "DLNA published URL", "autoUpdate": True,
                 "status": "Active", "assemblies": []})
    (output / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    with tarfile.open(output / "source-patched.tar.gz", "w:gz") as archive:
        tracked = subprocess.check_output(["git", "-C", str(source), "ls-files", "-z"]).decode().split("\0")
        for name in tracked:
            if name:
                archive.add(source / name, arcname="dlna-source/" + name)
    (output / "SHA256SUMS").write_text(data["sha256"] + "  " + package.name + "\n")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--upstream-tag", required=True)
    parser.add_argument("--dotnet", default="dotnet")
    args = parser.parse_args()
    build(args.source, args.output, args.upstream_tag, args.dotnet)
