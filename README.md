# steam-cli

## 日本語

Windows上にインストールされているSteamゲームを確認するための軽量CLIです。

Steamライブラリをローカルから読み取り、Steam Store APIでローカライズされたゲーム名を取得し、必要に応じてSteam Web APIから総プレイ時間も取得します。

実行時の依存関係は、意図的にPython標準ライブラリのみに限定しています。

### 機能

- WindowsレジストリからSteamのインストールパスを検出します。
- `steamapps/libraryfolders.vdf` を読み取り、Steamライブラリを検出します。
- `steamapps/appmanifest_*.acf` からインストール済みゲーム情報を解析します。
- Steam Store APIからSteamの言語設定に合わせたゲーム名を取得します。
- Steam Web APIから総プレイ時間を取得します。
- JSON / CSV / テーブル形式で出力できます。
- プレイ時間でゲームを抽出できます。

### 必要条件

| 項目              | 内容                                               |
| ----------------- | -------------------------------------------------- |
| OS                | Windows                                            |
| Python            | 3.11以上                                           |
| Steam             | インストール済みであること                         |
| Steam Web API key | 総プレイ時間とプレイ時間フィルタを使う場合のみ必要 |

### インストール

開発中のローカル環境では、リポジトリ直下で次のようにインストールできます。

```powershell
python -m pip install -e .
```

インストール後、`steam-cli` コマンドを実行できます。

```powershell
steam-cli list
```

インストール後は、モジュールとして実行することもできます。

```powershell
python -m steam_cli list
```

### コマンド一覧

| コマンド           | 用途                                                             |
| ------------------ | ---------------------------------------------------------------- |
| `steam-cli list`   | インストール済みゲームを表示します。                             |
| `steam-cli export` | インストール済みゲームをファイルへ書き出します。                 |
| `steam-cli filter` | 条件に合うゲームだけを表示します。                               |
| `steam-cli config` | SteamID64、Steam Web API key、言語設定を保存・確認・削除します。 |

### 基本的な使い方

```powershell
steam-cli list
steam-cli list --json
steam-cli list --csv
steam-cli export --csv games.csv
steam-cli export --json games.json
```

<details>
<summary>コマンドと出力例</summary>

**テーブル形式**

**コマンド**

```powershell
steam-cli list
```

**出力**

```text
AppID   Name                  Size    Last Updated         Install Path
132520  仁王 Complete Edition  70.4 GB 2024/01/15 21:30:05 C:\Program Files (x86)\Steam\steamapps\common\Nioh
```

**JSON形式**

**コマンド**

```powershell
steam-cli list --json
```

**出力**

```json
[
	{
		"app_id": "132520",
		"name": "仁王 Complete Edition",
		"install_path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Nioh",
		"install_size_bytes": 75691499520,
		"last_updated_at": "2024/01/15 21:30:05"
	}
]
```

</details>

詳細情報を含める場合は `--details` を指定します。

```powershell
steam-cli list --details
steam-cli list --json --details
steam-cli export --csv games.csv --details
steam-cli export --json games.json --details
```

<details>
<summary>コマンドと出力例</summary>

**詳細テーブル形式**

**コマンド**

```powershell
steam-cli list --details
```

**出力**

```text
AppID   Name                  Size     Last Updated         Install Path                                      AppManifest Name       Steam Store Name        Name Source
132520  仁王 Complete Edition  70.4 GB  2024/01/15 21:30:05 C:\Program Files (x86)\Steam\steamapps\common\Nioh  Nioh: Complete Edition  仁王 Complete Edition  steam_store
```

**詳細JSON形式**

**コマンド**

```powershell
steam-cli list --json --details
```

**出力**

```json
[
	{
		"app_id": "132520",
		"name": "仁王 Complete Edition",
		"install_path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Nioh",
		"install_size_bytes": 75691499520,
		"last_updated_at": "2024/01/15 21:30:05",
		"appmanifest_name": "Nioh: Complete Edition",
		"steam_store_name": "仁王 Complete Edition",
		"name_source": "steam_store"
	}
]
```

