# ContextForge

**Design deterministic input artifacts for LLMs.**

→ 解析しない。エージェントではない。

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

---

## Quick start

### 依存のインストール（初回のみ）

```bash
pip install "gradio>=4.0" python-dotenv networkx requests
```

### CLI で生成（例）

```bash
python contextforge.py --profile gemini-chronicle
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

👉 **ContextForge Pro** の詳細は [Pro のページ](#) をご覧ください。

---

## Design philosophy

> LLM は賢い。  
> しかし、**何を読ませるかは設計問題だ。**

---

## License / Status

- **License**: MIT License（OSS）
- **Status**: **Experimental / Early-stage** — 仕様変更や破壊的変更の可能性があります。個人・検証用途での利用を想定しています。
- Pro edition details: docs/pro.md
