# Changelog

## v0.4.0

### 日本語

#### 追加

- `filter --played` を追加し、総プレイ時間が1分以上のゲームを抽出できるようにしました。
- `filter --min-playtime` と `filter --max-playtime` を追加し、総プレイ時間の範囲で抽出できるようにしました。
- `filter --app-id` を追加し、Steam AppIDの完全一致で抽出できるようにしました。
- `filter --name` と `filter --install-path` を追加し、ゲーム名とインストールパスを正規表現で抽出できるようにしました。
- `list` と `filter` に `--sort` と `--desc` を追加し、名前、サイズ、最終更新日時、総プレイ時間で並び替えられるようにしました。
- `list` と `filter` に `--summary` を追加し、ゲーム数、合計インストールサイズ、ライブラリ別の件数と容量を表示できるようにしました。
- `steam-cli --version` を追加し、CLIから現在のバージョンを確認できるようにしました。
- Windows向け単体exeのビルド用に、PyInstallerを含む任意依存 `dist` を追加しました。
- プレイ時間フィルタでは、総プレイ時間を確認できないゲームを結果から除外する挙動を明記しました。

#### 変更

- バージョンを `0.4.0` に更新しました。
- Windowsでは、設定ファイルに保存するSteam Web API keyをDPAPIで保護するようにしました。既存の平文設定ファイルも引き続き読み込めます。

### English

#### Added

- Added `filter --played` for games with at least 1 minute of total playtime.
- Added `filter --min-playtime` and `filter --max-playtime` for filtering by total playtime ranges.
- Added `filter --app-id` for exact Steam AppID matches.
- Added `filter --name` and `filter --install-path` for regular-expression matching against game names and install paths.
- Added `--sort` and `--desc` to `list` and `filter` for sorting by name, size, last updated time, and total playtime.
- Added `--summary` to `list` and `filter` for game counts, total install size, and per-library counts and sizes.
- Added `steam-cli --version` so users can inspect the current CLI version.
- Added the optional `dist` dependency group with PyInstaller for Windows single-file exe builds.
- Documented that playtime filters exclude games whose total playtime could not be fetched.

#### Changed

- Bumped the version to `0.4.0`.
- On Windows, Steam Web API keys saved in the config file are now protected with DPAPI. Existing plaintext config files remain readable.

## v0.3.1

### 日本語

#### 変更

- READMEに必要条件、インストール方法、コマンド一覧、出力項目、設定とキャッシュ、制限事項を追加しました。
- README全体の章構成を見直し、はじめて読む人が導入から主要機能まで辿りやすい構成にしました。
- バージョンを `0.3.1` に更新しました。

### English

#### Changed

- Added requirements, installation steps, command summary, output fields, settings and cache details, and limitations to the README.
- Reorganized the README so new users can move from setup to core features more easily.
- Bumped the version to `0.3.1`.

## v0.3.0

### 日本語

#### 追加

- Steam Web API連携を追加し、総プレイ時間を取得できるようにしました。
- `list --with-playtime` を追加しました。
- `filter --unplayed` を追加し、総プレイ時間が0分のゲームを抽出できるようにしました。
- `--refresh` を追加し、総プレイ時間キャッシュを無視して最新情報を取得できるようにしました。
- `config` コマンドを追加し、SteamID64、Steam Web API key、言語設定を保存できるようにしました。
- `config --status` を追加し、設定状態、Steam Web APIの妥当性確認、キャッシュ状態を確認できるようにしました。
- `config --reset` を追加し、保存済み設定を削除できるようにしました。
- `export --json` を追加しました。
- Steam Store APIのゲーム名キャッシュと、Steam Web APIの総プレイ時間キャッシュを追加しました。
- READMEに折り畳み式の出力例を追加しました。

#### 変更

- 設定コマンド名を `configure` から `config` に整理しました。
- READMEを日本語・英語ともに章立てし直し、可読性を改善しました。
- バージョンを `0.3.0` に更新しました。

#### 注意

- Steam Web API keyは `config --status` でも表示されません。
- 総プレイ時間キャッシュはSteamIDごとに6時間保持されます。
- Steam Store APIで取得したゲーム名は、言語とAppIDごとに7日間保持されます。

### English

#### Added

- Added Steam Web API integration for fetching total playtime.
- Added `list --with-playtime`.
- Added `filter --unplayed` to list games with 0 minutes of total playtime.
- Added `--refresh` to ignore the playtime cache and fetch fresh data.
- Added the `config` command for saving SteamID64, Steam Web API key, and language settings.
- Added `config --status` to show configuration status, Steam Web API validation, and cache status.
- Added `config --reset` to remove saved settings.
- Added `export --json`.
- Added Steam Store API game-name caching and Steam Web API playtime caching.
- Added collapsible output examples to the README.

#### Changed

- Renamed the settings command from `configure` to `config`.
- Reorganized the Japanese and English README sections for readability.
- Bumped the version to `0.3.0`.

#### Notes

- Steam Web API key values are not printed by `config --status`.
- Total playtime is cached per SteamID for 6 hours.
- Game names fetched from the Steam Store API are cached per language and AppID for 7 days.
