#!/usr/bin/env python3
"""
シミュレーションモードで即座に実行
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from external_api.simulated_sources import get_external_results
from core.analyzer import DarkwebAnalyzer
from core.alert_engine import AlertEngine
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def run_simulation():
    """Run monitoring with simulated data"""
    print("\n" + "="*80)
    print("🚀 ダークウェブ監視システム起動（シミュレーションモード）")
    print("="*80 + "\n")
    
    # Initialize
    analyzer = DarkwebAnalyzer('config/targets.json')
    alert_engine = AlertEngine()
    
    # Get simulated darkweb findings
    print("📡 ダークウェブを監視中...")
    results = get_external_results()
    print(f"✓ {len(results)}件の潜在的脅威を検出\n")
    
    # Analyze and send alerts
    alerts_sent = 0
    print("🔍 日本企業への脅威を分析中...\n")
    
    for result in results:
        alert = analyzer.analyze(result)
        
        if alert and alerts_sent < 5:  # Limit to 5 alerts
            print(f"⚠️  脅威検出: {alert['matched_term']}")
            print(f"   ソース: {result['source']}")
            print(f"   重要度: {alert['severity']}")
            print(f"   信頼度: {alert['confidence_score']}%")
            
            # Prepare alert message
            alert['raw_text'] = f"[監視システム] {result['raw_text'][:200]}..."
            
            # Send to Slack
            success = alert_engine.send_alert(alert)
            if success:
                print(f"   ✓ Slackに通知を送信しました\n")
                alerts_sent += 1
            else:
                print(f"   ✗ 通知送信に失敗しました\n")
    
    print("\n" + "-"*80)
    print(f"📊 監視結果:")
    print(f"   - 検出された脅威: {len(results)}件")
    print(f"   - 送信されたアラート: {alerts_sent}件")
    print(f"   - モード: シミュレーション（テスト環境）")
    print("-"*80 + "\n")
    
    print("💡 本番環境では実際の外部APIが使用されます")
    print("✅ 監視サイクルが完了しました\n")

if __name__ == "__main__":
    run_simulation()