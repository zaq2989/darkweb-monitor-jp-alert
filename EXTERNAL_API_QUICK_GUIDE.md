# 外部情報収集 クイックガイド

## 🚀 すぐに変更すべき主要設定

### 1. Nitterインスタンス（Twitter監視）
**ファイル**: `external_api/twitter_monitor.py`（行24-30）
```python
self.nitter_instances = [
    "https://nitter.net",  # ← 動作するインスタンスに変更
    "https://nitter.privacydev.net",
    "https://nitter.poast.org"
]
```
**変更理由**: Nitterインスタンスは頻繁にダウンするため、動作確認が必要

### 2. プロキシ設定（Tor経由アクセス）
**ファイル**: `external_api/web_scraper.py`（行36-40）
```python
# Torを使用する場合
self.proxies = {
    'http': 'socks5://127.0.0.1:9050',  # ← Torのポートを確認
    'https': 'socks5://127.0.0.1:9050'
}
```
**変更理由**: ダークウェブアクセスにはTorが必要

### 3. APIキー設定（有料APIを使用する場合）
**ファイル**: `.env`
```bash
# 実際のAPIキーに変更
DARKOWL_API_KEY=your_actual_key_here
SPYCLOUD_API_KEY=your_actual_key_here
```

### 4. 監視間隔
**ファイル**: `scripts/start_monitoring_free.py`（実行時パラメータ）
```bash
# デフォルト10分 → 変更する場合
python scripts/start_monitoring_free.py --interval 30  # 30分間隔
```

## 📋 チェックリスト

### ネットワーク環境の確認
- [ ] Google検索にアクセス可能か？
- [ ] Torが利用可能か？（ポート9050）
- [ ] プロキシが必要か？

### API設定
- [ ] 無料APIのみで十分か？
- [ ] 有料APIのキーを取得したか？
- [ ] レート制限を確認したか？

### 監視対象
- [ ] `config/targets.json`の企業リストは最新か？
- [ ] 優先度設定は適切か？

## 🔧 トラブルシューティング

### すべての外部APIが失敗する場合
```python
# シミュレーションモードで動作確認
python run_with_simulation.py
```

### 特定のAPIのみ失敗する場合
1. そのAPIのエンドポイントを確認
2. 認証情報を確認
3. レート制限を確認

### タイムアウトが多い場合
```python
# web_scraper.py でタイムアウトを延長
kwargs['timeout'] = kwargs.get('timeout', 60)  # 30→60秒に
```

## 📞 サポート

問題が解決しない場合：
1. `logs/darkweb_monitor_free.log`を確認
2. ネットワーク設定を確認
3. プロキシ/ファイアウォール設定を確認