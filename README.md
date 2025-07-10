# 🛡️ Darkweb Monitor JP Alert

日本企業を対象としたダークウェブ監視システム。脅威情報を自動収集し、Slackに通知します。

## 📋 目次
- [概要](#概要)
- [主な機能](#主な機能)
- [必要な環境](#必要な環境)
- [インストール](#インストール)
- [初期設定](#初期設定)
- [使い方](#使い方)
- [監視対象の設定](#監視対象の設定)
- [高度な設定](#高度な設定)
- [トラブルシューティング](#トラブルシューティング)

## 概要

このシステムは、ダークウェブや各種オンラインソースから日本企業に関する脅威情報を自動的に収集し、リアルタイムでSlackに通知します。個人情報漏洩、企業情報流出、サイバー攻撃の予兆などを早期に発見できます。

### 監視対象の例
- 企業の機密情報漏洩
- 従業員の認証情報流出
- 顧客データベースの露出
- 攻撃計画の議論
- 脆弱性情報の共有

## 主な機能

### 🔍 情報収集ソース
- **Web検索**: Google検索でダークウェブ関連情報を収集
- **セキュリティニュース**: 日本のセキュリティサイトを監視
- **Pastebin**: 漏洩情報の投稿を監視
- **GitHub Gists**: 意図しない情報公開を検出
- **Reddit/Telegram**: ダークウェブ関連の議論を追跡
- **Tor対応**: Ahmia、Dark.fail等のダークウェブディレクトリ

### 🚨 アラート機能
- Slack通知（重要度別）
- 日本語対応
- カスタマイズ可能なフィルター

### 🎛️ 管理機能
- TUI（ターミナルUI）による簡単設定
- 監視対象企業の管理
- 優先度設定
- ログ管理

## 必要な環境

- **OS**: Ubuntu/Debian (推奨) または macOS
- **Python**: 3.8以上
- **メモリ**: 2GB以上
- **ディスク**: 1GB以上の空き容量
- **ネットワーク**: インターネット接続必須
- **Tor** (オプション): ダークウェブアクセス用

## インストール

### 1. リポジトリのクローン
```bash
git clone https://github.com/zaq2989/darkweb-monitor-jp-alert.git
cd darkweb-monitor-jp-alert
```

### 2. 初回セットアップ（最も簡単な方法）
```bash
# ローカル実行環境をセットアップ
python3 start_local.py
```

このコマンドで以下が自動的に実行されます：
- Python環境チェック
- 仮想環境の作成
- 必要なパッケージのインストール
- 設定ファイルの作成

### 3. Slack Webhook URLの設定

1. Slackワークスペースで[Incoming Webhooks](https://slack.com/apps/A0F7XDUAZ-incoming-webhooks)を設定
2. Webhook URLをコピー
3. `.env`ファイルに設定：
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 初期設定

### 🎯 クイックスタート（3分で開始）

```bash
# 1. シミュレーションモードでテスト
./quick_start.sh

# 2. 問題なければ本番モードに切り替え
./switch_to_production.sh

# 3. 監視を開始
source venv/bin/activate && python scripts/start_monitoring_free.py
```

### 📊 TUIを使った詳細設定

```bash
# TUI設定画面を起動
source venv/bin/activate && python tui_config_advanced.py
```

TUIメニュー:
1. **基本設定**: 監視間隔、モード、アラート数
2. **情報収集ソース**: 各ソースのON/OFF
3. **Slack通知設定**: Webhook URL、テスト送信
4. **監視対象企業**: 企業の追加/編集/削除
5. **優先度設定**: 重要な企業をHIGHに設定

### 操作方法
- `↑↓`: メニュー移動
- `Enter`: 選択/決定
- `Space`: ON/OFF切り替え
- `ESC`: 前の画面に戻る
- `q`: 終了

## 使い方

### 📌 基本的な使い方

#### 1. 監視対象企業の設定
`config/targets.json`を編集するか、TUIで設定：
```json
{
  "company_names": ["ソニー", "トヨタ自動車", "任天堂"],
  "domains": ["sony.co.jp", "toyota.co.jp", "nintendo.co.jp"],
  "keywords": ["Sony", "Toyota", "Nintendo"],
  "priority_targets": {
    "sony.co.jp": "HIGH",
    "toyota.co.jp": "MEDIUM"
  }
}
```

#### 2. 監視の開始
```bash
# 本番モードで監視開始（10分間隔）
source venv/bin/activate
python scripts/start_monitoring_free.py --interval 10
```

#### 3. 監視状況の確認
```bash
# ステータス確認
python monitor_status.py

# ログの確認
tail -f logs/darkweb_monitor_free.log
```

### 🚀 Tor経由での監視（推奨）

#### 1. Torのインストール
```bash
sudo apt update
sudo apt install -y tor
sudo systemctl start tor
sudo systemctl enable tor
```

#### 2. Tor監視の有効化
```bash
./setup_tor_monitoring.sh
```

#### 3. Tor対応で監視開始
```bash
./start_production_with_tor.sh
```

## 監視対象の設定

### 企業の追加方法

#### 方法1: TUIを使用（推奨）
```bash
python tui_config_advanced.py
# → 10. 企業管理 → 企業名/ドメイン/キーワードを追加
```

#### 方法2: 直接編集
`config/targets.json`:
```json
{
  "company_names": [
    "株式会社サンプル",
    "サンプル銀行"
  ],
  "domains": [
    "sample.co.jp",
    "sample-bank.jp"
  ],
  "priority_targets": {
    "sample-bank.jp": "HIGH"  // 金融機関は優先度HIGH
  }
}
```

### 優先度の設定
- **HIGH**: 即座に通知（金融、インフラ企業など）
- **MEDIUM**: 通常通知（一般企業）
- **LOW/設定なし**: 低優先度

## 高度な設定

### フィルター設定
```bash
python tui_config_advanced.py
# → 2. フィルター設定
```

- **信頼度しきい値**: 75-85%（推奨）
- **重要度レベル**: HIGH, MEDIUM のみ（ノイズ削減）
- **優先ターゲットのみ**: 重要企業に集中

### 外部APIの設定

#### Nitterインスタンス（Twitter監視）
```bash
python tui_config_advanced.py
# → 4. 外部API設定 → 1. Nitterインスタンス管理
```

動作するインスタンスを追加：
- https://nitter.privacydev.net
- https://nitter.poast.org

### プロキシ設定
Tor使用時は自動設定されますが、手動設定も可能：
```bash
python tui_config_advanced.py
# → 8. プロキシ設定
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. Slack通知が届かない
```bash
# テスト通知を送信
python test_alert.py
```
- Webhook URLが正しいか確認
- ファイアウォール設定を確認

#### 2. 外部APIエラーが多い
- 一時的に情報ソースを減らす（TUIで設定）
- 監視間隔を延ばす（15-30分）
- プロキシ設定を確認

#### 3. Torが動作しない
```bash
# Torサービスの状態確認
sudo systemctl status tor

# 再起動
sudo systemctl restart tor
```

#### 4. メモリ不足
- 監視間隔を延ばす
- 同時処理する情報ソースを減らす
- ログファイルを定期的に削除

### ログの確認
```bash
# エラーログの確認
grep ERROR logs/*.log

# 警告の確認
grep WARNING logs/*.log
```

## 📁 ディレクトリ構成

```
darkweb-monitor-jp-alert/
├── config/                 # 設定ファイル
│   ├── targets.json       # 監視対象企業
│   └── monitoring_config.json  # システム設定
├── core/                  # コアモジュール
│   ├── analyzer.py        # 分析エンジン
│   └── alert_engine.py    # アラート送信
├── external_api/          # 外部API連携
│   ├── web_scraper.py     # Webスクレイピング
│   └── twitter_monitor.py # Twitter監視
├── scripts/               # 実行スクリプト
│   └── start_monitoring_free.py  # メイン実行ファイル
├── logs/                  # ログファイル
├── data/                  # データ保存
└── venv/                  # Python仮想環境
```

## 🔒 セキュリティ

- APIキーや認証情報は`.env`ファイルに保存
- `.env`ファイルは`.gitignore`に含める
- Tor経由でアクセスすることで匿名性を確保
- ログファイルには機密情報を含めない

## 📝 ライセンス

MIT License

## 🤝 コントリビューション

Issue や Pull Request は歓迎します。

## 📞 サポート

問題が発生した場合：
1. [Issues](https://github.com/zaq2989/darkweb-monitor-jp-alert/issues)で報告
2. `logs/`ディレクトリのログを確認
3. READMEのトラブルシューティングを参照

## 🙏 謝辞

このプロジェクトは以下のオープンソースプロジェクトを使用しています：
- BeautifulSoup4
- Requests
- FuzzyWuzzy
- Schedule

---

**注意**: このツールは防御的なセキュリティ目的でのみ使用してください。