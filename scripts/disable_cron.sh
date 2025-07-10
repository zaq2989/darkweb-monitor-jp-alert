#!/bin/bash
# Disable cron job for darkweb monitoring

echo "==================================="
echo "Cronjob 無効化スクリプト"
echo "==================================="
echo

# Check if cron job exists
if crontab -l 2>/dev/null | grep -q "darkweb-monitor-jp-alert"; then
    echo "✓ 既存のcronjobを検出しました"
    
    # Remove the cron job
    crontab -l | grep -v "darkweb-monitor-jp-alert" | crontab -
    
    echo "✓ Cronjobを無効化しました"
else
    echo "ℹ️  Cronjobは設定されていません"
fi

# Rename cron script to prevent accidental execution
if [ -f "scripts/cron_monitor.sh" ]; then
    mv scripts/cron_monitor.sh scripts/cron_monitor.sh.disabled
    echo "✓ Cronスクリプトを無効化しました"
fi

echo
echo "完了！Cronjobは無効化されました。"
echo
echo "再度有効化する場合:"
echo "1. scripts/cron_monitor.sh.disabled を scripts/cron_monitor.sh に戻す"
echo "2. crontab -e で以下を追加:"
echo "   */10 * * * * /home/zaq/デスクトップ/exp/darkweb/darkweb-monitor-jp-alert/scripts/cron_monitor.sh"