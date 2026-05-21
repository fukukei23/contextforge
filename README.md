# ContextForge

**Design deterministic input artifacts for LLMs.**

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-102%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-86%25-brightgreen)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![ContextForge Demo](assets/demo.gif)

---

## なぜContextForgeを作ったか

LLMにコードレビューや設計相談を依頼する際、「何を読ませたか」が分からないと再現・検証が不可能になる。ContextForgeは、**LLMへの入力そのものを決定論的な成果物として生成する**ことで、この問題を解決する。

---

## What is ContextForge?

**ContextForge は、LLM に渡す“入力アーティファクト”を設計・生成するツールです。**

- コードを解析して答えを出すツール**ではない**
- LLM の代わりに考えるツール**でもない**
- LLM が読む「入力そのもの」を、**再現可能な成果物**として作るためのツールです。

---

## What ContextForge is NOT

誤解を先に潰すためのセクションです。

| | |
|---|---|
| ❌ | IDE 拡張ではない |
| ❌ | 自律エージェントではない |
| ❌ | LLM API を使わない |
| ❌ | LLM の出力品質を保証しない |
| ❌ | “分析結果”を生成するツールではない |

---

## Why input artifacts matter

LLM は賢いが、**毎回同じものを読んでいない**ことがある。

**IDE やエージェント内では：**

- 何が渡ったか分からない
- 再現できない
- 説明できない

**ContextForge では：**

- 「これを読ませた」と言える
- ZIP で共有できる
- 後から検証できる

---

## What ContextForge generates

**LLM に直接渡せる Input Artifact（入力アーティファクト）**

含まれるものの例：

- **プロジェクト要約**（年代記・統計・品質レポート）
- **選定されたファイル群**（結合コード or チャンク）
- **なぜ含めたかの理由**（マニフェスト・ブートストラップ指示）
- **決定論的**：同じプロジェクト・同じプロファイル → 同じ成果物

### 出力例（ディレクトリ）

```
exports/
  <project>_<profile>_<timestamp>/
    PROJECT_CHRONICLE.md   # Git 履歴ベースの要約
    COMBINED_CODE.py       # 選定コードの結合
    PROJECT_INFO.md        # 統計・品質・推奨プロンプト
    README.md              # パッケージ説明（ZIP 内）
```

プロファイルによっては単一 `.md` やチャンク分割ファイル群になります。

---

## Typical use cases

- **LLM を使った設計レビュー**：同じコンテキストで何度も聞き直したいとき
- **社外共有・引き継ぎ**：「この ZIP を読んでから議論しよう」と渡したいとき
- **セキュリティ／構造レビュー前の入力固定**：前提を揃えてから依頼したいとき
- **「この前提で考えて」と指示したいとき**：入力そのものを成果物として残したいとき

**ツールの有用性**：「ContextForgeを使うとLLMのコードレビュー精度が上がるか」で測る設計を [docs/EVALUATION_USEFULNESS.md](docs/EVALUATION_USEFULNESS.md) にまとめています。改善を分析するときの枠組みは [docs/IMPROVEMENT_FRAMEWORK.md](docs/IMPROVEMENT_FRAMEWORK.md) を参照してください。

---

## Features

- **決定論的出力**: 同じ入力・同じプロファイル → 常に同一の成果物
- **複数出力形式**: ZIP、単一 Markdown、チャンク分割に対応
- **秘密漏洩防止**: .env、*.pem、*.key などをデフォルト除外
- **Gradio UI**: ブラウザで直感的に操作可能
- **拡張可能**: TOML 設定でカスタムプロファイルを追加可能

---

## Quick start

### 依存のインストール（初回のみ）

**パッケージからインストール（推奨）:**

```bash
pip install .
```

**または依存のみ:**

```bash
pip install "gradio>=4.0" python-dotenv networkx requests
```

### CLI で生成（例）

```bash
python contextforge.py --profile gemini-chronicle
# または（pip install 後）: contextforge --profile gemini-chronicle
```

### UI で起動

```bash
python contextforge.py --ui
```

ブラウザでプロジェクトルートとプロファイルを選び、実行できます。詳細オプションは `python contextforge.py --help` を参照してください。

---

## Editions

| | ContextForge（OSS / Individual） | ContextForge Pro |
|---|---|---|
| 保証 | ベストエフォート | 固定入力アーティファクト仕様 |
| 互換 | 仕様・互換保証なし | 再現性・互換性保証 |
| 用途 | 個人・検証 | 業務プリセット |

👉 **ContextForge Pro** の詳細は [Pro のページ](docs/pro.md) をご覧ください。

👉 **ビジネス用途・チーム利用の場合は Pro 版がおすすめ**。再現性・互換性を保証し、業務プリセット（audit/handover/security-review/refactor-review）を含む。[Pro 版の詳細を見る](docs/pro.md)

---

## Release

- **バージョン**: [pyproject.toml](pyproject.toml) の `version` で一箇所管理。SemVer（MAJOR.MINOR.PATCH）に従う。
- **タグ**: リリース時は Git タグ `vX.Y.Z` を打つ（[PROJECT_PROFILE](docs/PROJECT_PROFILES/PROJECT_PROFILE_CONTEXTFORGE.md) の Repo Policy に従う）。
- **変更履歴**: [CHANGELOG.md](CHANGELOG.md) をリリースごとに更新する。
- **手順**: [docs/RELEASE_PROCEDURE.md](docs/RELEASE_PROCEDURE.md)。リリース前は [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) を実行する。

---

## アーキテクチャ

```
プロジェクトディレクトリ
       ↓
  ContextForge（TOML プロファイル選択）
       ↓
  ┌──────────────┐
  │ Git履歴解析   │ → PROJECT_CHRONICLE.md
  │ ファイル選定   │ → COMBINED_CODE.py
  │ 統計・品質    │ → PROJECT_INFO.md
  └──────┬───────┘
         ↓
  出力: exports/<project>_<profile>_<timestamp>/
         ↓ ZIP で共有可能
```

---

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 言語 | Python 3.10+ |
| UI | Gradio 4.0+ |
| 設定 | TOML |
| 依存解析 | networkx |
| パッケージング | pyproject.toml / pip |

---

## テスト

```bash
# テスト実行
python -m pytest tests/ -v
```

---

## Design philosophy

> LLM は賢い。  
> しかし、**何を読ませるかは設計問題だ。**

---

## License / Status

- **License**: MIT License（OSS）
- **Status**: **Experimental / Early-stage** — 仕様変更や破壊的変更の可能性があります。個人・検証用途での利用を想定しています。
- Pro edition details: [docs/pro.md](docs/pro.md)
