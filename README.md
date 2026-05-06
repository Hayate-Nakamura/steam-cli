# steam-cli

## 日本語

Windows上にインストールされているSteamゲームを確認するための軽量CLIです。

### 現在のスコープ

- WindowsレジストリからSteamのインストールパスを検出します。
- `steamapps/libraryfolders.vdf` を読み取ります。
- `appmanifest_*.acf` からインストール済みゲーム情報を解析します。
- Steam Store APIからSteamの言語設定に合わせたゲーム名を取得します。
- Steam Store APIで取得したゲーム名は7日間キャッシュし、不要なリクエストを避けます。
- Steam Store APIでゲーム名を取得できない場合は、`appmanifest_*.acf` の `name` を使用します。
- `list` コマンドでAppID、ゲーム名、インストールサイズ、最終更新日時、インストールパスを表示します。
- `list --json` と `list --csv` で標準出力へ出力できます。
- `export --csv` でCSVファイルを書き出せます。
- `--details` を指定すると、`appmanifest_*.acf` の `name`、Steam Store APIで取得したゲーム名、`name_source` を追加で出力します。

実行時の依存関係は、意図的にPython標準ライブラリのみに限定しています。

### 使い方

```powershell
steam-cli list
```

JSONまたはCSVとして標準出力へ表示できます。

```powershell
steam-cli list --json
steam-cli list --csv
```

CSVファイルとして書き出せます。

```powershell
steam-cli export --csv games.csv
```

詳細情報を含める場合は `--details` を指定します。

```powershell
steam-cli list --details
steam-cli list --json --details
steam-cli export --csv games.csv --details
```

ゲーム名の取得に使うSteam Store APIの言語は、OSのロケールから自動判定します。<br>
明示的に言語を指定したい場合はSteamworksの[API language code](https://partner.steamgames.com/doc/store/localization/languages)を指定できます。

```powershell
steam-cli --language japanese list
```

Steam Store APIから取得したゲーム名は、言語とAppIDごとに7日間キャッシュされます。キャッシュが有効な間はSteam Store APIを呼び直さず、期限切れまたは未取得のゲーム名だけを再取得します。

開発中またはテスト時は、Steamのインストールパスを直接指定できます。

```powershell
python -m steam_cli --steam-path "C:\Program Files (x86)\Steam" list
```

### ロードマップ

- フェーズ2: `--json`, `--csv`, インストールサイズ、最終更新日時 -> 完了
- フェーズ3: Steam Web API連携、プレイ時間、未プレイゲーム抽出。
- フェーズ4: HDD / SSDへの配置提案。
- フェーズ5: GUI、Web UI、自動整理ツール。

### バージョン管理

このプロジェクトは[Semantic Versioning](https://semver.org/)をベースにします。

- `MAJOR`: 互換性のないCLI仕様変更。
- `MINOR`: 新しいコマンド、オプション、出力項目などの後方互換な機能追加。
- `PATCH`: バグ修正、ドキュメント修正、内部実装の改善。

初期開発中は `0.x.y` とし、フェーズ単位の機能追加では `MINOR` を上げます。
現在のバージョンは `0.2.0` です。

## English

A lightweight CLI for inspecting installed Steam games on Windows.

### Current Scope

- Detect the Steam installation path from the Windows registry.
- Read `steamapps/libraryfolders.vdf`.
- Parse installed game manifests from `appmanifest_*.acf`.
- Fetch localized game names from the Steam Store API.
- Cache game names fetched from the Steam Store API for 7 days to avoid unnecessary requests.
- Use the `name` value from `appmanifest_*.acf` when the Steam Store API cannot return a game name.
- Show each game's AppID, game name, install size, last updated time, and install path with the `list` command.
- Print to stdout with `list --json` and `list --csv`.
- Write a CSV file with `export --csv`.
- Add the `name` value from `appmanifest_*.acf`, the game name from the Steam Store API, and `name_source` when `--details` is specified.

Runtime dependencies are intentionally limited to the Python standard library.

### Usage

```powershell
steam-cli list
```

Print as JSON or CSV:

```powershell
steam-cli list --json
steam-cli list --csv
```

Export to a CSV file:

```powershell
steam-cli export --csv games.csv
```

Include detailed fields with `--details`:

```powershell
steam-cli list --details
steam-cli list --json --details
steam-cli export --csv games.csv --details
```

The Steam Store API language is detected from the OS locale. To set it explicitly, pass a Steamworks [API language code](https://partner.steamgames.com/doc/store/localization/languages):

```powershell
steam-cli --language japanese list
```

Game names fetched from the Steam Store API are cached per language and AppID for 7 days. While the cache is fresh, steam-cli does not call the Steam Store API again and only refreshes expired or missing names.

For development or testing, pass a Steam installation path directly:

```powershell
python -m steam_cli --steam-path "C:\Program Files (x86)\Steam" list
```

### Roadmap

- Phase 2: `--json`, `--csv`, install size, last updated time -> Done
- Phase 3: Steam Web API integration, play time, unplayed games.
- Phase 4: HDD / SSD placement recommendations.
- Phase 5: GUI, Web UI, automatic organization tools.

### Versioning

This project follows [Semantic Versioning](https://semver.org/).

- `MAJOR`: Incompatible CLI changes.
- `MINOR`: Backward-compatible feature additions such as new commands, options, or output fields.
- `PATCH`: Bug fixes, documentation updates, and internal improvements.

During early development, versions use `0.x.y`. Phase-level feature additions bump `MINOR`.
The current version is `0.2.0`.
