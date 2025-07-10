#!/bin/bash
# Torモニタリングセットアップスクリプト

echo "================================================"
echo "🧅 Torモニタリング セットアップ"
echo "================================================"
echo

# 1. Torの状態確認
echo "1. Torサービスの状態を確認中..."
if systemctl is-active --quiet tor; then
    echo "   ✓ Torサービスは既に実行中です"
    TOR_RUNNING=true
else
    echo "   ℹ️  Torサービスが実行されていません"
    TOR_RUNNING=false
fi

# 2. Torポート確認
echo
echo "2. Torプロキシポートを確認中..."
if ss -tlnp 2>/dev/null | grep -q ":9050"; then
    echo "   ✓ ポート9050でTorプロキシが利用可能です"
    TOR_PORT_OK=true
else
    echo "   ⚠️  ポート9050が開いていません"
    TOR_PORT_OK=false
fi

# 3. Tor接続テスト
echo
echo "3. Tor接続をテスト中..."
if command -v torify &> /dev/null; then
    if torify curl -s https://check.torproject.org/api/ip | grep -q '"IsTor":true'; then
        echo "   ✓ Tor経由でインターネットに接続できます"
        TOR_WORKS=true
    else
        echo "   ⚠️  Tor接続テストに失敗しました"
        TOR_WORKS=false
    fi
else
    echo "   ⚠️  torifyコマンドが見つかりません"
    TOR_WORKS=false
fi

# 4. Torのインストール手順表示
if [ "$TOR_RUNNING" = false ] || [ "$TOR_PORT_OK" = false ]; then
    echo
    echo "================================================"
    echo "📋 Torのインストール手順:"
    echo "================================================"
    echo
    echo "1. Torをインストール:"
    echo "   sudo apt update"
    echo "   sudo apt install -y tor"
    echo
    echo "2. Torサービスを開始:"
    echo "   sudo systemctl start tor"
    echo "   sudo systemctl enable tor  # 自動起動を有効化"
    echo
    echo "3. 状態確認:"
    echo "   sudo systemctl status tor"
    echo
    echo "インストール後、このスクリプトを再実行してください。"
    exit 1
fi

# 5. Python設定を更新
echo
echo "4. Tor監視機能を有効化中..."

python3 << 'EOF'
import json
import os

# 設定ファイルを読み込み
config_file = 'config/monitoring_config.json'
with open(config_file, 'r') as f:
    config = json.load(f)

# Tor関連のソースを有効化
config['sources']['tor_directories'] = True
config['sources']['ahmia'] = True

# プロキシ設定を有効化
config['proxy']['enabled'] = True
config['proxy']['type'] = 'socks5'
config['proxy']['host'] = '127.0.0.1'
config['proxy']['port'] = 9050

# Web scraperでもプロキシを使用可能に
print("   ✓ Tor関連の情報ソースを有効化しました:")
print("     - Torディレクトリ監視: 有効")
print("     - Ahmia (Tor検索エンジン): 有効")
print("   ✓ プロキシ設定を有効化しました:")
print("     - タイプ: SOCKS5")
print("     - ホスト: 127.0.0.1:9050")

# 保存
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

# 外部API設定も更新
api_config_file = 'config/external_api_config.json'
if os.path.exists(api_config_file):
    with open(api_config_file, 'r') as f:
        api_config = json.load(f)
else:
    api_config = {'external_apis': {}}

# Torディレクトリを追加
if 'tor_directories' not in api_config.get('external_apis', {}):
    api_config['external_apis']['tor_directories'] = []

# 既知のTorディレクトリとダークウェブ検索エンジン
tor_directories = [
    "https://dark.fail",
    "https://darkfailenbsdla5mal2mxn2uz66od5vtzd5qozslagrfzachha3f3id.onion.ws",
    "https://darkfailenbsdla5mal2mxn2uz66od5vtzd5qozslagrfzachha3f3id.onion.ly",
    "https://ahmia.fi",
    "https://thehiddenwiki.org"
]

