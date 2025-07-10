# 📋 GitHub アップロード前チェックリスト

## 1. 機密情報の確認

### .envファイル
```bash
# 実際のWebhook URLが含まれていないことを確認
grep "hooks.slack.com" .env

# もし含まれていたら、サンプルに置き換え
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" > .env
```

### 設定ファイル
```bash
# monitoring_config.jsonに機密情報がないか確認
cat config/monitoring_config.json | grep -i "api\|key\|secret\|password"
```

## 2. 不要ファイルの削除

```bash
# ログファイルを削除
rm -rf logs/*.log

# テストファイルを削除
rm -f test_*.json
rm -f *_test_*.json
rm -f config_export_*.json

# キャッシュを削除
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 処理済みURLリストを削除
rm -f processed_urls_free.txt
```

## 3. .gitignoreの確認

```bash
# .gitignoreが正しく機能しているか確認
git init
git add .
git status

# 以下が表示されないことを確認:
# - venv/
# - .env (実際の値を含むもの)
# - logs/
# - __pycache__/
```

## 4. ドキュメントの最終確認

- [ ] README.mdが最新の内容になっている
- [ ] インストール手順が正確
- [ ] 使用方法が分かりやすい
- [ ] トラブルシューティングが充実
- [ ] ライセンスが含まれている

## 5. コードの最終確認

- [ ] ハードコードされたAPIキーがない
- [ ] ハードコードされたURLがない（サンプル以外）
- [ ] 個人情報が含まれていない
- [ ] 企業の実名が適切（汎用的な例になっている）

## 6. アップロードコマンド

すべて確認できたら、以下のコマンドでアップロード：

```bash
# クリーンアップ
rm -rf .git
rm -rf logs/*.log
rm -f processed_urls_free.txt

# Git初期化
git init
git add .
git commit -m "Initial commit: Darkweb Monitor JP Alert System

- 日本企業向けダークウェブ監視システム
- 複数の情報ソースから脅威情報を収集
- Slack通知機能
- TUIによる簡単設定
- Tor対応"

# GitHubにプッシュ
git remote add origin https://github.com/zaq2989/darkweb-monitor-jp-alert.git
git branch -M main
git push -u origin main
```

## 7. アップロード後の確認

GitHubで以下を確認：
- [ ] READMEが正しく表示されている
- [ ] .envが含まれていない（.env.exampleのみ）
- [ ] logsディレクトリが空または存在しない
- [ ] ライセンスが認識されている

## 完了！ 🎉

アップロードが完了したら、以下のURLでアクセス可能：
https://github.com/zaq2989/darkweb-monitor-jp-alert