</details>

開発中またはテスト時は、Steamのインストールパスを直接指定できます。

```powershell
python -m steam_cli --steam-path "C:\Program Files (x86)\Steam" list
```

### 設定

総プレイ時間やプレイ時間フィルタのために、SteamID64、Steam Web API key、任意の言語設定を保存できます。

```powershell
steam-cli config
```

入力後、Steam Web APIへ簡易的な確認リクエストを送り、問題がなければ設定ファイルへ保存します。

コマンドラインから値を渡して保存することもできます。

```powershell
steam-cli config --steam-id 76561198000000000 --web-api-key YOUR_KEY
steam-cli config --language japanese
```

設定状態とSteam Web APIでの妥当性確認結果を確認できます。Steam Web API keyの値は表示されません。

```powershell
steam-cli config --status
```

<details>
<summary>コマンドと出力例</summary>

**設定状態**

**コマンド**

```powershell
steam-cli config --status
```

**出力**

```text
Config file: C:\Users\you\AppData\Local\steam-cli\config.json
SteamID64: configured (config file)
Steam Web API key: configured (config file)
Language: japanese (config file)
Steam Store name cache: 120 entries, 118 fresh, 2 expired (C:\Users\you\AppData\Local\steam-cli\store_names.json)
Steam Web API playtime cache: 1 entries, 1 fresh, 0 expired (C:\Users\you\AppData\Local\steam-cli\webapi_playtime.json)
Steam Web API validation: OK
```

</details>

保存した設定を削除できます。

```powershell
steam-cli config --reset
steam-cli config --reset --yes
```

SteamID64とSteam Web API keyは環境変数でも指定できます。

```powershell
$env:STEAM_ID="76561198000000000"
$env:STEAM_WEB_API_KEY="YOUR_KEY"
steam-cli list --with-playtime
```

### プレイ時間とフィルタ

総プレイ時間を表示できます。

```powershell
steam-cli list --with-playtime
steam-cli list --with-playtime --refresh
```

プレイ時間でゲームを抽出できます。

```powershell
steam-cli filter --unplayed
steam-cli filter --played
steam-cli filter --min-playtime 60
steam-cli filter --max-playtime 120
steam-cli filter --played --min-playtime 60 --max-playtime 120
steam-cli filter --unplayed --json
steam-cli filter --unplayed --csv
steam-cli filter --unplayed --refresh
```

ゲーム情報でも抽出できます。

```powershell
steam-cli filter --app-id 132520
steam-cli filter --name "仁王|Nioh"
steam-cli filter --install-path "Steam\\steamapps\\common"
steam-cli filter --name "edition" --install-path "Steam"
```

並び替えと集計もできます。

```powershell
steam-cli list --sort size --desc
steam-cli list --sort last-updated --desc
steam-cli list --sort playtime --desc
steam-cli list --summary
steam-cli filter --played --sort playtime --desc --summary
```

`--refresh` を指定すると、総プレイ時間キャッシュを無視して最新情報を取得します。

<details>
<summary>コマンドと出力例</summary>

**総プレイ時間**

**コマンド**

```powershell
steam-cli list --with-playtime
```

**出力**

```text
AppID   Name                  Playtime  Size     Last Updated         Install Path
132520  仁王 Complete Edition  12h 35m   70.4 GB  2024/01/15 21:30:05 C:\Program Files (x86)\Steam\steamapps\common\Nioh
```

**プレイ時間フィルタ**

**コマンド**

```powershell
steam-cli filter --played --min-playtime 60 --max-playtime 180
```

**出力**

```text
AppID   Name                  Playtime  Size     Last Updated         Install Path
132520  仁王 Complete Edition  2h 5m     70.4 GB  2024/01/15 21:30:05 C:\Program Files (x86)\Steam\steamapps\common\Nioh
```

</details>

