#!/usr/bin/env python3
"""
TUI設定画面 - ダークウェブモニタリングシステム
"""
import os
import sys
import json
import curses
from typing import Dict, Any, List
import subprocess

class MonitoringTUI:
    """Terminal User Interface for monitoring configuration"""
    
    def __init__(self):
        self.config_file = 'config/monitoring_config.json'
        self.targets_file = 'config/targets.json'
        self.env_file = '.env'
        self.load_config()
        
    def load_config(self):
        """Load current configuration"""
        # デフォルト設定
        self.config = {
            'monitoring': {
                'interval_minutes': 10,
                'mode': 'simulation',  # 'simulation' or 'production'
                'max_alerts_per_cycle': 5
            },
            'sources': {
                'web_scraping': True,
                'twitter': True,
                'tor_directories': True,
                'security_news': True,
                'simulation_fallback': True
            },
            'slack': {
                'enabled': True,
                'webhook_url': ''
            },
            'proxy': {
                'enabled': False,
                'type': 'socks5',
                'host': '127.0.0.1',
                'port': 9050
            }
        }
        
        # 既存の設定を読み込み
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                saved_config = json.load(f)
                self.config.update(saved_config)
        
        # Slack URLを.envから読み込み
        self._load_slack_url()
    
    def _load_slack_url(self):
        """Load Slack URL from .env"""
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    if line.startswith('SLACK_WEBHOOK_URL='):
                        url = line.split('=', 1)[1].strip()
                        self.config['slack']['webhook_url'] = url
    
    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        # Slack URLを.envに保存
        self._save_slack_url()
    
    def _save_slack_url(self):
        """Save Slack URL to .env"""
        lines = []
        url_found = False
        
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    if line.startswith('SLACK_WEBHOOK_URL='):
                        lines.append(f"SLACK_WEBHOOK_URL={self.config['slack']['webhook_url']}\n")
                        url_found = True
                    else:
                        lines.append(line)
        
        if not url_found:
            lines.append(f"SLACK_WEBHOOK_URL={self.config['slack']['webhook_url']}\n")
        
        with open(self.env_file, 'w') as f:
            f.writelines(lines)
    
    def draw_menu(self, stdscr, current_row):
        """Draw main menu"""
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Title
        title = "🛡️  ダークウェブモニタリング設定 (TUI)"
        stdscr.addstr(1, (w - len(title)) // 2, title, curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * (w - 4))
        
        # Menu items
        menu_items = [
            ("1. 基本設定", self.config_monitoring),
            ("2. 情報収集ソース設定", self.config_sources),
            ("3. Slack通知設定", self.config_slack),
            ("4. プロキシ設定", self.config_proxy),
            ("5. 監視対象企業", self.config_targets),
            ("6. 監視を開始", self.start_monitoring),
            ("7. テスト実行", self.test_monitoring),
            ("8. 設定を保存して終了", None),
            ("9. 保存せずに終了", None)
        ]
        
        for idx, (text, _) in enumerate(menu_items):
            y = 4 + idx
            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, 4, f"> {text}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, 4, f"  {text}")
        
        # Status
        mode = self.config['monitoring']['mode']
        status_color = curses.color_pair(2) if mode == 'production' else curses.color_pair(3)
        stdscr.addstr(h - 3, 2, f"モード: ", curses.A_BOLD)
        stdscr.addstr(h - 3, 10, mode.upper(), status_color | curses.A_BOLD)
        
        stdscr.addstr(h - 2, 2, "↑↓: 移動  Enter: 選択  q: 終了")
        stdscr.refresh()
        
        return menu_items
    
    def config_monitoring(self, stdscr):
        """Configure basic monitoring settings"""
        stdscr.clear()
        stdscr.addstr(1, 2, "基本設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        settings = [
            ('interval_minutes', '監視間隔（分）'),
            ('mode', 'モード (simulation/production)'),
            ('max_alerts_per_cycle', '1サイクルの最大アラート数')
        ]
        
        current_row = 0
        
        while True:
            for idx, (key, label) in enumerate(settings):
                y = 4 + idx * 2
                value = self.config['monitoring'][key]
                
                if idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {label}: {value}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 2, f"  {label}: {value}")
            
            stdscr.addstr(12, 2, "↑↓: 移動  Enter: 編集  ESC: 戻る")
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(settings) - 1:
                current_row += 1
            elif key == 10:  # Enter
                setting_key, label = settings[current_row]
                self._edit_value(stdscr, setting_key, label)
    
    def _edit_value(self, stdscr, key, label):
        """Edit a configuration value"""
        h, w = stdscr.getmaxyx()
        stdscr.addstr(h - 5, 2, f"{label}の新しい値: ")
        curses.echo()
        
        value = stdscr.getstr(h - 5, len(label) + 12, 60).decode('utf-8')
        curses.noecho()
        
        if value:
            # 型変換
            if key in ['interval_minutes', 'max_alerts_per_cycle']:
                try:
                    value = int(value)
                except ValueError:
                    stdscr.addstr(h - 3, 2, "無効な値です", curses.color_pair(4))
                    stdscr.refresh()
                    stdscr.getch()
                    return
            
            if 'monitoring' in self.config and key in self.config['monitoring']:
                self.config['monitoring'][key] = value
            elif 'slack' in self.config and key in self.config['slack']:
                self.config['slack'][key] = value
            elif 'proxy' in self.config and key in self.config['proxy']:
                self.config['proxy'][key] = value
            
            stdscr.addstr(h - 3, 2, "✓ 更新しました", curses.color_pair(2))
            stdscr.refresh()
            stdscr.getch()
    
    def config_sources(self, stdscr):
        """Configure data sources"""
        stdscr.clear()
        stdscr.addstr(1, 2, "情報収集ソース設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        sources = list(self.config['sources'].items())
        current_row = 0
        
        while True:
            for idx, (source, enabled) in enumerate(sources):
                y = 4 + idx
                status = "有効" if enabled else "無効"
                color = curses.color_pair(2) if enabled else curses.color_pair(4)
                
                if idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {source}: ")
                    stdscr.attroff(curses.color_pair(1))
                    stdscr.addstr(y, 25, status, color | curses.A_BOLD)
                else:
                    stdscr.addstr(y, 2, f"  {source}: ")
                    stdscr.addstr(y, 25, status, color)
            
            stdscr.addstr(12, 2, "↑↓: 移動  Space: 切替  ESC: 戻る")
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(sources) - 1:
                current_row += 1
            elif key == 32:  # Space
                source_key = sources[current_row][0]
                self.config['sources'][source_key] = not self.config['sources'][source_key]
                sources = list(self.config['sources'].items())
    
    def config_slack(self, stdscr):
        """Configure Slack settings"""
        stdscr.clear()
        stdscr.addstr(1, 2, "Slack通知設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        enabled = self.config['slack']['enabled']
        webhook_url = self.config['slack']['webhook_url']
        
        stdscr.addstr(4, 2, f"通知: {'有効' if enabled else '無効'}")
        stdscr.addstr(5, 2, f"Webhook URL: {webhook_url[:50]}..." if len(webhook_url) > 50 else f"Webhook URL: {webhook_url}")
        
        stdscr.addstr(8, 2, "1. 通知を切り替え")
        stdscr.addstr(9, 2, "2. Webhook URLを変更")
        stdscr.addstr(10, 2, "3. テスト通知を送信")
        stdscr.addstr(12, 2, "ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == ord('1'):
                self.config['slack']['enabled'] = not self.config['slack']['enabled']
                stdscr.addstr(4, 2, f"通知: {'有効' if self.config['slack']['enabled'] else '無効'}     ")
                stdscr.refresh()
            elif key == ord('2'):
                self._edit_value(stdscr, 'webhook_url', 'Slack Webhook URL')
                webhook_url = self.config['slack']['webhook_url']
                stdscr.addstr(5, 2, f"Webhook URL: {webhook_url[:50]}..." if len(webhook_url) > 50 else f"Webhook URL: {webhook_url}     ")
                stdscr.refresh()
            elif key == ord('3'):
                self._test_slack(stdscr)
    
    def _test_slack(self, stdscr):
        """Send test notification to Slack"""
        h, w = stdscr.getmaxyx()
        stdscr.addstr(h - 3, 2, "テスト通知を送信中...", curses.color_pair(3))
        stdscr.refresh()
        
        # Create test alert script
        test_script = """
import sys
sys.path.append('.')
from core.alert_engine import AlertEngine
alert_engine = AlertEngine()
test_alert = {
    'matched_term': 'テスト企業',
    'source': 'TUI設定画面',
    'severity': 'INFO',
    'confidence_score': 100,
    'raw_text': 'これはTUI設定画面からのテスト通知です。'
}
success = alert_engine.send_alert(test_alert)
print('SUCCESS' if success else 'FAILED')
"""
        
        result = subprocess.run(
            ['python', '-c', test_script],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if 'SUCCESS' in result.stdout:
            stdscr.addstr(h - 3, 2, "✓ テスト通知が送信されました     ", curses.color_pair(2))
        else:
            stdscr.addstr(h - 3, 2, "✗ 送信に失敗しました            ", curses.color_pair(4))
        
        stdscr.refresh()
        stdscr.getch()
    
    def config_proxy(self, stdscr):
        """Configure proxy settings"""
        stdscr.clear()
        stdscr.addstr(1, 2, "プロキシ設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        settings = [
            ('enabled', 'プロキシ使用'),
            ('type', 'タイプ (socks5/http)'),
            ('host', 'ホスト'),
            ('port', 'ポート')
        ]
        
        current_row = 0
        
        while True:
            for idx, (key, label) in enumerate(settings):
                y = 4 + idx
                value = self.config['proxy'][key]
                
                if key == 'enabled':
                    value = '有効' if value else '無効'
                
                if idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {label}: {value}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 2, f"  {label}: {value}")
            
            stdscr.addstr(10, 2, "↑↓: 移動  Enter: 編集  ESC: 戻る")
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(settings) - 1:
                current_row += 1
            elif key == 10:  # Enter
                setting_key, label = settings[current_row]
                if setting_key == 'enabled':
                    self.config['proxy']['enabled'] = not self.config['proxy']['enabled']
                elif setting_key == 'port':
                    self._edit_value(stdscr, setting_key, label)
                    try:
                        self.config['proxy']['port'] = int(self.config['proxy']['port'])
                    except:
                        self.config['proxy']['port'] = 9050
                else:
                    self._edit_value(stdscr, setting_key, label)
    
    def config_targets(self, stdscr):
        """Configure monitoring targets"""
        stdscr.clear()
        stdscr.addstr(1, 2, "監視対象企業", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        with open(self.targets_file, 'r', encoding='utf-8') as f:
            targets = json.load(f)
        
        companies = targets.get('company_names', [])[:10]
        
        for idx, company in enumerate(companies):
            stdscr.addstr(4 + idx, 2, f"• {company}")
        
        stdscr.addstr(16, 2, f"合計: {len(targets.get('company_names', []))}社")
        stdscr.addstr(18, 2, "targets.jsonで詳細設定可能")
        stdscr.addstr(20, 2, "ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
    
    def start_monitoring(self, stdscr):
        """Start monitoring"""
        stdscr.clear()
        stdscr.addstr(1, 2, "監視を開始", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        mode = self.config['monitoring']['mode']
        interval = self.config['monitoring']['interval_minutes']
        
        stdscr.addstr(4, 2, f"モード: {mode}")
        stdscr.addstr(5, 2, f"間隔: {interval}分")
        stdscr.addstr(7, 2, "監視を開始しますか？")
        stdscr.addstr(9, 2, "Y: はい  N: いいえ")
        
        key = stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            self.save_config()
            stdscr.addstr(11, 2, "設定を保存しました", curses.color_pair(2))
            stdscr.addstr(12, 2, "監視を開始します...", curses.color_pair(3))
            stdscr.refresh()
            
            # Exit curses mode
            curses.endwin()
            
            # Start monitoring
            if mode == 'simulation':
                os.system('source venv/bin/activate && python run_with_simulation.py')
            else:
                os.system(f'source venv/bin/activate && python scripts/start_monitoring_free.py --interval {interval}')
            
            sys.exit(0)
    
    def test_monitoring(self, stdscr):
        """Run test monitoring"""
        stdscr.clear()
        stdscr.addstr(1, 2, "テスト実行", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        stdscr.addstr(4, 2, "1回だけテスト実行します")
        stdscr.addstr(6, 2, "Y: 実行  N: キャンセル")
        
        key = stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            self.save_config()
            curses.endwin()
            
            # Run test
            os.system('source venv/bin/activate && python test_simulated_monitoring.py')
            
            print("\nテストが完了しました。Enterキーで設定画面に戻ります...")
            input()
            return
    
    def run(self):
        """Run TUI"""
        def main(stdscr):
            # Setup colors
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Selected
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Success
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Warning
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)    # Error
            
            curses.curs_set(0)
            stdscr.keypad(True)
            
            current_row = 0
            
            while True:
                menu_items = self.draw_menu(stdscr, current_row)
                
                key = stdscr.getch()
                
                if key == curses.KEY_UP and current_row > 0:
                    current_row -= 1
                elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
                    current_row += 1
                elif key == 10:  # Enter
                    _, action = menu_items[current_row]
                    
                    if current_row == 7:  # Save and exit
                        self.save_config()
                        break
                    elif current_row == 8:  # Exit without saving
                        break
                    elif action:
                        action(stdscr)
                elif key in [ord('q'), ord('Q'), 27]:  # q or ESC
                    break
        
        curses.wrapper(main)


if __name__ == "__main__":
    tui = MonitoringTUI()
    tui.run()