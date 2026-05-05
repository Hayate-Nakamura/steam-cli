# steam-cli

Lightweight CLI for inspecting installed Steam games on Windows.

## Current Scope

- Detect the Steam installation path from the Windows registry.
- Read `steamapps/libraryfolders.vdf`.
- Parse installed game manifests from `appmanifest_*.acf`.
- Show each game's AppID, name, and install path with the `list` command.

Runtime dependencies are intentionally limited to the Python standard library.

## Usage

```powershell
steam-cli list
```

For development or testing, pass a Steam installation path directly:

```powershell
python -m steam_cli --steam-path "C:\Program Files (x86)\Steam" list
```

## Roadmap

- Phase 2: `--json`, `--csv`, install size, last updated time.
- Phase 3: Steam Web API integration, play time, unplayed games.
- Phase 4: HDD / SSD placement recommendations.
- Phase 5: GUI, Web UI, automatic organization tools.