プレイ時間フィルタの挙動:

- `filter --unplayed` は、総プレイ時間が0分のゲームだけを表示します。
- `filter --played` は、総プレイ時間が1分以上のゲームだけを表示します。
- `--min-playtime` と `--max-playtime` は分単位で指定し、境界値を含めて判定します。
- プレイ時間を確認できないゲームは含めません。

ゲーム情報フィルタの挙動:

- `--app-id` はSteam AppIDを完全一致で判定します。
- `--name` は表示名を正規表現で検索します。
- `--install-path` はインストールパスを正規表現で検索します。
- 複数のフィルタを指定した場合は、すべての条件に一致するゲームだけを表示します。
- プレイ時間条件を指定しない場合、Steam Web API keyは不要です。

並び替えと集計の挙動:

- `--sort` は `name`, `size`, `last-updated`, `playtime` を指定できます。
- `--desc` を指定すると降順で並び替えます。
- サイズ、最終更新日時、総プレイ時間が不明なゲームは末尾に表示します。
- `--sort playtime` は総プレイ時間を取得するため、Steam Web API keyが必要です。
- `--summary` はゲーム数、合計インストールサイズ、ライブラリ別の件数と容量を表示します。
- `--summary` は `--json` / `--csv` と同時には使えません。

### 出力項目

| 項目                       | 内容                                                                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `app_id`                   | Steam AppIDです。                                                                                                                          |
| `name`                     | 表示に使うゲーム名です。Steam Store APIで取得できた場合はローカライズ名、取得できない場合は `steamapps/appmanifest_*.acf` の `name` です。 |
| `install_path`             | インストール先パスです。                                                                                                                   |
| `install_size_bytes`       | インストールサイズのバイト数です。                                                                                                         |
| `last_updated_at`          | 最終更新日時です。タイムゾーンは含みません。                                                                                               |
| `playtime_forever_minutes` | 総プレイ時間の分数です。`--with-playtime` または `filter` のプレイ時間条件で出力されます。                                                 |
| `appmanifest_name`         | `steamapps/appmanifest_*.acf` に記録されている `name` です。`--details` で出力されます。                                                   |
| `steam_store_name`         | Steam Store APIで取得したゲーム名です。`--details` で出力されます。                                                                        |
| `name_source`              | `name` の由来です。`steam_store` または `appmanifest` です。`--details` で出力されます。                                                   |

### 設定とキャッシュ

| 種類                         | 場所                                            | 内容                                                                                                  |
| ---------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| 設定ファイル                 | `%LOCALAPPDATA%\steam-cli\config.json`          | SteamID64、Steam Web API key、言語設定を保存します。WindowsではSteam Web API keyをDPAPIで保護します。 |
| Steam Store name cache       | `%LOCALAPPDATA%\steam-cli\store_names.json`     | Steam Store APIで取得したゲーム名を、言語とAppIDごとに7日間キャッシュします。                         |
| Steam Web API playtime cache | `%LOCALAPPDATA%\steam-cli\webapi_playtime.json` | Steam Web APIから取得した総プレイ時間を、SteamIDごとに6時間キャッシュします。                         |

SteamID64とSteam Web API keyの優先順位は、コマンドラインオプション、環境変数、設定ファイルの順です。

言語設定の優先順位は、コマンドラインオプション、`STEAM_CLI_LANGUAGE` 環境変数、設定ファイル、OSロケールの順です。

Windowsでは、設定ファイルへ保存するSteam Web API keyをDPAPIで現在のWindowsユーザーに紐づけて保護します。古い平文の設定ファイルも読み込めますが、次に `steam-cli config` で保存すると保護済み形式へ更新されます。

Steam Web API keyは秘密情報として扱い、共有しないでください。

### SteamID64とSteam Web API key

SteamID64はSteamプロフィールURLから確認できます。

