# Maintained DLNA published-URL fork

This fork advertises `JELLYFIN_PublishedServerUrl` in SSDP LOCATION messages.
It keeps the original interface address for local sockets. If that environment
variable is blank, normal upstream interface-based advertising is retained.
Use an HTTP address reachable by the DLNA clients.

The fork has its own stable plugin GUID and the display name **DLNA (Published
URL)**. Normal DLNA catalog updates therefore cannot overwrite it. Install only
one of the original DLNA plugin or this fork, because both use the same assembly
names and implement the same DLNA service.

## Jellyfin update feed

Add this repository in Dashboard → Plugins → Repositories:

`https://raw.githubusercontent.com/akhan23wgu/jellyfin-plugin-dlna/master/manifest.json`

Keep automatic updates enabled for **DLNA (Published URL)**. Jellyfin still needs
its normal restart after plugin updates. The feed retains older versions and
sets the minimum server ABI to the Jellyfin version actually used for compilation.

## Automatic upstream updates

`Maintain patched DLNA releases` checks the latest official stable upstream
release every day, on relevant maintenance commits, and when run manually.
It checks out that exact tag, applies the URL patch and fork identity, determines
the required .NET SDK, runs the safety tests, and builds a Release package.
A separate publishing job then publishes the ZIP, checksums, and matching source
and updates `manifest.json`. The build job has read-only repository permissions;
only the publisher can write releases and the catalog.

If upstream code changes so the patch no longer matches, or compilation/tests
fail, no new package or catalog entry is published. The last working release
stays available. Review the failed Actions run, adapt `apply_patch.py`, increment
`patch_revision` in `config.json`, test, and commit. Increment that revision for
any change that needs a new package of an already-published upstream release.

GitHub can disable scheduled workflows after 60 days without repository activity.
Check Actions occasionally and re-enable the workflow if GitHub has disabled it.
Do not enable the archived upstream workflows; this fork uses only its own
maintenance workflow for publishing.

## Build manually

Check out an official upstream tag into a separate directory, install its required
.NET SDK, and run from the fork root:

```sh
UPSTREAM_SOURCE=/path/to/upstream python3 -m unittest discover -s maintenance -p 'test_*.py' -v
python3 maintenance/build_release.py /path/to/upstream release-output --upstream-tag v14
```

The source checkout is patched in place. Build output includes `release.json`,
the installable ZIP, `meta.json` for manual installation, SHA256SUMS, and the
matching GPL source archive. The upstream license is retained.
