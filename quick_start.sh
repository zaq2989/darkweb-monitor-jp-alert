#!/bin/bash
# クイックスタートスクリプト

echo "=================================================="
echo "🛡️  ダークウェブモニタリング - クイックスタート"
echo "=================================================="
echo

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv venv
    echo "✅ 仮想環境を作成しました"
    
    echo "📚 必須パッケージをインストール中..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install requests beautifulsoup4 python-dotenv fuzzywuzzy schedule
    echo "✅ パッケージをインストールしました"
else
    echo "✅ 仮想環境が既に存在します"
    source venv/bin/activate
fi

# Create necessary directories
echo "📁 ディレクトリを確認中..."
mkdir -p config logs data
echo "✅ ディレクトリを確認しました"

# Check config files
if [ ! -f "config/targets.json" ]; then
    echo "📝 デフォルト設定を作成中..."
    cat > config/targets.json << 'EOF'
{
  "keywords": ["sony.co.jp", "トヨタ自動車", "panasonic.com", "任天堂", "softbank.jp"],
  "domains": ["sony.co.jp", "toyota.co.jp", "panasonic.com", "nintendo.co.jp", "softbank.jp"],
  "company_names": ["ソニー", "トヨタ自動車", "パナソニック", "任天堂", "ソフトバンク"],
  "priority_targets": {
    "sony.co.jp": "HIGH",
    "rakuten.co.jp": "HIGH",
    "三菱UFJ銀行": "HIGH"
  }
}
EOF
    echo "✅ targets.jsonを作成しました"
fi

if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Slack Webhook URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/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

# Optional API Keys
# DARKOWL_API_KEY=
# SPYCLOUD_API_KEY=
EOF
    echo "✅ .envファイルを作成しました"
fi

echo
echo "🎯 実行オプション:"
echo "1) シミュレーションテスト（推奨）"
echo "2) TUI設定画面"
echo "3) 本番モード"
echo

# Run simulation by default
echo "シミュレーションモードで実行します..."
echo "=============================================="
echo

python run_with_simulation.py

echo
echo "✅ テスト実行が完了しました！"
echo
echo "次のステップ:"
echo "- TUI設定: python tui_config.py"
echo "- 本番実行: python scripts/start_monitoring_free.py"
echo "- ドキュメント: cat LOCAL_SETUP_GUIDE.md"