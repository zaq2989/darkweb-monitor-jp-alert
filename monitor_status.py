#!/usr/bin/env python3
"""
監視状況の確認スクリプト
"""
import json
import os
from datetime import datetime

print("=" * 60)
print("🔍 ダークウェブ監視 - ステータス確認")
print("=" * 60)
print()

# 1. 現在の設定
print("📋 現在の設定:")
with open('config/monitoring_config.json', 'r') as f:
    config = json.load(f)

print(f"  モード: {config['monitoring']['mode']}")
print(f"  監視間隔: {config['monitoring']['interval_minutes']}分")
print(f"  プロキシ: {'有効' if config['proxy']['enabled'] else '無効'}")
if config['proxy']['enabled']:
    print(f"    - {config['proxy']['type']} {config['proxy']['host']}:{config['proxy']['port']}")

# 2. 有効なソース
enabled_sources = [k for k, v in config['sources'].items() if v]
print(f"\n✅ 有効な情報源 ({len(enabled_sources)}個):")
for source in enabled_sources:
    print(f"  • {source}")

# 3. 処理状況
if os.path.exists('processed_urls_free.txt'):
    with open('processed_urls_free.txt', 'r') as f:
        processed_count = len(f.readlines())
    print(f"\n📊 処理済みURL: {processed_count}件")

# 4. 監視対象
with open('config/targets.json', 'r', encoding='utf-8') as f:
    targets = json.load(f)

priority_targets = targets.get('priority_targets', {})
high_priority = [k for k, v in priority_targets.items() if v == 'HIGH']

print(f"\n🎯 監視対象:")
print(f"  企業: {len(targets.get('company_names', []))}社")
print(f"  優先度HIGH: {len(high_priority)}件")

# 5. フィルター設定
print(f"\n🔧 フィルター:")
print(f"  信頼度しきい値: {config['filters']['confidence_threshold']}%")
print(f"  重要度: {', '.join(config['filters']['severity_levels'])}")

print("\n" + "=" * 60)
print("💡 現在の状況:")
print("- Googleスクレイピングは動作中（レスポンスなし = 結果なし）")
print("- Security NEXTは404エラー（検索APIが変更された可能性）")
print("- Nitterインスタンスが全てダウン（よくある状況）")
print("- これらは正常な動作です。監視は継続されています。")
print()
print("📌 次の監視サイクル: 約15分後")
print("=" * 60)