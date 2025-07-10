# ローカル実行ガイド

## 🚀 クイックスタート

### 1. システム起動
```bash
# プロジェクトディレクトリに移動
cd /home/zaq/デスクトップ/exp/darkweb/darkweb-monitor-jp-alert/

# ローカル実行スクリプトを起動
python3 start_local.py
```

初回実行時は自動的に以下をセットアップします：
- ✅ Python環境チェック
- ✅ 仮想環境作成
- ✅ 依存関係インストール
- ✅ 設定ファイル作成

### 2. TUI設定画面

起動後、メニューから「1」を選択してTUI設定画面を開きます：

```
🛡️  ダークウェブモニタリング設定 (TUI)
=====================================

  1. 基本設定
  2. 情報収集ソース設定
  3. Slack通知設定
  4. プロキシ設定
  5. 監視対象企業
  6. 監視を開始
  7. テスト実行
  8. 設定を保存して終了
  9. 保存せずに終了

モード: SIMULATION
↑↓: 移動  Enter: 選択  q: 終了
```

## 📋 TUI操作方法

### ナビゲーション
- **↑↓**: メニュー項目の移動
- **Enter**: 選択/決定
- **ESC**: 前の画面に戻る
- **q**: 終了

### 各設定画面

#### 1. 基本設定
- **監視間隔**: 何分ごとに監視するか（デフォルト: 10分）
- **モード**: simulation（テスト）/ production（本番）
- **最大アラート数**: 1サイクルあたりの最大通知数

#### 2. 情報収集ソース設定
- **web_scraping**: Google検索、セキュリティサイト
- **twitter**: Nitter経由のTwitter監視
- **tor_directories**: Torディレクトリ監視
- **security_news**: 日本のセキュリティニュース
- **simulation_fallback**: ネットワークエラー時の代替

スペースキーで有効/無効を切り替え

#### 3. Slack通知設定
- Webhook URLの設定
- テスト通知の送信
- 通知の有効/無効切り替え

#### 4. プロキシ設定
- Tor経由でのアクセス設定
- プロキシタイプ: socks5 / http
- デフォルト: 127.0.0.1:9050（Tor）

## 🧪 動作テスト

### シミュレーションモード（推奨）
外部APIを使用せず、ローカルでテスト：

```bash
# メニューから「2」を選択、または直接実行：
python3 run_with_simulation.py
```

### 単発テスト
1回だけ実行してすぐ終了：

```bash
# メニューから「4」を選択、または：
python3 test_simulated_monitoring.py
```

## 🚀 本番運用

### 前提条件
1. **外部API設定**（必要に応じて）
   - Nitterインスタンスの確認
   - プロキシ設定（Tor使用時）

2. **Slack設定**
   - Webhook URLの設定
   - `.env`ファイルに記載

### 本番起動
```bash
# TUIから「6. 監視を開始」を選択
# または直接実行：
source venv/bin/activate
python scripts/start_monitoring_free.py
```

## 📁 ファイル構成

```
darkweb-monitor-jp-alert/
├── start_local.py          # ローカル起動スクリプト
├── tui_config.py          # TUI設定画面
├── config/
│   ├── monitoring_config.json  # 監視設定
│   └── targets.json           # 監視対象企業
├── .env                   # 環境変数（Slack URL等）
└── logs/                  # ログファイル
```

## 🔧 トラブルシューティング

### TUIが文字化けする場合
```bash
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8
```

### 依存関係エラー
```bash
# 仮想環境を再作成
rm -rf venv/
python3 start_local.py
```

### ネットワークエラー
- プロキシ設定を確認
- シミュレーションモードで動作確認

## 💡 Tips

1. **初回は必ずシミュレーションモードでテスト**
2. **Slack通知はテスト送信で確認**
3. **監視対象は`config/targets.json`で追加可能**
4. **ログは`logs/`ディレクトリに保存**

## 📞 サポート

問題が発生した場合：
1. `logs/darkweb_monitor_free.log`を確認
2. TUI設定画面で設定を再確認
3. シミュレーションモードで動作確認