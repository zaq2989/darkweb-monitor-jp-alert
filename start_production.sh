#!/bin/bash
#
# 本番運用開始スクリプト
#

set -e  # エラーで停止

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Darkweb Monitor - 本番運用開始"
echo "=========================================="
echo ""

# 1. 環境確認
echo "1. 環境確認中..."
if [ ! -f ".env" ]; then
    echo "❌ .envファイルが見つかりません"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "❌ 仮想環境が見つかりません"
    exit 1
fi

echo "✅ 環境確認完了"
echo ""

# 2. 設定確認
echo "2. 現在の監視対象:"
source venv/bin/activate
python scripts/manage_targets.py list | head -20
echo ""

# 3. プロセス確認
echo "3. 既存プロセス確認..."
if ./scripts/monitor_daemon.sh status | grep -q "running"; then
    echo "⚠️  既にデーモンが実行中です"
    read -p "再起動しますか？ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./scripts/monitor_daemon.sh restart
    fi
else
    echo "✅ デーモンは停止中"
fi
echo ""

# 4. ログローテーション設定
echo "4. ログローテーション設定..."
cat > /tmp/darkweb-monitor-logrotate << EOF
$SCRIPT_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
}
EOF
echo "✅ ログローテーション設定作成（/tmp/darkweb-monitor-logrotate）"
echo "   sudo cp /tmp/darkweb-monitor-logrotate /etc/logrotate.d/darkweb-monitor"
echo ""

# 5. 最終確認
echo "5. 本番運用開始の最終確認"
echo ""
echo "チェックリスト:"
echo "  ✓ Slack通知先は本番チャンネルですか？"
echo "  ✓ 監視対象企業は最新ですか？"
echo "  ✓ 営業時間設定は適切ですか？"
echo ""
read -p "本番運用を開始しますか？ (y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "運用開始をキャンセルしました"
    exit 0
fi

# 6. 運用開始
echo ""
echo "6. 本番運用を開始します..."

# バックアップ作成
echo "- 設定ファイルをバックアップ中..."
backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp -r config "$backup_dir/"
cp .env "$backup_dir/"
echo "✅ バックアップ完了: $backup_dir"

# デーモン起動
echo "- モニタリングデーモンを起動中..."
./scripts/monitor_daemon.sh start

# 動作確認
sleep 3
if ./scripts/monitor_daemon.sh status | grep -q "running"; then
    echo "✅ デーモン起動成功"
else
    echo "❌ デーモン起動失敗"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 本番運用開始完了！"
echo "=========================================="
echo ""
echo "監視状況:"
./scripts/monitor_daemon.sh status
echo ""
echo "ログ確認: tail -f logs/monitor_daemon.log"
echo "停止方法: ./scripts/monitor_daemon.sh stop"
echo ""
echo "定期確認項目:"
echo "  - 毎日: ログファイルのサイズ確認"
echo "  - 週次: アラート統計の確認"
echo "  - 月次: 監視対象の見直し"
echo ""