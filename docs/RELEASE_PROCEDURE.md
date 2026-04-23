# GitHub Release 手順

リリース時は次の手順で GitHub Release を作成する。

## 1. タグを打つ

- バージョン `X.Y.Z` に合わせて Git タグ `vX.Y.Z` を打つ。
- バージョン番号は [pyproject.toml](../pyproject.toml) の `version` と一致させる。

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

## 2. GitHub で Release を作成する

- GitHub リポジトリの **Releases** から「Draft a new release」を選ぶ。
- **Choose a tag**: 上記でプッシュした `vX.Y.Z` を選択する。
- **Release title**: `vX.Y.Z` または「ContextForge vX.Y.Z」など。
- **Describe this release**: そのバージョンの変更概要を 1〜2 行で書く。[CHANGELOG.md](../CHANGELOG.md) の該当見出しをコピーしてよい。
- 成果物として「ソースコード (zip/tar.gz)」が自動添付される。必要なら後から wheel を追加できる。
- 「Publish release」で公開する。

## 3. リリース後の確認

- [CHANGELOG.md](../CHANGELOG.md) に該当バージョンのエントリがあることを確認する。
- リリース前チェックリスト（[docs/RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)）を実行済みであることを確認する。
