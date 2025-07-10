#!/bin/bash
# Tor対応の本番モニタリング開始スクリプト

echo "================================================"
echo "🚀 Tor対応本番モニタリング開始"
echo "================================================"
echo

# モードを本番に変更
echo "1. 本番モードに切り替え中..."
python3 << 'EOF'
import json

with open('config/monitoring_config.json', 'r') as f:
    config = json.load(f)

# 本番モードに変更
config['monitoring']['mode'] = 'production'

# 監視間隔を15分に（Tor経由は遅いため）
config['monitoring']['interval_minutes'] = 15

# アラート数を適度に
config['monitoring']['max_alerts_per_cycle'] = 5

# Tor関連ソースが有効になっていることを確認
config['sources']['tor_directories'] = True
config['sources']['ahmia'] = True

# フィルターを調整（Tor経由の情報は信頼度が低い場合がある）
config['filters']['confidence_threshold'] = 75

with open('config/monitoring_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("   ✓ モード: production")
print("   ✓ 監視間隔: 15分")
print("   ✓ Torディレクトリ: 有効")
print("   ✓ Ahmia: 有効")
print("   ✓ プロキシ: SOCKS5 (127.0.0.1:9050)")
EOF

echo
echo "2. 有効な情報ソース:"
python3 << 'EOF'
import json

with open('config/monitoring_config.json', 'r') as f:
    config = json.load(f)

enabled_sources = [k for k, v in config['sources'].items() if v]
for source in enabled_sources:
    print(f"   ✓ {source}")
EOF

echo
echo "================================================"
echo "📊 監視対象の確認"
echo "================================================"
python3 << 'EOF'
import json

with open('config/targets.json', 'r', encoding='utf-8') as f:
    targets = json.load(f)

print(f"企業名: {len(targets.get('company_names', []))}社")
print("主要企業:")
for company in targets.get('company_names', [])[:5]:
    print(f"  • {company}")

priority = targets.get('priority_targets', {})
if priority:
    high_priority = [k for k, v in priority.items() if v == 'HIGH']
    print(f"\n優先度HIGH: {len(high_priority)}件")
    for target in high_priority[:3]:
        print(f"  • {target}")
EOF

echo
echo "================================================"
echo "🚀 監視を開始します"
echo "================================================"
echo
echo "注意事項:"
echo "- Tor経由のアクセスは通常より遅くなります"
echo "- 初回は情報収集に時間がかかる場合があります"
echo "- エラーが多い場合は監視間隔を延ばしてください"
echo
echo "Ctrl+C で停止できます"
echo
echo "================================================"

# 監視開始
source venv/bin/activate
python scripts/start_monitoring_free.py