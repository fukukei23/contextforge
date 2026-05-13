# 初回 GitHub Release ドラムキット（v1.0.0）

初めて GitHub Release を実施するときの、**そのまま実行できる手順**と**コピペ用テキスト**です。

---

## 前提

- リポジトリは GitHub に push 済みであること。
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) の「要手元確認」項目を実行し、問題ないこと。
- リリースするバージョンは **1.0.0**（pyproject.toml と CHANGELOG.md と一致していること）。

---

## Step 1: タグを打ってプッシュ

リポジトリルートで実行。

```bash
git tag v1.0.0
git push origin v1.0.0
```

※ 既に `v1.0.0` タグがある場合は `git tag -d v1.0.0` でローカル削除し、必要なら `git push origin :refs/tags/v1.0.0` でリモート削除してからやり直す。

---

## Step 2: GitHub で Release を作成

1. GitHub のリポジトリページを開く。
2. 右側の **Releases** をクリック。
3. **Draft a new release** をクリック。
4. 以下を入力・選択する。

| 項目 | 入力内容 |
|------|----------|
| **Choose a tag** | `v1.0.0` を選択（既にプッシュ済みのタグ） |
| **Release title** | 下記「コピペ用: Release title」をコピー |
| **Describe this release** | 下記「コピペ用: Release description」をコピー |

5. **Publish release** をクリック。

※ ソースコードの zip/tar.gz は自動で添付されます。wheel は必要なら後から追加できます。

---

## コピペ用: Release title

```
ContextForge v1.0.0
```

---

## コピペ用: Release description

```
初回リリース。LLM 向け入力アーティファクト（ZIP／単一ファイル／チャンク群）の決定論的生成。
プロファイル: gemini-chronicle, claude-chronicle-30mb, gemini-single-file, gpt5-zip, perplexity-prepare 等。
CLI および Gradio UI。秘密漏洩防止のデフォルト除外（.env, *.pem, *.key 等）。
```

（CHANGELOG の [1.0.0] の Added を要約したものです。）

---

## Step 3: リリース後の確認

- [ ] GitHub の Releases ページに v1.0.0 が表示されている。
- [ ] ソースコード (Source code zip / tar.gz) がダウンロードできる。
- [ ] CHANGELOG.md に 1.0.0 のエントリがあることを再確認。

---

## まとめ

| 順番 | やること |
|------|----------|
| 1 | `git tag v1.0.0` → `git push origin v1.0.0` |
| 2 | GitHub → Releases → Draft a new release |
| 3 | タグ `v1.0.0` を選択、タイトル・説明をコピペ、Publish release |
| 4 | ダウンロードと CHANGELOG を確認 |

以上で初回 GitHub Release の実施は完了です。
