#!/usr/bin/env python3
"""
ローカル実行用スタートスクリプト
環境チェックと初期設定を行い、監視を開始する
"""
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

class LocalMonitoringSetup:
    """ローカル環境セットアップ"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.venv_dir = self.base_dir / 'venv'
        self.requirements_file = self.base_dir / 'requirements.txt'
        
    def check_python(self):
        """Pythonバージョンチェック"""
        print("🔍 Python環境をチェック中...")
        
        version_info = sys.version_info
        if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
            print("❌ Python 3.8以上が必要です")
            print(f"   現在のバージョン: {sys.version}")
            return False
        
        print(f"✅ Python {sys.version.split()[0]} 検出")
        return True
    
    def setup_venv(self):
        """仮想環境セットアップ"""
        if self.venv_dir.exists():
            print("✅ 仮想環境が既に存在します")
            return True
        
        print("📦 仮想環境を作成中...")
        try:
            subprocess.run([sys.executable, '-m', 'venv', str(self.venv_dir)], check=True)
            print("✅ 仮想環境を作成しました")
            return True
        except subprocess.CalledProcessError:
            print("❌ 仮想環境の作成に失敗しました")
            return False
    
    def install_dependencies(self):
        """依存関係インストール"""
        print("📚 依存関係をインストール中...")
        
        pip_path = self.venv_dir / 'bin' / 'pip'
        if os.name == 'nt':  # Windows
            pip_path = self.venv_dir / 'Scripts' / 'pip.exe'
        
        try:
            # Upgrade pip
            subprocess.run([str(pip_path), 'install', '--upgrade', 'pip'], 
                         capture_output=True, check=True)
            
            # Install requirements
            if self.requirements_file.exists():
                subprocess.run([str(pip_path), 'install', '-r', str(self.requirements_file)], 
                             check=True)
                print("✅ 依存関係をインストールしました")
            else:
                print("⚠️  requirements.txtが見つかりません")
                # 最小限の依存関係をインストール
                essential_packages = [
                    'requests', 'beautifulsoup4', 'python-dotenv',
                    'fuzzywuzzy', 'schedule'
                ]
                for package in essential_packages:
                    subprocess.run([str(pip_path), 'install', package], 
                                 capture_output=True, check=True)
                print("✅ 必須パッケージをインストールしました")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ インストールに失敗しました: {e}")
            return False
    
    def check_config(self):
        """設定ファイルチェック"""
        print("⚙️  設定ファイルをチェック中...")
        
        required_files = [
            ('config/targets.json', self._create_default_targets),
            ('.env', self._create_default_env),
            ('config/monitoring_config.json', self._create_default_config)
        ]
        
        all_ok = True
        for file_path, create_func in required_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                print(f"   📝 {file_path} を作成中...")
                create_func(full_path)
            else:
                print(f"   ✅ {file_path} 存在確認")
        
        return all_ok
    
    def _create_default_targets(self, path):
        """デフォルトターゲット作成"""
        path.parent.mkdir(exist_ok=True)
        default_targets = {
            "keywords": ["sony.co.jp", "トヨタ自動車", "panasonic.com"],
            "domains": ["sony.co.jp", "toyota.co.jp", "panasonic.com"],
            "company_names": ["ソニー", "トヨタ自動車", "パナソニック"],
            "priority_targets": {
                "sony.co.jp": "HIGH"
            }
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_targets, f, ensure_ascii=False, indent=2)
    
    def _create_default_env(self, path):
        """デフォルト.env作成"""
        with open(path, 'w') as f:
            f.write("# Slack Webhook URL\n")
            f.write("SLACK_WEBHOOK_URL=\n\n")
            f.write("# Optional: API Keys\n")
            f.write("# DARKOWL_API_KEY=\n")
            f.write("# SPYCLOUD_API_KEY=\n")
    
    def _create_default_config(self, path):
        """デフォルト設定作成"""
        path.parent.mkdir(exist_ok=True)
        default_config = {
            "monitoring": {
                "interval_minutes": 10,
                "mode": "simulation",
                "max_alerts_per_cycle": 5
            },
            "sources": {
                "web_scraping": True,
                "twitter": True,
                "tor_directories": True,
                "security_news": True,
                "simulation_fallback": True
            },
            "slack": {
                "enabled": False,
                "webhook_url": ""
            },
            "proxy": {
                "enabled": False,
                "type": "socks5",
                "host": "127.0.0.1",
                "port": 9050
            }
        }
        with open(path, 'w') as f:
            json.dump(default_config, f, indent=2)
    
    def create_directories(self):
        """必要なディレクトリ作成"""
        print("📁 ディレクトリ構造を確認中...")
        
        dirs = ['config', 'logs', 'data', 'core', 'external_api', 'crawler', 'scripts']
        for dir_name in dirs:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(exist_ok=True)
        
        print("✅ ディレクトリ構造を確認しました")
        return True
    
    def show_menu(self):
        """メインメニュー表示"""
        print("\n" + "="*60)
        print("🛡️  ダークウェブモニタリングシステム - ローカル実行")
        print("="*60)
        print("\n実行オプションを選択してください:\n")
        print("1. 🎛️  TUI設定画面を開く（推奨）")
        print("2. 🧪 シミュレーションモードで実行")
        print("3. 🚀 本番モードで実行")
        print("4. 📊 単発テスト実行")
        print("5. 📖 ドキュメントを表示")
        print("6. 🚪 終了")
        print("\n" + "-"*60)
        
        while True:
            choice = input("\n選択 (1-6): ").strip()
            
            if choice == '1':
                self.run_tui()
            elif choice == '2':
                self.run_simulation()
            elif choice == '3':
                self.run_production()
            elif choice == '4':
                self.run_test()
            elif choice == '5':
                self.show_docs()
            elif choice == '6':
                print("\n👋 終了します")
                break
            else:
                print("❌ 無効な選択です")
    
    def run_tui(self):
        """TUI設定画面実行"""
        print("\n🎛️  TUI設定画面を起動中...")
        
        python_path = self.venv_dir / 'bin' / 'python'
        if os.name == 'nt':  # Windows
            python_path = self.venv_dir / 'Scripts' / 'python.exe'
        
        subprocess.run([str(python_path), 'tui_config.py'])
    
    def run_simulation(self):
        """シミュレーションモード実行"""
        print("\n🧪 シミュレーションモードで実行中...")
        
        python_path = self.venv_dir / 'bin' / 'python'
        if os.name == 'nt':  # Windows
            python_path = self.venv_dir / 'Scripts' / 'python.exe'
        
        subprocess.run([str(python_path), 'run_with_simulation.py'])
        input("\nEnterキーでメニューに戻ります...")
    
    def run_production(self):
        """本番モード実行"""
        print("\n🚀 本番モードで実行中...")
        print("⚠️  外部APIにアクセスします")
        
        python_path = self.venv_dir / 'bin' / 'python'
        if os.name == 'nt':  # Windows
            python_path = self.venv_dir / 'Scripts' / 'python.exe'
        
        subprocess.run([str(python_path), 'scripts/start_monitoring_free.py'])
    
    def run_test(self):
        """テスト実行"""
        print("\n📊 テストを実行中...")
        
        python_path = self.venv_dir / 'bin' / 'python'
        if os.name == 'nt':  # Windows
            python_path = self.venv_dir / 'Scripts' / 'python.exe'
        
        subprocess.run([str(python_path), 'test_simulated_monitoring.py'])
        input("\nEnterキーでメニューに戻ります...")
    
    def show_docs(self):
        """ドキュメント表示"""
        docs = [
            "README.md",
            "EXTERNAL_API_QUICK_GUIDE.md",
            "EXTERNAL_API_CONFIGURATION.md"
        ]
        
        print("\n📖 利用可能なドキュメント:\n")
        for idx, doc in enumerate(docs, 1):
            doc_path = self.base_dir / doc
            if doc_path.exists():
                print(f"{idx}. {doc}")
        
        choice = input("\n表示するドキュメント番号 (0でキャンセル): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(docs):
            doc_path = self.base_dir / docs[int(choice) - 1]
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # ページャーで表示
                import subprocess
                try:
                    subprocess.run(['less'], input=content.encode(), check=True)
                except:
                    # lessが使えない場合は直接表示
                    print("\n" + "="*60)
                    print(content[:2000])  # 最初の2000文字
                    if len(content) > 2000:
                        print("\n... (省略) ...")
                    print("="*60)
                
        input("\nEnterキーでメニューに戻ります...")
    
    def setup(self):
        """セットアップ実行"""
        print("\n🚀 ローカル環境セットアップを開始します...\n")
        
        steps = [
            (self.check_python, "Python環境チェック"),
            (self.setup_venv, "仮想環境セットアップ"),
            (self.install_dependencies, "依存関係インストール"),
            (self.create_directories, "ディレクトリ作成"),
            (self.check_config, "設定ファイルチェック")
        ]
        
        for step_func, step_name in steps:
            if not step_func():
                print(f"\n❌ {step_name}で失敗しました")
                return False
        
        print("\n✅ セットアップが完了しました！")
        return True


def main():
    """メイン実行"""
    setup = LocalMonitoringSetup()
    
    # 初回セットアップ
    if not setup.venv_dir.exists():
        if not setup.setup():
            print("\nセットアップに失敗しました。")
            sys.exit(1)
    
    # メニュー表示
    setup.show_menu()


if __name__ == "__main__":
    main()