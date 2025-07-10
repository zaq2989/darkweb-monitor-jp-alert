#!/usr/bin/env python3
"""
TUI設定画面（拡張版） - ダークウェブモニタリングシステム
脅威情報収集に関わる全設定を網羅
"""
import os
import sys
import json
import curses
from typing import Dict, Any, List
import subprocess
from datetime import datetime

class AdvancedMonitoringTUI:
    """Advanced Terminal User Interface for monitoring configuration"""
    
    def __init__(self):
        self.config_file = 'config/monitoring_config.json'
        self.targets_file = 'config/targets.json'
        self.env_file = '.env'
        self.external_api_config = 'config/external_api_config.json'
        self.load_all_configs()
        
    def load_all_configs(self):
        """Load all configuration files"""
        # 基本設定
        self.config = {
            'monitoring': {
                'interval_minutes': 10,
                'mode': 'simulation',
                'max_alerts_per_cycle': 5,
                'deduplication': True,
                'log_level': 'INFO',
                'retention_days': 30
            },
            'sources': {
                'web_scraping': True,
                'twitter': True,
                'tor_directories': True,
                'security_news': True,
                'simulation_fallback': True,
                'ahmia': True,
                'pastebin': True,
                'github_gists': True,
                'reddit': True,
                'telegram': True
            },
            'slack': {
                'enabled': True,
                'webhook_url': '',
                'severity_filter': ['HIGH', 'MEDIUM', 'LOW'],
                'test_mode': False
            },
            'proxy': {
                'enabled': False,
                'type': 'socks5',
                'host': '127.0.0.1',
                'port': 9050,
                'username': '',
                'password': ''
            },
            'api_keys': {
                'darkowl': '',
                'spycloud': '',
                'intelligencex': '',
                'shodan': '',
                'hibp': ''
            },
            'external_apis': {
                'nitter_instances': [
                    'https://nitter.net',
                    'https://nitter.privacydev.net'
                ],
                'security_sites': {
                    'Security NEXT': 'https://www.security-next.com',
                    'ITmedia': 'https://www.itmedia.co.jp/enterprise/subtop/security/',
                    'IPA': 'https://www.ipa.go.jp/security/'
                },
                'tor_directories': [
                    'https://dark.fail',
                    'https://darkfailenbsdla5mal2mxn2uz66od5vtzd5qozslagrfzachha3f3id.onion.ws'
                ]
            },
            'filters': {
                'confidence_threshold': 85,
                'severity_levels': ['HIGH', 'MEDIUM', 'LOW', 'INFO'],
                'exclude_sources': [],
                'priority_only': False
            },
            'storage': {
                'elasticsearch': {
                    'enabled': False,
                    'host': 'localhost',
                    'port': 9200,
                    'index': 'darkweb-alerts'
                },
                'local_db': {
                    'enabled': True,
                    'path': 'data/alerts.db'
                }
            }
        }
        
        # Load existing configs
        self._load_existing_configs()
        
        # Load targets
        self._load_targets()
    
    def _load_existing_configs(self):
        """Load existing configuration files"""
        # Main config
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                saved_config = json.load(f)
                self._deep_update(self.config, saved_config)
        
        # External API config
        if os.path.exists(self.external_api_config):
            with open(self.external_api_config, 'r') as f:
                api_config = json.load(f)
                if 'external_apis' in api_config:
                    self.config['external_apis'].update(api_config['external_apis'])
        
        # Environment variables
        self._load_env_vars()
    
    def _deep_update(self, d, u):
        """Deep update dictionary"""
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
    
    def _load_env_vars(self):
        """Load environment variables"""
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key == 'SLACK_WEBHOOK_URL':
                            self.config['slack']['webhook_url'] = value
                        elif key.endswith('_API_KEY'):
                            api_name = key.replace('_API_KEY', '').lower()
                            if api_name in self.config['api_keys']:
                                self.config['api_keys'][api_name] = value
    
    def _load_targets(self):
        """Load monitoring targets"""
        if os.path.exists(self.targets_file):
            with open(self.targets_file, 'r', encoding='utf-8') as f:
                self.targets = json.load(f)
        else:
            self.targets = {
                'keywords': [],
                'domains': [],
                'company_names': [],
                'priority_targets': {},
                'categories': {}
            }
    
    def draw_main_menu(self, stdscr, current_row):
        """Draw enhanced main menu"""
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Title
        title = "🛡️  ダークウェブモニタリング設定 (拡張版)"
        stdscr.addstr(1, (w - len(title)) // 2, title, curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * (w - 4))
        
        # Menu categories
        menu_items = [
            ("━━━ 基本設定 ━━━", None),
            ("1. 監視設定", self.config_monitoring),
            ("2. フィルター設定", self.config_filters),
            ("━━━ 情報収集 ━━━", None),
            ("3. 情報収集ソース", self.config_sources),
            ("4. 外部API設定", self.config_external_apis),
            ("5. APIキー管理", self.config_api_keys),
            ("━━━ 通知・出力 ━━━", None),
            ("6. Slack通知設定", self.config_slack),
            ("7. ストレージ設定", self.config_storage),
            ("━━━ ネットワーク ━━━", None),
            ("8. プロキシ設定", self.config_proxy),
            ("9. Nitterインスタンス", self.config_nitter),
            ("━━━ 監視対象 ━━━", None),
            ("10. 企業管理", self.manage_targets),
            ("11. 優先度設定", self.config_priorities),
            ("━━━ 実行・管理 ━━━", None),
            ("12. 監視を開始", self.start_monitoring),
            ("13. ログ表示", self.view_logs),
            ("14. 統計情報", self.view_statistics),
            ("15. エクスポート/インポート", self.export_import),
            ("━━━ システム ━━━", None),
            ("16. ヘルスチェック", self.health_check),
            ("17. 設定を保存して終了", None),
            ("18. 保存せずに終了", None)
        ]
        
        # Draw menu
        menu_y = 4
        selectable_items = []
        item_positions = {}
        
        for idx, (text, action) in enumerate(menu_items):
            if action is None and not text.startswith("━"):
                continue
                
            if text.startswith("━"):
                # Section header
                stdscr.addstr(menu_y, 4, text, curses.A_DIM)
            else:
                # Selectable item
                item_positions[len(selectable_items)] = (menu_y, text, action)
                selectable_items.append((text, action))
                
                if len(selectable_items) - 1 == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(menu_y, 4, f"> {text}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(menu_y, 4, f"  {text}")
            
            menu_y += 1
        
        # Status bar
        self._draw_status_bar(stdscr, h)
        
        return selectable_items
    
    def _draw_status_bar(self, stdscr, h):
        """Draw status bar with current status"""
        mode = self.config['monitoring']['mode']
        mode_color = curses.color_pair(2) if mode == 'production' else curses.color_pair(3)
        
        # Mode
        stdscr.addstr(h - 4, 2, f"モード: ", curses.A_BOLD)
        stdscr.addstr(h - 4, 10, mode.upper(), mode_color | curses.A_BOLD)
        
        # Sources status
        active_sources = sum(1 for v in self.config['sources'].values() if v)
        total_sources = len(self.config['sources'])
        stdscr.addstr(h - 4, 25, f"ソース: {active_sources}/{total_sources}")
        
        # Slack status
        slack_status = "有効" if self.config['slack']['enabled'] else "無効"
        slack_color = curses.color_pair(2) if self.config['slack']['enabled'] else curses.color_pair(4)
        stdscr.addstr(h - 4, 45, f"Slack: ", curses.A_BOLD)
        stdscr.addstr(h - 4, 52, slack_status, slack_color)
        
        # Navigation help
        stdscr.addstr(h - 2, 2, "↑↓: 移動  Enter: 選択  q: 終了")
    
    def config_filters(self, stdscr):
        """Configure filtering settings"""
        stdscr.clear()
        stdscr.addstr(1, 2, "フィルター設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        settings = [
            ('confidence_threshold', '信頼度しきい値 (%)'),
            ('priority_only', '優先ターゲットのみ'),
            ('severity_levels', '重要度レベル')
        ]
        
        current_row = 0
        
        while True:
            for idx, (key, label) in enumerate(settings):
                y = 4 + idx * 2
                value = self.config['filters'][key]
                
                if key == 'priority_only':
                    value = '有効' if value else '無効'
                elif key == 'severity_levels':
                    value = ', '.join(value)
                
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
                if setting_key == 'priority_only':
                    self.config['filters']['priority_only'] = not self.config['filters']['priority_only']
                elif setting_key == 'confidence_threshold':
                    self._edit_number_value(stdscr, 'filters', setting_key, label, 0, 100)
                elif setting_key == 'severity_levels':
                    self._edit_severity_levels(stdscr)
    
    def _edit_severity_levels(self, stdscr):
        """Edit severity levels filter"""
        stdscr.clear()
        stdscr.addstr(1, 2, "重要度レベル設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        levels = ['HIGH', 'MEDIUM', 'LOW', 'INFO']
        current_levels = self.config['filters']['severity_levels']
        
        stdscr.addstr(4, 2, "Spaceで選択/解除:")
        
        for idx, level in enumerate(levels):
            y = 6 + idx
            checked = level in current_levels
            checkbox = "[x]" if checked else "[ ]"
            stdscr.addstr(y, 4, f"{checkbox} {level}")
        
        stdscr.addstr(12, 2, "Space: 切替  ESC: 完了")
        
        current_row = 0
        
        while True:
            # Highlight current row
            for idx, level in enumerate(levels):
                y = 6 + idx
                checked = level in current_levels
                checkbox = "[x]" if checked else "[ ]"
                
                if idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 4, f"{checkbox} {level}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 4, f"{checkbox} {level}")
            
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(levels) - 1:
                current_row += 1
            elif key == 32:  # Space
                level = levels[current_row]
                if level in current_levels:
                    current_levels.remove(level)
                else:
                    current_levels.append(level)
    
    def config_external_apis(self, stdscr):
        """Configure external API endpoints"""
        stdscr.clear()
        stdscr.addstr(1, 2, "外部API設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        stdscr.addstr(4, 2, "1. Nitterインスタンス管理")
        stdscr.addstr(5, 2, "2. セキュリティサイト管理")
        stdscr.addstr(6, 2, "3. Torディレクトリ管理")
        stdscr.addstr(8, 2, "ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == ord('1'):
                self._manage_list_config(stdscr, 'nitter_instances', 'Nitterインスタンス')
            elif key == ord('2'):
                self._manage_dict_config(stdscr, 'security_sites', 'セキュリティサイト')
            elif key == ord('3'):
                self._manage_list_config(stdscr, 'tor_directories', 'Torディレクトリ')
    
    def _manage_list_config(self, stdscr, key, title):
        """Manage list configuration"""
        stdscr.clear()
        stdscr.addstr(1, 2, f"{title}管理", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        items = self.config['external_apis'][key]
        current_row = 0
        
        while True:
            # Display items
            for idx, item in enumerate(items):
                y = 4 + idx
                if idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {item[:60]}...")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 2, f"  {item[:60]}...")
            
            # Instructions
            y = max(5 + len(items), 10)
            stdscr.addstr(y, 2, "A: 追加  D: 削除  E: 編集  ESC: 戻る")
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(items) - 1:
                current_row += 1
            elif key in [ord('a'), ord('A')]:
                # Add new item
                new_item = self._get_string_input(stdscr, f"新しい{title}")
                if new_item:
                    items.append(new_item)
            elif key in [ord('d'), ord('D')] and items:
                # Delete current item
                if current_row < len(items):
                    del items[current_row]
                    if current_row >= len(items) and current_row > 0:
                        current_row -= 1
            elif key in [ord('e'), ord('E')] and items:
                # Edit current item
                if current_row < len(items):
                    new_value = self._get_string_input(stdscr, f"{title}を編集", items[current_row])
                    if new_value:
                        items[current_row] = new_value
    
    def config_api_keys(self, stdscr):
        """Configure API keys"""
        stdscr.clear()
        stdscr.addstr(1, 2, "APIキー管理", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        api_keys = list(self.config['api_keys'].items())
        current_row = 0
        
        while True:
            for idx, (api_name, api_key) in enumerate(api_keys):
                y = 4 + idx
                # Mask API key
                masked_key = api_key[:8] + "..." if api_key else "(未設定)"
                
                if idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {api_name.upper()}: {masked_key}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 2, f"  {api_name.upper()}: {masked_key}")
            
            stdscr.addstr(12, 2, "↑↓: 移動  Enter: 編集  C: クリア  ESC: 戻る")
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(api_keys) - 1:
                current_row += 1
            elif key == 10:  # Enter
                api_name, _ = api_keys[current_row]
                new_key = self._get_string_input(stdscr, f"{api_name.upper()} APIキー", masked=True)
                if new_key is not None:
                    self.config['api_keys'][api_name] = new_key
                    api_keys = list(self.config['api_keys'].items())
            elif key in [ord('c'), ord('C')]:
                api_name, _ = api_keys[current_row]
                self.config['api_keys'][api_name] = ''
                api_keys = list(self.config['api_keys'].items())
    
    def manage_targets(self, stdscr):
        """Manage monitoring targets"""
        stdscr.clear()
        stdscr.addstr(1, 2, "監視対象企業管理", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        categories = [
            ('company_names', '企業名'),
            ('domains', 'ドメイン'),
            ('keywords', 'キーワード')
        ]
        
        current_cat = 0
        
        while True:
            # Display categories
            for idx, (key, label) in enumerate(categories):
                y = 4 + idx
                count = len(self.targets.get(key, []))
                
                if idx == current_cat:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {label} ({count}件)")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 2, f"  {label} ({count}件)")
            
            stdscr.addstr(10, 2, "Enter: 編集  ESC: 戻る")
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_UP and current_cat > 0:
                current_cat -= 1
            elif key == curses.KEY_DOWN and current_cat < len(categories) - 1:
                current_cat += 1
            elif key == 10:  # Enter
                cat_key, cat_label = categories[current_cat]
                self._edit_target_list(stdscr, cat_key, cat_label)
    
    def _edit_target_list(self, stdscr, key, title):
        """Edit target list"""
        stdscr.clear()
        stdscr.addstr(1, 2, f"{title}編集", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        items = self.targets.get(key, [])
        current_row = 0
        
        while True:
            # Display items (with scroll if needed)
            max_display = 15
            start_idx = max(0, current_row - max_display + 1)
            end_idx = min(len(items), start_idx + max_display)
            
            for idx in range(start_idx, end_idx):
                y = 4 + (idx - start_idx)
                if idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {items[idx]}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 2, f"  {items[idx]}")
            
            # Status
            stdscr.addstr(20, 2, f"項目 {current_row + 1}/{len(items)}")
            stdscr.addstr(21, 2, "A: 追加  D: 削除  E: 編集  ESC: 戻る")
            stdscr.refresh()
            
            input_key = stdscr.getch()
            if input_key == 27:  # ESC
                break
            elif input_key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif input_key == curses.KEY_DOWN and current_row < len(items) - 1:
                current_row += 1
            elif input_key in [ord('a'), ord('A')]:
                new_item = self._get_string_input(stdscr, f"新しい{title}")
                if new_item:
                    items.append(new_item)
                    self.targets[key] = items
            elif input_key in [ord('d'), ord('D')] and items:
                if current_row < len(items):
                    del items[current_row]
                    self.targets[key] = items
                    if current_row >= len(items) and current_row > 0:
                        current_row -= 1
            elif input_key in [ord('e'), ord('E')] and items:
                if current_row < len(items):
                    new_value = self._get_string_input(stdscr, f"{title}を編集", items[current_row])
                    if new_value:
                        items[current_row] = new_value
                        self.targets[key] = items
    
    def config_priorities(self, stdscr):
        """Configure target priorities"""
        stdscr.clear()
        stdscr.addstr(1, 2, "優先度設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        # Get all unique targets
        all_targets = set()
        all_targets.update(self.targets.get('company_names', []))
        all_targets.update(self.targets.get('domains', []))
        all_targets.update(self.targets.get('keywords', []))
        
        priority_targets = self.targets.get('priority_targets', {})
        
        # Create list for display
        target_list = sorted(list(all_targets))
        current_row = 0
        
        while True:
            # Display targets with priorities
            max_display = 15
            start_idx = max(0, current_row - max_display + 1)
            end_idx = min(len(target_list), start_idx + max_display)
            
            for idx in range(start_idx, end_idx):
                y = 4 + (idx - start_idx)
                target = target_list[idx]
                priority = priority_targets.get(target, "NORMAL")
                
                # Color based on priority
                if priority == "HIGH":
                    color = curses.color_pair(4)  # Red
                elif priority == "MEDIUM":
                    color = curses.color_pair(3)  # Yellow
                else:
                    color = curses.color_pair(0)  # Normal
                
                if idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {target[:40]}: ")
                    stdscr.attroff(curses.color_pair(1))
                    stdscr.addstr(y, 45, priority, color | curses.A_BOLD)
                else:
                    stdscr.addstr(y, 2, f"  {target[:40]}: ")
                    stdscr.addstr(y, 45, priority, color)
            
            stdscr.addstr(21, 2, "H: HIGH  M: MEDIUM  N: NORMAL  ESC: 戻る")
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(target_list) - 1:
                current_row += 1
            elif key in [ord('h'), ord('H')]:
                target = target_list[current_row]
                priority_targets[target] = "HIGH"
                self.targets['priority_targets'] = priority_targets
            elif key in [ord('m'), ord('M')]:
                target = target_list[current_row]
                priority_targets[target] = "MEDIUM"
                self.targets['priority_targets'] = priority_targets
            elif key in [ord('n'), ord('N')]:
                target = target_list[current_row]
                if target in priority_targets:
                    del priority_targets[target]
                self.targets['priority_targets'] = priority_targets
    
    def view_logs(self, stdscr):
        """View monitoring logs"""
        stdscr.clear()
        stdscr.addstr(1, 2, "ログ表示", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        log_file = 'logs/darkweb_monitor_free.log'
        
        if os.path.exists(log_file):
            # Read last 20 lines
            with open(log_file, 'r') as f:
                lines = f.readlines()
                last_lines = lines[-20:] if len(lines) > 20 else lines
            
            y = 4
            for line in last_lines:
                if y < curses.LINES - 4:
                    # Color based on log level
                    if 'ERROR' in line:
                        stdscr.addstr(y, 2, line.strip()[:curses.COLS-4], curses.color_pair(4))
                    elif 'WARNING' in line:
                        stdscr.addstr(y, 2, line.strip()[:curses.COLS-4], curses.color_pair(3))
                    else:
                        stdscr.addstr(y, 2, line.strip()[:curses.COLS-4])
                    y += 1
        else:
            stdscr.addstr(4, 2, "ログファイルが見つかりません")
        
        stdscr.addstr(curses.LINES - 2, 2, "Enter: 更新  ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == 10:  # Enter
                self.view_logs(stdscr)  # Refresh
                break
    
    def view_statistics(self, stdscr):
        """View monitoring statistics"""
        stdscr.clear()
        stdscr.addstr(1, 2, "統計情報", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        # Calculate statistics
        stats = {
            '監視対象企業数': len(self.targets.get('company_names', [])),
            '監視ドメイン数': len(self.targets.get('domains', [])),
            '監視キーワード数': len(self.targets.get('keywords', [])),
            '優先ターゲット数': len(self.targets.get('priority_targets', {})),
            '有効ソース数': sum(1 for v in self.config['sources'].values() if v),
            '総ソース数': len(self.config['sources']),
            'APIキー設定数': sum(1 for v in self.config['api_keys'].values() if v),
        }
        
        y = 4
        for label, value in stats.items():
            stdscr.addstr(y, 2, f"{label}: {value}")
            y += 1
        
        # Check processed URLs file
        if os.path.exists('processed_urls_free.txt'):
            with open('processed_urls_free.txt', 'r') as f:
                processed_count = len(f.readlines())
            stdscr.addstr(y, 2, f"処理済みURL数: {processed_count}")
        
        stdscr.addstr(curses.LINES - 2, 2, "ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
    
    def health_check(self, stdscr):
        """System health check"""
        stdscr.clear()
        stdscr.addstr(1, 2, "ヘルスチェック", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        checks = []
        y = 4
        
        # Check directories
        for dir_name in ['logs', 'data', 'config']:
            exists = os.path.exists(dir_name)
            status = "✓" if exists else "✗"
            color = curses.color_pair(2) if exists else curses.color_pair(4)
            stdscr.addstr(y, 2, f"{status} ディレクトリ '{dir_name}': ", color)
            stdscr.addstr(y, 25, "存在" if exists else "不在", color)
            y += 1
        
        # Check config files
        for file_name in ['config/targets.json', '.env']:
            exists = os.path.exists(file_name)
            status = "✓" if exists else "✗"
            color = curses.color_pair(2) if exists else curses.color_pair(4)
            stdscr.addstr(y, 2, f"{status} ファイル '{file_name}': ", color)
            stdscr.addstr(y, 30, "存在" if exists else "不在", color)
            y += 1
        
        # Check Slack webhook
        webhook_set = bool(self.config['slack']['webhook_url'])
        status = "✓" if webhook_set else "⚠"
        color = curses.color_pair(2) if webhook_set else curses.color_pair(3)
        stdscr.addstr(y, 2, f"{status} Slack Webhook: ", color)
        stdscr.addstr(y, 25, "設定済み" if webhook_set else "未設定", color)
        y += 1
        
        # Check Python packages
        y += 1
        stdscr.addstr(y, 2, "必須パッケージチェック:", curses.A_BOLD)
        y += 1
        
        packages = ['requests', 'beautifulsoup4', 'fuzzywuzzy', 'schedule', 'python-dotenv']
        for package in packages:
            try:
                __import__(package.replace('-', '_'))
                stdscr.addstr(y, 2, f"✓ {package}", curses.color_pair(2))
            except ImportError:
                stdscr.addstr(y, 2, f"✗ {package}", curses.color_pair(4))
            y += 1
        
        stdscr.addstr(curses.LINES - 2, 2, "ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
    
    def export_import(self, stdscr):
        """Export/Import configuration"""
        stdscr.clear()
        stdscr.addstr(1, 2, "エクスポート/インポート", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        stdscr.addstr(4, 2, "1. 設定をエクスポート")
        stdscr.addstr(5, 2, "2. 設定をインポート")
        stdscr.addstr(7, 2, "ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == ord('1'):
                # Export
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_file = f"config_export_{timestamp}.json"
                
                export_data = {
                    'config': self.config,
                    'targets': self.targets,
                    'timestamp': timestamp
                }
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                stdscr.addstr(9, 2, f"✓ エクスポート完了: {export_file}", curses.color_pair(2))
                stdscr.refresh()
                stdscr.getch()
                break
                
            elif key == ord('2'):
                # Import
                import_file = self._get_string_input(stdscr, "インポートファイル名")
                if import_file and os.path.exists(import_file):
                    try:
                        with open(import_file, 'r', encoding='utf-8') as f:
                            import_data = json.load(f)
                        
                        if 'config' in import_data:
                            self.config = import_data['config']
                        if 'targets' in import_data:
                            self.targets = import_data['targets']
                        
                        stdscr.addstr(9, 2, "✓ インポート完了", curses.color_pair(2))
                    except Exception as e:
                        stdscr.addstr(9, 2, f"✗ インポート失敗: {str(e)}", curses.color_pair(4))
                else:
                    stdscr.addstr(9, 2, "✗ ファイルが見つかりません", curses.color_pair(4))
                
                stdscr.refresh()
                stdscr.getch()
                break
    
    def _get_string_input(self, stdscr, prompt, default="", masked=False):
        """Get string input from user"""
        h, w = stdscr.getmaxyx()
        stdscr.addstr(h - 5, 2, f"{prompt}: ")
        curses.echo()
        
        if masked:
            # For password input
            curses.noecho()
            input_str = ""
            while True:
                key = stdscr.getch()
                if key == 10:  # Enter
                    break
                elif key == 27:  # ESC
                    return None
                elif key in [8, 127]:  # Backspace
                    if input_str:
                        input_str = input_str[:-1]
                        stdscr.addstr(h - 5, len(prompt) + 4 + len(input_str), " ")
                        stdscr.move(h - 5, len(prompt) + 4 + len(input_str))
                elif 32 <= key <= 126:  # Printable characters
                    input_str += chr(key)
                    stdscr.addstr(h - 5, len(prompt) + 4 + len(input_str) - 1, "*")
            value = input_str
        else:
            # Normal input
            stdscr.addstr(h - 5, len(prompt) + 4, default)
            value = stdscr.getstr(h - 5, len(prompt) + 4, 60).decode('utf-8')
            curses.noecho()
        
        return value if value else default
    
    def _edit_number_value(self, stdscr, section, key, label, min_val=0, max_val=999999):
        """Edit numeric value"""
        h, w = stdscr.getmaxyx()
        current_value = str(self.config[section][key])
        
        value = self._get_string_input(stdscr, label, current_value)
        
        if value and value.isdigit():
            num_value = int(value)
            if min_val <= num_value <= max_val:
                self.config[section][key] = num_value
                stdscr.addstr(h - 3, 2, "✓ 更新しました", curses.color_pair(2))
            else:
                stdscr.addstr(h - 3, 2, f"✗ 値は{min_val}〜{max_val}の範囲で入力してください", curses.color_pair(4))
        elif value:
            stdscr.addstr(h - 3, 2, "✗ 数値を入力してください", curses.color_pair(4))
        
        stdscr.refresh()
        stdscr.getch()
    
    def save_all_configs(self):
        """Save all configurations"""
        # Save main config
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        # Save targets
        with open(self.targets_file, 'w', encoding='utf-8') as f:
            json.dump(self.targets, f, ensure_ascii=False, indent=2)
        
        # Save external API config
        os.makedirs('config', exist_ok=True)
        with open(self.external_api_config, 'w') as f:
            json.dump({'external_apis': self.config['external_apis']}, f, indent=2)
        
        # Save environment variables
        self._save_env_vars()
    
    def _save_env_vars(self):
        """Save environment variables"""
        lines = []
        saved_keys = set()
        
        # Read existing file
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key = line.split('=', 1)[0]
                        if key == 'SLACK_WEBHOOK_URL':
                            lines.append(f"SLACK_WEBHOOK_URL={self.config['slack']['webhook_url']}\n")
                            saved_keys.add(key)
                        elif key.endswith('_API_KEY'):
                            api_name = key.replace('_API_KEY', '').lower()
                            if api_name in self.config['api_keys']:
                                lines.append(f"{key}={self.config['api_keys'][api_name]}\n")
                                saved_keys.add(key)
                        else:
                            lines.append(line)
                    else:
                        lines.append(line)
        
        # Add missing keys
        if 'SLACK_WEBHOOK_URL' not in saved_keys:
            lines.append(f"SLACK_WEBHOOK_URL={self.config['slack']['webhook_url']}\n")
        
        for api_name, api_key in self.config['api_keys'].items():
            key = f"{api_name.upper()}_API_KEY"
            if key not in saved_keys and api_key:
                lines.append(f"{key}={api_key}\n")
        
        # Write back
        with open(self.env_file, 'w') as f:
            f.writelines(lines)
    
    # Existing methods from original TUI
    def config_monitoring(self, stdscr):
        """Configure basic monitoring settings"""
        stdscr.clear()
        stdscr.addstr(1, 2, "監視設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        settings = [
            ('interval_minutes', '監視間隔（分）'),
            ('mode', 'モード (simulation/production)'),
            ('max_alerts_per_cycle', '1サイクルの最大アラート数'),
            ('deduplication', '重複除去'),
            ('log_level', 'ログレベル'),
            ('retention_days', 'データ保持期間（日）')
        ]
        
        current_row = 0
        
        while True:
            for idx, (key, label) in enumerate(settings):
                y = 4 + idx
                value = self.config['monitoring'][key]
                
                if key == 'deduplication':
                    value = '有効' if value else '無効'
                
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
                if setting_key == 'deduplication':
                    self.config['monitoring']['deduplication'] = not self.config['monitoring']['deduplication']
                elif setting_key == 'log_level':
                    self._select_log_level(stdscr)
                elif setting_key in ['interval_minutes', 'max_alerts_per_cycle', 'retention_days']:
                    self._edit_number_value(stdscr, 'monitoring', setting_key, label)
                else:
                    value = self._get_string_input(stdscr, label, str(self.config['monitoring'][setting_key]))
                    if value:
                        self.config['monitoring'][setting_key] = value
    
    def _select_log_level(self, stdscr):
        """Select log level"""
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        current_level = self.config['monitoring']['log_level']
        current_idx = levels.index(current_level) if current_level in levels else 1
        
        stdscr.clear()
        stdscr.addstr(1, 2, "ログレベル選択", curses.A_BOLD)
        
        while True:
            for idx, level in enumerate(levels):
                y = 3 + idx
                if idx == current_idx:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {level}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 2, f"  {level}")
            
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == curses.KEY_UP and current_idx > 0:
                current_idx -= 1
            elif key == curses.KEY_DOWN and current_idx < len(levels) - 1:
                current_idx += 1
            elif key == 10:  # Enter
                self.config['monitoring']['log_level'] = levels[current_idx]
                break
    
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
                if y >= curses.LINES - 4:
                    break
                    
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
            
            stdscr.addstr(curses.LINES - 3, 2, "↑↓: 移動  Space: 切替  A: 全て有効  D: 全て無効  ESC: 戻る")
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
            elif key in [ord('a'), ord('A')]:
                for source_key in self.config['sources']:
                    self.config['sources'][source_key] = True
                sources = list(self.config['sources'].items())
            elif key in [ord('d'), ord('D')]:
                for source_key in self.config['sources']:
                    self.config['sources'][source_key] = False
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
        
        # Severity filter
        severity_filter = self.config['slack'].get('severity_filter', ['HIGH', 'MEDIUM', 'LOW'])
        stdscr.addstr(6, 2, f"重要度フィルター: {', '.join(severity_filter)}")
        
        stdscr.addstr(8, 2, "1. 通知を切り替え")
        stdscr.addstr(9, 2, "2. Webhook URLを変更")
        stdscr.addstr(10, 2, "3. 重要度フィルターを設定")
        stdscr.addstr(11, 2, "4. テスト通知を送信")
        stdscr.addstr(13, 2, "ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == ord('1'):
                self.config['slack']['enabled'] = not self.config['slack']['enabled']
                stdscr.addstr(4, 2, f"通知: {'有効' if self.config['slack']['enabled'] else '無効'}     ")
                stdscr.refresh()
            elif key == ord('2'):
                value = self._get_string_input(stdscr, 'Slack Webhook URL', webhook_url)
                if value is not None:
                    self.config['slack']['webhook_url'] = value
                    webhook_url = value
                    stdscr.addstr(5, 2, f"Webhook URL: {webhook_url[:50]}..." if len(webhook_url) > 50 else f"Webhook URL: {webhook_url}     ")
                    stdscr.refresh()
            elif key == ord('3'):
                self._edit_severity_levels(stdscr)
                severity_filter = self.config['slack'].get('severity_filter', ['HIGH', 'MEDIUM', 'LOW'])
                stdscr.addstr(6, 2, f"重要度フィルター: {', '.join(severity_filter)}     ")
                stdscr.refresh()
            elif key == ord('4'):
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
    'source': 'TUI設定画面（拡張版）',
    'severity': 'INFO',
    'confidence_score': 100,
    'raw_text': 'これは拡張版TUI設定画面からのテスト通知です。'
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
            ('port', 'ポート'),
            ('username', 'ユーザー名'),
            ('password', 'パスワード')
        ]
        
        current_row = 0
        
        while True:
            for idx, (key, label) in enumerate(settings):
                y = 4 + idx
                value = self.config['proxy'][key]
                
                if key == 'enabled':
                    value = '有効' if value else '無効'
                elif key == 'password' and value:
                    value = '*' * 8
                
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
                if setting_key == 'enabled':
                    self.config['proxy']['enabled'] = not self.config['proxy']['enabled']
                elif setting_key == 'port':
                    self._edit_number_value(stdscr, 'proxy', setting_key, label, 1, 65535)
                elif setting_key == 'password':
                    value = self._get_string_input(stdscr, label, masked=True)
                    if value is not None:
                        self.config['proxy'][setting_key] = value
                else:
                    value = self._get_string_input(stdscr, label, str(self.config['proxy'][setting_key]))
                    if value is not None:
                        self.config['proxy'][setting_key] = value
    
    def config_nitter(self, stdscr):
        """Configure Nitter instances"""
        self._manage_list_config(stdscr, 'nitter_instances', 'Nitterインスタンス')
    
    def config_storage(self, stdscr):
        """Configure storage settings"""
        stdscr.clear()
        stdscr.addstr(1, 2, "ストレージ設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        # Elasticsearch settings
        es_enabled = self.config['storage']['elasticsearch']['enabled']
        es_host = self.config['storage']['elasticsearch']['host']
        es_port = self.config['storage']['elasticsearch']['port']
        
        # Local DB settings
        local_enabled = self.config['storage']['local_db']['enabled']
        local_path = self.config['storage']['local_db']['path']
        
        stdscr.addstr(4, 2, "Elasticsearch:")
        stdscr.addstr(5, 4, f"状態: {'有効' if es_enabled else '無効'}")
        stdscr.addstr(6, 4, f"ホスト: {es_host}:{es_port}")
        
        stdscr.addstr(8, 2, "ローカルDB:")
        stdscr.addstr(9, 4, f"状態: {'有効' if local_enabled else '無効'}")
        stdscr.addstr(10, 4, f"パス: {local_path}")
        
        stdscr.addstr(12, 2, "1. Elasticsearch設定")
        stdscr.addstr(13, 2, "2. ローカルDB設定")
        stdscr.addstr(15, 2, "ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == ord('1'):
                self._config_elasticsearch(stdscr)
                # Refresh display
                es_enabled = self.config['storage']['elasticsearch']['enabled']
                es_host = self.config['storage']['elasticsearch']['host']
                es_port = self.config['storage']['elasticsearch']['port']
                stdscr.addstr(5, 4, f"状態: {'有効' if es_enabled else '無効'}     ")
                stdscr.addstr(6, 4, f"ホスト: {es_host}:{es_port}     ")
                stdscr.refresh()
            elif key == ord('2'):
                self._config_local_db(stdscr)
                # Refresh display
                local_enabled = self.config['storage']['local_db']['enabled']
                local_path = self.config['storage']['local_db']['path']
                stdscr.addstr(9, 4, f"状態: {'有効' if local_enabled else '無効'}     ")
                stdscr.addstr(10, 4, f"パス: {local_path}     ")
                stdscr.refresh()
    
    def _config_elasticsearch(self, stdscr):
        """Configure Elasticsearch settings"""
        es_config = self.config['storage']['elasticsearch']
        
        stdscr.clear()
        stdscr.addstr(1, 2, "Elasticsearch設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        settings = [
            ('enabled', '有効/無効'),
            ('host', 'ホスト'),
            ('port', 'ポート'),
            ('index', 'インデックス名')
        ]
        
        current_row = 0
        
        while True:
            for idx, (key, label) in enumerate(settings):
                y = 4 + idx
                value = es_config[key]
                
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
                    es_config['enabled'] = not es_config['enabled']
                elif setting_key == 'port':
                    value = self._get_string_input(stdscr, label, str(es_config['port']))
                    if value and value.isdigit():
                        es_config['port'] = int(value)
                else:
                    value = self._get_string_input(stdscr, label, str(es_config[setting_key]))
                    if value:
                        es_config[setting_key] = value
    
    def _config_local_db(self, stdscr):
        """Configure local database settings"""
        local_config = self.config['storage']['local_db']
        
        stdscr.clear()
        stdscr.addstr(1, 2, "ローカルDB設定", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        stdscr.addstr(4, 2, f"状態: {'有効' if local_config['enabled'] else '無効'}")
        stdscr.addstr(5, 2, f"パス: {local_config['path']}")
        
        stdscr.addstr(7, 2, "1. 有効/無効を切り替え")
        stdscr.addstr(8, 2, "2. パスを変更")
        stdscr.addstr(10, 2, "ESC: 戻る")
        
        while True:
            key = stdscr.getch()
            if key == 27:  # ESC
                break
            elif key == ord('1'):
                local_config['enabled'] = not local_config['enabled']
                stdscr.addstr(4, 2, f"状態: {'有効' if local_config['enabled'] else '無効'}     ")
                stdscr.refresh()
            elif key == ord('2'):
                value = self._get_string_input(stdscr, 'DBパス', local_config['path'])
                if value:
                    local_config['path'] = value
                    stdscr.addstr(5, 2, f"パス: {local_config['path']}     ")
                    stdscr.refresh()
    
    def _manage_dict_config(self, stdscr, key, title):
        """Manage dictionary configuration"""
        stdscr.clear()
        stdscr.addstr(1, 2, f"{title}管理", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        items = list(self.config['external_apis'][key].items())
        current_row = 0
        
        while True:
            # Display items
            for idx, (name, url) in enumerate(items):
                y = 4 + idx
                if idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, 2, f"> {name}: {url[:40]}...")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, 2, f"  {name}: {url[:40]}...")
            
            # Instructions
            y = max(5 + len(items), 10)
            stdscr.addstr(y, 2, "A: 追加  D: 削除  E: URL編集  ESC: 戻る")
            stdscr.refresh()
            
            input_key = stdscr.getch()
            if input_key == 27:  # ESC
                break
            elif input_key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif input_key == curses.KEY_DOWN and current_row < len(items) - 1:
                current_row += 1
            elif input_key in [ord('a'), ord('A')]:
                # Add new item
                name = self._get_string_input(stdscr, "サイト名")
                if name:
                    url = self._get_string_input(stdscr, "URL")
                    if url:
                        self.config['external_apis'][key][name] = url
                        items = list(self.config['external_apis'][key].items())
            elif input_key in [ord('d'), ord('D')] and items:
                # Delete current item
                if current_row < len(items):
                    name, _ = items[current_row]
                    del self.config['external_apis'][key][name]
                    items = list(self.config['external_apis'][key].items())
                    if current_row >= len(items) and current_row > 0:
                        current_row -= 1
            elif input_key in [ord('e'), ord('E')] and items:
                # Edit URL
                if current_row < len(items):
                    name, old_url = items[current_row]
                    new_url = self._get_string_input(stdscr, f"{name}のURL", old_url)
                    if new_url:
                        self.config['external_apis'][key][name] = new_url
                        items = list(self.config['external_apis'][key].items())
    
    def start_monitoring(self, stdscr):
        """Start monitoring"""
        stdscr.clear()
        stdscr.addstr(1, 2, "監視を開始", curses.A_BOLD)
        stdscr.addstr(2, 2, "=" * 40)
        
        mode = self.config['monitoring']['mode']
        interval = self.config['monitoring']['interval_minutes']
        
        stdscr.addstr(4, 2, f"モード: {mode}")
        stdscr.addstr(5, 2, f"間隔: {interval}分")
        
        # Show active sources
        active_sources = [k for k, v in self.config['sources'].items() if v]
        stdscr.addstr(7, 2, "有効なソース:")
        for idx, source in enumerate(active_sources[:5]):
            stdscr.addstr(8 + idx, 4, f"• {source}")
        if len(active_sources) > 5:
            stdscr.addstr(13, 4, f"... 他 {len(active_sources) - 5} 件")
        
        stdscr.addstr(15, 2, "監視を開始しますか？")
        stdscr.addstr(17, 2, "Y: はい  N: いいえ")
        
        key = stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            self.save_all_configs()
            stdscr.addstr(19, 2, "設定を保存しました", curses.color_pair(2))
            stdscr.addstr(20, 2, "監視を開始します...", curses.color_pair(3))
            stdscr.refresh()
            
            # Exit curses mode
            curses.endwin()
            
            # Start monitoring
            if mode == 'simulation':
                os.system('source venv/bin/activate && python run_with_simulation.py')
            else:
                os.system(f'source venv/bin/activate && python scripts/start_monitoring_free.py --interval {interval}')
            
            sys.exit(0)
    
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
                menu_items = self.draw_main_menu(stdscr, current_row)
                
                key = stdscr.getch()
                
                if key == curses.KEY_UP and current_row > 0:
                    current_row -= 1
                elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
                    current_row += 1
                elif key == 10:  # Enter
                    _, action = menu_items[current_row]
                    
                    if current_row == len(menu_items) - 2:  # Save and exit
                        self.save_all_configs()
                        break
                    elif current_row == len(menu_items) - 1:  # Exit without saving
                        break
                    elif action:
                        action(stdscr)
                elif key in [ord('q'), ord('Q'), 27]:  # q or ESC
                    break
        
        curses.wrapper(main)


if __name__ == "__main__":
    tui = AdvancedMonitoringTUI()
    tui.run()