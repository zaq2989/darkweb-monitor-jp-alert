# 実際の脅威情報モニタリング開始ガイド

## 🚀 クイックスタート（最小限の設定）

### 1. モードを本番に変更
```bash
# TUIで変更
source venv/bin/activate && python tui_config_advanced.py
# → 1. 監視設定 → モード: production に変更
```

または直接編集：
```bash
# config/monitoring_config.json
"mode": "simulation" → "production"
```

### 2. 監視を開始
```bash
# 本番モードで起動
source venv/bin/activate && python scripts/start_monitoring_free.py
```

## 📋 推奨設定チェックリスト

### 1. 外部APIエンドポイントの更新（重要度: 高）

#### A. Nitterインスタンス
現在動作している可能性のあるインスタンス：
```
https://nitter.privacydev.net
https://nitter.poast.org
https://nitter.esmailelbob.xyz
https://nitter.mint.lgbt
```

設定方法：
- TUI: `4. 外部API設定` → `1. Nitterインスタンス管理`
- ファイル: `config/external_api_config.json`

#### B. セキュリティニュースサイト
```json
{
  "security_sites": {
    "Security NEXT": "https://www.security-next.com",
    "IPA": "https://www.ipa.go.jp/security/",
    "JPCERT": "https://www.jpcert.or.jp/"
  }
}
```

### 2. プロキシ設定（Tor使用時）

#### Torのインストールと起動
```bash
# Torをインストール
sudo apt install tor

# Torサービスを開始
sudo systemctl start tor

# 確認（ポート9050でリッスン）
ss -tlnp | grep 9050
```

#### TUIでプロキシ有効化
- `8. プロキシ設定`
- プロキシ使用: 有効
- タイプ: socks5
- ホスト: 127.0.0.1
- ポート: 9050

### 3. 監視対象の設定

#### 重要な企業を追加
TUI: `10. 企業管理` で追加
```
例：
- 金融: 三菱UFJ銀行、みずほ銀行、三井住友銀行
- IT: ソニー、富士通、NEC
- 製造: トヨタ、ホンダ、パナソニック
```

#### 優先度設定
TUI: `11. 優先度設定`
- 重要な企業を「HIGH」に設定

### 4. フィルター調整

#### 本番向け推奨設定
- 信頼度しきい値: 75%（誤検知を減らす）
- 重要度レベル: HIGH, MEDIUM のみ（ノイズ削減）
- 優先ターゲットのみ: 有効（重要企業に集中）

### 5. 情報ソースの選択

#### 推奨構成
```
✅ web_scraping     # Google検索
✅ security_news    # 日本のセキュリティニュース
✅ simulation_fallback # ネットワークエラー時の保険
✅ pastebin         # 漏洩情報
△ twitter          # Nitterが動作する場合
△ tor_directories  # Tor使用時
△ ahmia           # Tor使用時
```

## 🔧 段階的な開始方法

### ステップ1: 最小構成でテスト
```json
{
  "monitoring": {
    "mode": "production",
    "interval_minutes": 30
  },
  "sources": {
    "web_scraping": true,
    "security_news": true,
    "simulation_fallback": true,
    // 他はfalse
  }
}
```

### ステップ2: 動作確認後に拡張
- 監視間隔を短く（10分）
- 情報ソースを追加
- プロキシ有効化

### ステップ3: 本格運用
- すべての情報ソース有効化
- APIキー設定（有料API使用時）
- 24時間監視体制

## ⚠️ 注意事項

1. **レート制限**
   - Google: 1分あたり10クエリ以下
   - 無料API: 各サービスの制限を確認

2. **ネットワーク**
   - ファイアウォール設定確認
   - プロキシ経由の場合は速度低下

3. **ストレージ**
   - ログが増大するため定期的に確認
   - `retention_days`で自動削除設定

## 🏃 今すぐ始める

### 最速手順（3分で開始）
```bash
# 1. モード変更
sed -i 's/"mode": "simulation"/"mode": "production"/' config/monitoring_config.json

# 2. 監視開始
source venv/bin/activate && python scripts/start_monitoring_free.py --interval 10

# 3. ログ確認
tail -f logs/darkweb_monitor_free.log
```

## 📊 監視状況の確認

### リアルタイムログ
```bash
tail -f logs/darkweb_monitor_free.log
```

### Slack通知確認
設定したSlackチャンネルで通知を確認

### 統計情報
```bash
# 処理済みURL数
wc -l processed_urls_free.txt

# アラート履歴
grep "ALERT" logs/darkweb_monitor_free.log | wc -l
```