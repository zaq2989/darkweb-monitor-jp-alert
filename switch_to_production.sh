#!/bin/bash
# 本番モードに切り替えるスクリプト

echo "================================================"
echo "🚀 本番モード切り替えスクリプト"
echo "================================================"
echo

# 現在の設定確認
echo "1. 現在の設定:"
MODE=$(grep -o '"mode": "[^"]*"' config/monitoring_config.json | cut -d'"' -f4)
INTERVAL=$(grep -o '"interval_minutes": [0-9]*' config/monitoring_config.json | cut -d' ' -f2)
echo "   - モード: $MODE"
echo "   - 監視間隔: ${INTERVAL}分"
echo

# バックアップ作成
echo "2. 設定をバックアップ中..."
cp config/monitoring_config.json config/monitoring_config.json.backup
echo "   ✓ バックアップ完了: config/monitoring_config.json.backup"
echo

# モード変更
echo "3. 本番モードに変更中..."
sed -i 's/"mode": "simulation"/"mode": "production"/' config/monitoring_config.json
echo "   ✓ モードを production に変更しました"
echo

# 最小限の安全な設定
echo "4. 安全な初期設定を適用中..."

# Python スクリプトで設定を更新
python3 << 'EOF'
import json

# 設定を読み込み
with open('config/monitoring_config.json', 'r') as f:
    config = json.load(f)

# 安全な初期設定
config['monitoring']['interval_minutes'] = 30  # 30分間隔（負荷軽減）
config['monitoring']['max_alerts_per_cycle'] = 3  # アラート数制限

# 情報ソースを限定（最初は少なめ）
config['sources']['web_scraping'] = True
config['sources']['security_news'] = True
config['sources']['simulation_fallback'] = True
config['sources']['twitter'] = False  # Nitterが不安定なため最初はOFF
config['sources']['tor_directories'] = False  # Tor未設定の場合はOFF
config['sources']['ahmia'] = False
config['sources']['pastebin'] = True
config['sources']['github_gists'] = False
config['sources']['reddit'] = False
config['sources']['telegram'] = False

# フィルター設定（誤検知を減らす）
config['filters']['confidence_threshold'] = 80  # 80%以上の信頼度のみ
config['filters']['severity_levels'] = ['HIGH', 'MEDIUM']  # 重要なもののみ

# 保存
with open('config/monitoring_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("   ✓ 安全な初期設定を適用しました")
print()
print("   有効な情報ソース:")
print("   - Web Scraping (Google検索)")
print("   - セキュリティニュース")
print("   - Pastebin監視")
print("   - シミュレーションフォールバック")
print()
print("   フィルター:")
print("   - 信頼度: 80%以上")
print("   - 重要度: HIGH, MEDIUMのみ")
EOF

echo
echo "5. 設定完了!"
echo
echo "================================================"
echo "📋 次のステップ:"
echo "================================================"
echo
echo "1. 監視を開始:"
echo "   source venv/bin/activate && python scripts/start_monitoring_free.py"
echo
echo "2. ログを確認:"
echo "   tail -f logs/darkweb_monitor_free.log"
echo
echo "3. より多くの情報源を有効化（動作確認後）:"
echo "   python tui_config_advanced.py"
echo "   → 3. 情報収集ソース で追加の情報源を有効化"
echo
echo "4. 監視間隔を短縮（安定動作確認後）:"
echo "   python tui_config_advanced.py"
echo "   → 1. 監視設定 → 監視間隔: 10分"
echo
echo "================================================"
echo "⚠️  注意事項:"
echo "================================================"
echo "- 最初は30分間隔で様子を見てください"
echo "- エラーが多い場合は情報ソースを減らしてください"
echo "- Tor使用時は事前にTorサービスを起動してください"
echo
echo "準備ができたら上記コマンドで監視を開始してください！"