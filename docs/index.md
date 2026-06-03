---
title: 概要
nav_order: 1
---

# ContextForge

> 📂 **[GitHub リポジトリ →](https://github.com/fukukei23/contextforge)**{: .btn .btn-blue } — ソースコード・テスト詳細はこちらから

**Design deterministic input artifacts for LLMs.**

LLMにコードレビューや設計相談を依頼する際、「何を読ませたか」が分からないと再現・検証が不可能になる。ContextForgeは、LLMへの入力そのものを決定論的な成果物として生成するツール。

![ContextForge Demo]({{ site.baseurl }}/assets/demo.gif)

## できること

- **プロジェクト要約**: Git履歴ベースの年代記・統計・品質レポート
- **選定コード結合**: 重要ファイルを結合してLLMに渡す
- **再現可能**: 同じプロジェクト・同じプロファイル → 同じ成果物
- **ZIP配布**: LLMへの入力をパッケージして共有可能

## ContextForge が「ない」もの

| ❌ | IDE拡張ではない |
|---|---|
| ❌ | 自律エージェントではない |
| ❌ | LLM APIを使わない |
| ❌ | LLMの出力を保証しない |

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| 言語 | Python 3.10+ |
| テスト | pytest (102 tests) |
| カバレッジ | 86% |

---

> 👉 各機能の詳細はサイドバーの **docs** をご覧ください。
