# GitHub アップロードガイド

## 1. アップロード前の確認事項

### 🔒 機密情報の削除
```bash
# 現在の.envファイルを確認（実際の値が含まれていないことを確認）
cat .env

# もし実際のWebhook URLが含まれている場合は削除
cp .env.example .env
```

### 📁 不要なファイルの確認
```bash
# .gitignoreで除外されるファイルを確認
git status --ignored

# ログファイルやデータファイルが含まれていないことを確認
ls -la logs/
ls -la data/
```

## 2. GitHubリポジトリの作成

1. GitHubにログイン: https://github.com/zaq2989
2. 新しいリポジトリを作成:
   - Repository name: `darkweb-monitor-jp-alert`
   - Description: `日本企業向けダークウェブ監視システム / Darkweb monitoring system for Japanese companies`
   - Public リポジトリとして作成
   - READMEは作成しない（既にあるため）

## 3. ローカルからのアップロード

```bash
# プロジェクトディレクトリに移動
cd /home/zaq/デスクトップ/exp/darkweb/darkweb-monitor-jp-alert

# Gitリポジトリを初期化
git init

# すべてのファイルを追加
git add .

# 初回コミット
git commit -m "Initial commit: Darkweb Monitor JP Alert System"

# GitHubリポジトリをリモートとして追加
git remote add origin https://github.com/zaq2989/darkweb-monitor-jp-alert.git

# メインブランチに名前を変更
git branch -M main

# GitHubにプッシュ
git push -u origin main
```

## 4. アップロード後の設定

### リポジトリの説明を追加
GitHubのリポジトリページで:
- ⚙️ Settings → Description に以下を追加:
  ```
  🛡️ 日本企業向けダークウェブ監視システム。脅威情報を自動収集しSlackに通知 / Darkweb monitoring for Japanese companies with Slack alerts
  ```

### トピックスを追加
- `darkweb`
- `security`
- `monitoring`
- `japan`
- `slack`
- `tor`
- `threat-intelligence`

### About セクションを設定
- Website: なし
- Topics: 上記のトピックスを追加
- ☑️ Releases
- ☑️ Issues

## 5. 推奨される追加ファイル

### CONTRIBUTING.md (オプション)
```markdown
# Contributing to Darkweb Monitor JP Alert

プルリクエストを歓迎します！

## 開発環境のセットアップ
1. このリポジトリをフォーク
2. ローカルにクローン
3. `python3 start_local.py` で環境構築
4. 新しいブランチで作業

## プルリクエストのガイドライン
- 新機能は必ずテストを追加
- コミットメッセージは明確に
- READMEの更新も忘れずに
```

### SECURITY.md (オプション)
```markdown
# Security Policy

## 脆弱性の報告

セキュリティ上の問題を発見した場合は、公開のIssueではなく、
プライベートに報告してください。

## サポートされているバージョン

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
```

## 6. アップロード完了後の確認

- [ ] READMEが正しく表示されている
- [ ] .envファイルが含まれていない
- [ ] logsディレクトリが含まれていない
- [ ] venvディレクトリが含まれていない
- [ ] ライセンスが表示されている

## 7. 使用開始の案内

READMEに以下のバッジを追加（オプション）:
```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
```

## ⚠️ 注意事項

1. **Slack Webhook URLは絶対に含めない**
2. **実際の企業名が含まれている場合は汎用的な例に変更**
3. **ログファイルは必ず除外**
4. **個人情報や機密情報が含まれていないか最終確認**