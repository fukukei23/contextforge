# リリース前チェックリスト

GitHub Release を作成する前に、以下を確認する。PROJECT_PROFILE の [Quality Gates](PROJECT_PROFILES/PROJECT_PROFILE_CONTEXTFORGE.md) に準拠する。

## Quality Gates

- [ ] **初回CLI成功**: `exports/` が無い状態で `python contextforge.py --profile gemini-chronicle`（または `contextforge --profile gemini-chronicle`）を実行し、正常終了する。
- [ ] **ZIP制約**: いずれかのプロファイルで ZIP を生成し、プロファイルの `target_mb` 以内に収まっている（ベストエフォート）。超過時は heavy リストで除外されている。
- [ ] **秘密漏洩防止**: デフォルト除外に `.env`, `*.env`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*id_rsa*` が含まれている（[contextforge.py](../contextforge.py) の `COMMON_EXCLUDE_FILES` を確認）。

## Quick start 動作確認

- [ ] **依存インストール**: `pip install .` でインストールできる（推奨: venv 内で実行）。
- [ ] **CLI 例**: `python contextforge.py --profile gemini-chronicle` または `contextforge --profile gemini-chronicle` でアーティファクトが生成される。
- [ ] **UI 起動**: `python contextforge.py --ui` でブラウザが開き、プロファイル選択・実行ができる（Gradio が利用可能な環境）。

## その他

- [ ] [CHANGELOG.md](../CHANGELOG.md) に当該バージョンのエントリを追加済みである。
- [ ] [pyproject.toml](../pyproject.toml) の `version` がリリースするバージョンと一致している。

## チェック後

- 結果を [docs/RELEASE_CHECK_RESULT.md](RELEASE_CHECK_RESULT.md) に記録する（任意）。
- 初回リリース時は [docs/RELEASE_FIRST_TIME_DRUM_KIT.md](RELEASE_FIRST_TIME_DRUM_KIT.md) に従って GitHub Release を作成する。
