# 🆓 Darkweb Monitor JP Alert - 無料版

完全無料でダークウェブ監視を実現するシステム。有料APIを一切使用せず、オープンソースと無料サービスのみで構築。

## 🎯 無料版の特徴

### 利用可能な無料リソース

1. **Ahmia** - 無料Tor検索エンジン
   - .onionサイトの検索
   - レート制限なし（良識的な使用を推奨）

2. **Have I Been Pwned (HIBP)** - 漏洩確認
   - メールアドレスの漏洩チェック
   - 6秒間隔の制限あり

3. **GitHub Search API** - コード漏洩検出
   - 公開リポジトリでの企業情報検索
   - 60リクエスト/時（未認証時）

4. **OnionScan** - Torサイトスキャナー
   - .onionサイトの詳細スキャン
   - 完全無料のOSS

5. **Tor Discovery** - 新規サイト発見
   - 既知のディレクトリから探索
   - ペーストサイトモニタリング

## 📦 セットアップ

### 1. 最小限の環境設定

```bash
# .envファイルを作成
cp .env.example .env

# 必要な設定（Slack通知のみ）
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. オプション: OnionScanのインストール

```bash
# OnionScan (Goが必要)
go get github.com/s-rah/onionscan
# または
wget https://github.com/s-rah/onionscan/releases/latest/download/onionscan-linux-amd64
chmod +x onionscan-linux-amd64
sudo mv onionscan-linux-amd64 /usr/local/bin/onionscan
```

### 4. オプション: Torプロキシ

```bash
# Torのインストール（OnionScan使用時）
sudo apt-get install tor
sudo service tor start
```

## 🚀 使用方法

### 無料版の起動

```bash
# デフォルト: 10分間隔（API制限を考慮）
python scripts/start_monitoring_free.py

# カスタム間隔
python scripts/start_monitoring_free.py --interval 15

# 単発実行
python scripts/start_monitoring_free.py --once
```

## 📊 無料版の制限と回避策

| リソース | 制限 | 回避策 |
|---------|------|--------|
| GitHub | 60req/hour | 10分間隔で実行 |
| HIBP | 1req/6sec | メール数を限定 |
| Ahmia | なし | 良識的使用 |
| OnionScan | なし | Tor帯域に依存 |

## 🔍 監視フロー（無料版）

```
1. GitHub検索
   └→ 企業ドメイン + "password"等で検索
   
2. HIBP確認
   └→ 代表的なメールアドレスをチェック
   
3. Ahmia検索
   └→ Torサイトから企業名を検索
   
4. Tor Discovery（10サイクルごと）
   └→ 新規.onionサイト発見
   
5. OnionScan（オプション）
   └→ 発見したサイトの詳細スキャン
```

## 💡 無料版での工夫

### 1. 効率的なキーワード選定

```json
{
  "keywords": [
    "企業ドメイン + password",
    "企業名 + leak",
    "company.co.jp"
  ]
}
```

### 2. API制限の回避

- 実行間隔を10分以上に設定
- 重要度の高いターゲットを優先
- キャッシュによる重複チェック削減

### 3. 誤検知の削減

- 類似度スコア85%以上でフィルタ
- ソースごとの信頼度調整
- コンテキスト分析の強化

## 📈 拡張オプション

### 無料でできる追加監視

1. **Telegram監視**
   - 公開チャンネルの検索
   - t.me リンクの収集

2. **Reddit監視**
   - /r/onions等の監視
   - PRAW（Python Reddit API）

3. **Twitter監視**
   - 公開ツイートの検索
   - Nitter経由でのスクレイピング

## 🛠️ トラブルシューティング

### OnionScanが動作しない

```bash
# Torが起動しているか確認
curl --socks5 localhost:9050 https://check.torproject.org
```

### API制限エラー

```bash
# ログを確認
tail -f darkweb_monitor_free.log

# 間隔を延長
python scripts/start_monitoring_free.py --interval 20
```

## 📝 有料版との比較

| 機能 | 無料版 | 有料版 |
|------|--------|--------|
| リアルタイム性 | △（10分〜） | ◎（3分〜） |
| データ量 | △（制限あり） | ◎（大量） |
| 情報の深さ | ○（公開情報） | ◎（非公開含む） |
| 運用コスト | ◎（無料） | △（有料） |

## 🎯 無料版が適している場合

- 予算が限られている
- 基本的な監視で十分
- OSSを活用したい
- 小規模な監視対象

## 🚨 注意事項

- API制限を守って使用すること
- Torネットワークに負荷をかけないこと
- 発見した情報は適切に扱うこと
- 定期的にログを確認すること

---

無料版でも十分な監視が可能です。まずは無料版で始めて、必要に応じて有料APIを追加することをお勧めします。