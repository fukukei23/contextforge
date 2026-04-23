# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/lang/ja/).

## [1.0.0] - 2026-02-01

### Added

- 初回リリース。LLM 向け入力アーティファクト（ZIP／単一ファイル／チャンク群）の決定論的生成。
- プロファイル: gemini-chronicle, claude-chronicle-30mb, gemini-single-file, gpt5-zip, perplexity-prepare 等。
- CLI および Gradio UI。秘密漏洩防止のデフォルト除外（.env, *.pem, *.key 等）。