# 重複を避けて追加
existing = set(api_config['external_apis'].get('tor_directories', []))
for directory in tor_directories:
    if directory not in existing:
        api_config['external_apis'].setdefault('tor_directories', []).append(directory)

with open(api_config_file, 'w') as f:
    json.dump(api_config, f, indent=2)

print()
print("   ✓ Torディレクトリリストを更新しました")
EOF

# 6. テスト用スクリプト作成
echo
echo "5. Tor接続テストスクリプトを作成中..."

cat > test_tor_connection.py << 'EOF'
#!/usr/bin/env python3
"""
Tor接続テスト
"""
import requests
import json

def test_tor_connection():
    """Test Tor proxy connection"""
    print("=== Tor接続テスト ===\n")
    
    # プロキシ設定
    proxies = {
        'http': 'socks5://127.0.0.1:9050',
        'https': 'socks5://127.0.0.1:9050'
    }
    
    try:
        # 1. 通常の接続でIPを確認
        print("1. 通常のIP確認:")
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        normal_ip = response.json()['ip']
        print(f"   通常IP: {normal_ip}")
        
        # 2. Tor経由でIPを確認
        print("\n2. Tor経由のIP確認:")
        response = requests.get(
            'https://api.ipify.org?format=json', 
            proxies=proxies,
            timeout=30
        )
        tor_ip = response.json()['ip']
        print(f"   Tor IP: {tor_ip}")
        
        # 3. Torステータス確認
        print("\n3. Torステータス確認:")
        response = requests.get(
            'https://check.torproject.org/api/ip',
            proxies=proxies,
            timeout=30
        )
        tor_status = response.json()
        print(f"   Tor使用中: {tor_status.get('IsTor', False)}")
        
        if normal_ip != tor_ip:
            print("\n✅ Tor接続は正常に動作しています！")
            print("   IPアドレスが変更されていることを確認しました。")
        else:
            print("\n⚠️  警告: IPアドレスが変更されていません")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ エラー: {e}")
        print("\nTorサービスが実行されているか確認してください:")
        print("  sudo systemctl status tor")
    
    # 4. Ahmiaテスト
    print("\n4. Ahmia (Tor検索エンジン) 接続テスト:")
    try:
        response = requests.get('https://ahmia.fi', timeout=10)
        if response.status_code == 200:
            print("   ✅ Ahmiaに接続できます")
        else:
            print(f"   ⚠️  Ahmia応答: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ahmia接続エラー: {e}")

if __name__ == "__main__":
    # pysocksのインストール確認
    try:
        import socks
        test_tor_connection()
    except ImportError:
        print("❌ PySocksがインストールされていません")
        print("\n以下のコマンドでインストールしてください:")
        print("  source venv/bin/activate")
        print("  pip install pysocks")
EOF

chmod +x test_tor_connection.py

# 7. 必要なPythonパッケージをインストール
echo
echo "6. 必要なPythonパッケージを確認中..."
source venv/bin/activate

if python -c "import socks" 2>/dev/null; then
    echo "   ✓ PySocksは既にインストールされています"
else
    echo "   📦 PySocksをインストール中..."
    pip install pysocks
    echo "   ✓ PySocksをインストールしました"
fi

# 8. 完了メッセージ
echo
echo "================================================"
echo "✅ Torモニタリングの設定が完了しました！"
echo "================================================"
echo
echo "📋 次のステップ:"
echo
echo "1. Tor接続をテスト:"
echo "   source venv/bin/activate && python test_tor_connection.py"
echo
echo "2. Tor対応で監視を開始:"
echo "   source venv/bin/activate && python scripts/start_monitoring_free.py"
echo
echo "3. より詳細な設定（オプション）:"
echo "   python tui_config_advanced.py"
echo "   → 外部API設定でTorディレクトリを追加/編集"
echo
echo "================================================"
echo "🧅 有効化されたTor機能:"
echo "================================================"
echo "- Torディレクトリ監視 (dark.fail等)"
echo "- Ahmia検索エンジン"
echo "- SOCKS5プロキシ経由のアクセス"
echo "- .onionサイトの発見"
echo
echo "⚠️  注意: Tor経由のアクセスは通常より遅くなります"