プロフィールURLが `https://steamcommunity.com/profiles/76561198000000000` のような形式の場合、`profiles/` の後ろにある17桁の数値がSteamID64です。カスタムURLを使っている場合は、SteamID変換ツールなどでSteamID64を確認してください。

Steam Web API keyはSteam Communityの[Steam Web API Key登録ページ](https://steamcommunity.com/dev/apikey)で取得できます。取得にはSteamアカウントでのサインインと、Steam Web API Terms of Useへの同意が必要です。

### 言語

ゲーム名の取得に使うSteam Store APIの言語は、OSのロケールから自動判定します。

明示的に言語を指定したい場合はSteamworksの[API language code](https://partner.steamgames.com/doc/store/localization/languages)を指定できます。

```powershell
steam-cli --language japanese list
steam-cli config --language japanese
```

Steam Store APIでゲーム名を取得できない場合は、`steamapps/appmanifest_*.acf` の `name` を使用します。

### 制限事項

- SteamがWindowsにインストールされている環境を対象にしています。
- Steam Store APIでローカライズ名を取得できないゲームでは、`steamapps/appmanifest_*.acf` の `name` を使用します。
- 非公開プロフィールやSteam Web APIから取得できない情報がある場合、総プレイ時間を確認できないことがあります。
- `filter` のプレイ時間条件は、総プレイ時間を確認できたゲームだけを対象にします。

### ロードマップ

方針は、CLIを読み取り専用の信頼できる分析ツールとして固めてから、配置提案やUIに進めることです。自動整理のようなファイル移動を伴う機能は、提案内容を十分に検証できるようになってから扱います。

ロードマップは、実装の目的がわかるように分類して管理します。

| 目的分類           | 内容                                                                           |
| ------------------ | ------------------------------------------------------------------------------ |
| 機能追加           | 新しいコマンド、オプション、出力項目、分析軸を追加します。                     |
| バグフィックス     | 既存機能の不具合、例外、誤った出力、環境差による失敗を修正します。             |
| ユーザー体験の向上 | 導入、配布、表示、操作、エラーメッセージ、ドキュメントを改善します。           |
| 安全性の向上       | ファイル移動や外部操作を伴う機能で、ドライラン、確認、リスク低減を整備します。 |

| フェーズ    | ステータス | 目的分類           | 内容                                                                                                                                                                                                                          |
| ----------- | ---------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| フェーズ3   | 完了       | 機能追加           | Steam Web API連携、総プレイ時間、未プレイゲーム抽出を追加しました。                                                                                                                                                           |
| フェーズ3.5 | 完了       | 機能追加           | フィルタを拡張しました。`filter --app-id`, `filter --name`, `filter --install-path`, `filter --played`, `filter --min-playtime`, `filter --max-playtime` を追加し、未取得のプレイ時間を結果から除外する条件を明確にしました。 |
| フェーズ3.6 | 完了       | 機能追加           | 並び替えと集計を追加しました。`list` と `filter` で名前、サイズ、最終更新日時、総プレイ時間順に並び替え、ゲーム数、合計インストールサイズ、ライブラリ別の件数と容量を確認できます。                                           |
| フェーズ3.7 | 未着手     | ユーザー体験の向上 | Windows向け配布を整備します。単体exeのビルド手順、バージョン表示、リリース成果物の命名を追加します。                                                                                                                          |
| フェーズ4   | 未着手     | 機能追加           | ストレージ分析を追加します。ライブラリごとの空き容量、ゲームサイズ、プレイ状況を組み合わせ、HDD / SSD配置を判断するためのレポートを出します。                                                                                 |
| フェーズ4.5 | 未着手     | 機能追加           | 配置提案を追加します。移動候補、移動後の容量見込み、優先度を表示します。実際の移動は行いません。                                                                                                                              |
| フェーズ5   | 未着手     | 安全性の向上       | 安全な操作支援を検討します。Steamの仕様に沿った移動手順の案内、ドライラン、確認プロンプトを前提にします。                                                                                                                     |
| フェーズ6   | 未着手     | ユーザー体験の向上 | GUI / Web UIを検討します。CLIの出力と判断ロジックが安定してから、可視化や操作画面を追加します。                                                                                                                               |

設計中の項目:

実装可否やフェーズをすぐに決めないアイデアは、ここに記録して検討を継続します。

| 機能名                           | 機能概要                                                        | 検討中の項目                                                                                       |
| -------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| インストール済みゲームの起動支援 | インストール済みゲームをSteam経由で起動できるようにする案です。 | 読み取り中心の分析ツールという本質との整合性、コマンド仕様、フェーズへの組み込み可否を検討します。 |

### バージョン管理

このプロジェクトは[Semantic Versioning](https://semver.org/)をベースにします。

| 種類    | 内容                                                           |
| ------- | -------------------------------------------------------------- |
| `MAJOR` | 互換性のないCLI仕様変更。                                      |
| `MINOR` | 新しいコマンド、オプション、出力項目などの後方互換な機能追加。 |
| `PATCH` | バグ修正、ドキュメント修正、内部実装の改善。                   |

初期開発中は `0.x.y` とし、フェーズ単位の機能追加では `MINOR` を上げます。

現在のバージョンは `0.4.0` です。

## English

A lightweight CLI for inspecting installed Steam games on Windows.

steam-cli reads local Steam libraries, fetches localized game names from the Steam Store API, and can fetch total playtime from the Steam Web API when needed.

Runtime dependencies are intentionally limited to the Python standard library.

### Features

- Detect the Steam installation path from the Windows registry.
- Read `steamapps/libraryfolders.vdf` and detect Steam libraries.
- Parse installed game information from `steamapps/appmanifest_*.acf`.
- Fetch localized game names from the Steam Store API.
- Fetch total playtime from the Steam Web API.
- Output as table, JSON, or CSV.
- Filter games by playtime.

### Requirements

| Item              | Requirement                                           |
| ----------------- | ----------------------------------------------------- |
| OS                | Windows                                               |
| Python            | 3.11 or later                                         |
| Steam             | Installed                                             |
| Steam Web API key | Required only for total playtime and playtime filters |

### Installation

For local development, install the project from the repository root:

```powershell
python -m pip install -e .
```

After installation, run the `steam-cli` command:

```powershell
steam-cli list
```

After installation, you can also run it as a module:

```powershell
python -m steam_cli list
```

### Commands

| Command            | Purpose                                                                       |
| ------------------ | ----------------------------------------------------------------------------- |
| `steam-cli list`   | Show installed games.                                                         |
| `steam-cli export` | Export installed games to a file.                                             |
| `steam-cli filter` | Show games matching a filter.                                                 |
| `steam-cli config` | Save, inspect, or remove SteamID64, Steam Web API key, and language settings. |

### Basic Usage

```powershell
steam-cli list
steam-cli list --json
steam-cli list --csv
steam-cli export --csv games.csv
steam-cli export --json games.json
```

<details>
<summary>Commands and outputs</summary>

**Table output**

**Command**

```powershell
steam-cli list
```

**Output**

```text
AppID   Name                  Size    Last Updated         Install Path
132520  仁王 Complete Edition  70.4 GB 2024/01/15 21:30:05 C:\Program Files (x86)\Steam\steamapps\common\Nioh
```

**JSON output**

**Command**

```powershell
steam-cli list --json
```

**Output**

```json
[
	{
		"app_id": "132520",
		"name": "仁王 Complete Edition",
		"install_path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Nioh",
		"install_size_bytes": 75691499520,
		"last_updated_at": "2024/01/15 21:30:05"
	}
]
```

</details>

Include detailed fields with `--details`:

```powershell
steam-cli list --details
steam-cli list --json --details
steam-cli export --csv games.csv --details
steam-cli export --json games.json --details
```

<details>
<summary>Commands and outputs</summary>

**Detailed table output**

**Command**

```powershell
steam-cli list --details
```

**Output**

```text
AppID   Name                  Size     Last Updated         Install Path                                      AppManifest Name       Steam Store Name        Name Source
132520  仁王 Complete Edition  70.4 GB  2024/01/15 21:30:05 C:\Program Files (x86)\Steam\steamapps\common\Nioh  Nioh: Complete Edition  仁王 Complete Edition  steam_store
```

**Detailed JSON output**

**Command**

```powershell
steam-cli list --json --details
```

**Output**

```json
[
	{
		"app_id": "132520",
		"name": "仁王 Complete Edition",
		"install_path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Nioh",
		"install_size_bytes": 75691499520,
		"last_updated_at": "2024/01/15 21:30:05",
		"appmanifest_name": "Nioh: Complete Edition",
		"steam_store_name": "仁王 Complete Edition",
		"name_source": "steam_store"
	}
]
```

</details>

For development or testing, pass a Steam installation path directly:

```powershell
python -m steam_cli --steam-path "C:\Program Files (x86)\Steam" list
```

### Configuration

Save SteamID64, the Steam Web API key, and an optional language setting for total playtime and playtime filters.

```powershell
steam-cli config
```

After input, steam-cli sends a lightweight validation request to the Steam Web API and saves the settings only when validation succeeds.

You can also pass values directly:

```powershell
steam-cli config --steam-id 76561198000000000 --web-api-key YOUR_KEY
steam-cli config --language japanese
```

Show configuration status and Steam Web API validation results. The Steam Web API key value is not printed.

```powershell
steam-cli config --status
```

<details>
<summary>Command and output</summary>

**Configuration status**

**Command**

```powershell
steam-cli config --status
```

**Output**

```text
Config file: C:\Users\you\AppData\Local\steam-cli\config.json
SteamID64: configured (config file)
Steam Web API key: configured (config file)
Language: japanese (config file)
Steam Store name cache: 120 entries, 118 fresh, 2 expired (C:\Users\you\AppData\Local\steam-cli\store_names.json)
Steam Web API playtime cache: 1 entries, 1 fresh, 0 expired (C:\Users\you\AppData\Local\steam-cli\webapi_playtime.json)
Steam Web API validation: OK
```

</details>

Remove saved settings:

```powershell
steam-cli config --reset
steam-cli config --reset --yes
```

SteamID64 and the Steam Web API key can also be provided through environment variables:

```powershell
$env:STEAM_ID="76561198000000000"
$env:STEAM_WEB_API_KEY="YOUR_KEY"
steam-cli list --with-playtime
```

### Playtime And Filters

Show total playtime:

```powershell
steam-cli list --with-playtime
steam-cli list --with-playtime --refresh
```

Filter games by playtime:

```powershell
steam-cli filter --unplayed
steam-cli filter --played
steam-cli filter --min-playtime 60
steam-cli filter --max-playtime 120
steam-cli filter --played --min-playtime 60 --max-playtime 120
steam-cli filter --unplayed --json
steam-cli filter --unplayed --csv
steam-cli filter --unplayed --refresh
```

Filter by game metadata:

```powershell
steam-cli filter --app-id 132520
steam-cli filter --name "Nioh|仁王"
steam-cli filter --install-path "Steam\\steamapps\\common"
steam-cli filter --name "edition" --install-path "Steam"
```

Sort and summarize games:

```powershell
steam-cli list --sort size --desc
steam-cli list --sort last-updated --desc
steam-cli list --sort playtime --desc
steam-cli list --summary
steam-cli filter --played --sort playtime --desc --summary
```

Pass `--refresh` to ignore the total playtime cache and fetch fresh data.

<details>
<summary>Commands and outputs</summary>

**Total playtime**

**Command**

```powershell
steam-cli list --with-playtime
```

**Output**

```text
AppID   Name                  Playtime  Size     Last Updated         Install Path
132520  仁王 Complete Edition  12h 35m   70.4 GB  2024/01/15 21:30:05 C:\Program Files (x86)\Steam\steamapps\common\Nioh
```

**Playtime filter**

**Command**

```powershell
steam-cli filter --played --min-playtime 60 --max-playtime 180
```

**Output**

```text
AppID   Name                  Playtime  Size     Last Updated         Install Path
132520  仁王 Complete Edition  2h 5m     70.4 GB  2024/01/15 21:30:05 C:\Program Files (x86)\Steam\steamapps\common\Nioh
```

</details>

Playtime filter behavior:

- `filter --unplayed` shows only games with 0 minutes of total playtime.
- `filter --played` shows only games with at least 1 minute of total playtime.
- `--min-playtime` and `--max-playtime` use minutes and include boundary values.
- Games with unknown playtime are excluded.

Game metadata filter behavior:

- `--app-id` matches Steam AppID exactly.
- `--name` searches the display name with a regular expression.
- `--install-path` searches the install path with a regular expression.
- Multiple filters are combined with AND logic.
- Steam Web API credentials are not required unless you use playtime conditions.

Sorting and summary behavior:

- `--sort` accepts `name`, `size`, `last-updated`, and `playtime`.
- Pass `--desc` to sort in descending order.
- Games with unknown size, last updated time, or total playtime are shown last.
- `--sort playtime` fetches total playtime and requires Steam Web API credentials.
- `--summary` prints game count, total install size, and per-library counts and sizes.
- `--summary` cannot be combined with `--json` or `--csv`.

### Output Fields

| Field                      | Description                                                                                                                                                      |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app_id`                   | Steam AppID.                                                                                                                                                     |
| `name`                     | Display name. If the Steam Store API returns a localized name, steam-cli uses it. Otherwise, steam-cli uses the `name` value from `steamapps/appmanifest_*.acf`. |
| `install_path`             | Installation path.                                                                                                                                               |
| `install_size_bytes`       | Installation size in bytes.                                                                                                                                      |
| `last_updated_at`          | Last updated time without timezone information.                                                                                                                  |
| `playtime_forever_minutes` | Total playtime in minutes. Printed with `--with-playtime` or `filter` playtime conditions.                                                                       |
| `appmanifest_name`         | The `name` value from `steamapps/appmanifest_*.acf`. Printed with `--details`.                                                                                   |
| `steam_store_name`         | Game name fetched from the Steam Store API. Printed with `--details`.                                                                                            |
| `name_source`              | Source of `name`: `steam_store` or `appmanifest`. Printed with `--details`.                                                                                      |

### Settings And Cache

| Type                         | Location                                        | Description                                                                                                               |
| ---------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Config file                  | `%LOCALAPPDATA%\steam-cli\config.json`          | Stores SteamID64, the Steam Web API key, and language setting. On Windows, the Steam Web API key is protected with DPAPI. |
| Steam Store name cache       | `%LOCALAPPDATA%\steam-cli\store_names.json`     | Caches game names fetched from the Steam Store API per language and AppID for 7 days.                                     |
| Steam Web API playtime cache | `%LOCALAPPDATA%\steam-cli\webapi_playtime.json` | Caches total playtime fetched from the Steam Web API per SteamID for 6 hours.                                             |

SteamID64 and the Steam Web API key are resolved in this order: command-line options, environment variables, then the config file.

Language is resolved in this order: command-line option, `STEAM_CLI_LANGUAGE` environment variable, config file, then OS locale.

On Windows, steam-cli protects the Steam Web API key saved in the config file with DPAPI for the current Windows user. Legacy plaintext config files can still be read and are rewritten in the protected format the next time you save with `steam-cli config`.

Treat the Steam Web API key as a secret and do not share it.

### SteamID64 And Steam Web API Key

You can find your SteamID64 from your Steam profile URL.

If the URL looks like `https://steamcommunity.com/profiles/76561198000000000`, the 17-digit number after `profiles/` is your SteamID64. If you use a custom profile URL, use a SteamID converter to resolve it to SteamID64.

You can get a Steam Web API key from the Steam Community [Steam Web API Key registration page](https://steamcommunity.com/dev/apikey). You need to sign in with your Steam account and agree to the Steam Web API Terms of Use.

### Language

The Steam Store API language is detected from the OS locale.

To set it explicitly, pass a Steamworks [API language code](https://partner.steamgames.com/doc/store/localization/languages):

```powershell
steam-cli --language japanese list
steam-cli config --language japanese
```

When the Steam Store API cannot return a game name, steam-cli uses the `name` value from `steamapps/appmanifest_*.acf`.

### Limitations

- steam-cli targets Windows environments where Steam is installed.
- If the Steam Store API cannot return a localized name, steam-cli uses the `name` value from `steamapps/appmanifest_*.acf`.
- Total playtime may be unavailable for private profiles or information that the Steam Web API cannot return.
- `filter` playtime conditions include only games whose total playtime could be fetched.

### Roadmap

The direction is to keep the CLI as a trustworthy read-only analysis tool first, then move into placement recommendations and UI. Features that move files, such as automatic organization, should wait until recommendations can be inspected and validated clearly.

Roadmap items are grouped by implementation purpose.

| Purpose         | Description                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------- |
| Feature         | Add new commands, options, output fields, or analysis dimensions.                               |
| Bug Fix         | Fix existing defects, exceptions, incorrect output, or environment-specific failures.           |
| User Experience | Improve installation, distribution, display, operation, error messages, or documentation.       |
| Safety          | Add dry runs, confirmations, and risk reduction for file-moving or external-operation features. |

| Phase     | Status      | Purpose         | Description                                                                                                                                                                                                                      |
| --------- | ----------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 3   | Done        | Feature         | Added Steam Web API integration, total playtime, and unplayed game filtering.                                                                                                                                                    |
| Phase 3.5 | Done        | Feature         | Expanded filters. Added `filter --app-id`, `filter --name`, `filter --install-path`, `filter --played`, `filter --min-playtime`, and `filter --max-playtime`, with clear behavior for games whose playtime could not be fetched. |
| Phase 3.6 | Done        | Feature         | Added sorting and summaries. `list` and `filter` can sort by name, size, last updated time, and total playtime, plus show game counts, total install size, and per-library counts and sizes.                                     |
| Phase 3.7 | Not Started | User Experience | Prepare Windows distribution. Add single-file exe build instructions, version output, and release artifact naming.                                                                                                               |
| Phase 4   | Not Started | Feature         | Add storage analysis. Combine library free space, game size, and play status into reports that help users reason about HDD / SSD placement.                                                                                      |
| Phase 4.5 | Not Started | Feature         | Add placement recommendations. Show move candidates, estimated space changes, and priority. Do not move files.                                                                                                                   |
| Phase 5   | Not Started | Safety          | Consider safe operation helpers. Base them on Steam-compatible move guidance, dry runs, and confirmation prompts.                                                                                                                |
| Phase 6   | Not Started | User Experience | Consider a GUI / Web UI after the CLI output and decision logic are stable.                                                                                                                                                      |

Designing:

Ideas whose feasibility or phase is not decided yet are tracked here for continued discussion.

| Feature                          | Overview                                        | Under Consideration                                                                                  |
| -------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Installed game launching helpers | Let users launch installed games through Steam. | Product fit with the read-focused analysis tool, command shape, and whether to assign it to a phase. |

### Versioning

This project follows [Semantic Versioning](https://semver.org/).

| Type    | Description                                                                            |
| ------- | -------------------------------------------------------------------------------------- |
| `MAJOR` | Incompatible CLI changes.                                                              |
| `MINOR` | Backward-compatible feature additions such as new commands, options, or output fields. |
| `PATCH` | Bug fixes, documentation updates, and internal improvements.                           |

During early development, versions use `0.x.y`. Phase-level feature additions bump `MINOR`.

The current version is `0.4.0`.
