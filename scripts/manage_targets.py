#!/usr/bin/env python3
"""
監視対象管理ツール
targets.jsonの編集、優先度設定、カテゴリ管理
"""
import os
import sys
import json
import argparse
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TargetManager:
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'config',
                'targets.json'
            )
        self.config_file = config_file
        self.load_targets()
    
    def load_targets(self):
        """Load current targets from file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.targets = json.load(f)
        except FileNotFoundError:
            self.targets = {
                "keywords": [],
                "domains": [],
                "company_names": [],
                "priority_targets": {},
                "categories": {}
            }
    
    def save_targets(self):
        """Save targets to file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.targets, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved to {self.config_file}")
    
    def list_targets(self, category: str = None):
        """List all targets or by category"""
        print("\n=== Current Monitoring Targets ===\n")
        
        if category:
            if category in self.targets:
                print(f"{category.upper()}:")
                for item in self.targets[category]:
                    priority = self.get_priority(item)
                    print(f"  - {item} {f'[{priority}]' if priority else ''}")
        else:
            for cat in ['keywords', 'domains', 'company_names']:
                if cat in self.targets and self.targets[cat]:
                    print(f"{cat.upper()}:")
                    for item in self.targets[cat]:
                        priority = self.get_priority(item)
                        category_name = self.get_category(item)
                        info = []
                        if priority:
                            info.append(f"Priority: {priority}")
                        if category_name:
                            info.append(f"Category: {category_name}")
                        
                        info_str = f" ({', '.join(info)})" if info else ""
                        print(f"  - {item}{info_str}")
                    print()
        
        # Show priority targets
        if self.targets.get('priority_targets'):
            print("PRIORITY TARGETS:")
            for target, priority in self.targets['priority_targets'].items():
                print(f"  - {target}: {priority}")
            print()
        
        # Show categories
        if self.targets.get('categories'):
            print("CATEGORIES:")
            for target, category in self.targets['categories'].items():
                print(f"  - {target}: {category}")
    
    def add_target(self, target: str, target_type: str, priority: str = None, category: str = None):
        """Add a new target"""
        if target_type not in ['keywords', 'domains', 'company_names']:
            print(f"❌ Invalid type: {target_type}")
            return
        
        if target not in self.targets[target_type]:
            self.targets[target_type].append(target)
            print(f"✓ Added '{target}' to {target_type}")
        else:
            print(f"⚠️  '{target}' already exists in {target_type}")
        
        if priority:
            self.set_priority(target, priority)
        
        if category:
            self.set_category(target, category)
        
        self.save_targets()
    
    def remove_target(self, target: str):
        """Remove a target from all lists"""
        removed = False
        
        for target_type in ['keywords', 'domains', 'company_names']:
            if target in self.targets[target_type]:
                self.targets[target_type].remove(target)
                print(f"✓ Removed '{target}' from {target_type}")
                removed = True
        
        # Remove from priority and categories
        if 'priority_targets' in self.targets and target in self.targets['priority_targets']:
            del self.targets['priority_targets'][target]
        
        if 'categories' in self.targets and target in self.targets['categories']:
            del self.targets['categories'][target]
        
        if removed:
            self.save_targets()
        else:
            print(f"❌ '{target}' not found")
    
    def set_priority(self, target: str, priority: str):
        """Set priority for a target (HIGH, MEDIUM, LOW)"""
        if priority.upper() not in ['HIGH', 'MEDIUM', 'LOW']:
            print(f"❌ Invalid priority: {priority}")
            return
        
        if 'priority_targets' not in self.targets:
            self.targets['priority_targets'] = {}
        
        self.targets['priority_targets'][target] = priority.upper()
        print(f"✓ Set priority for '{target}' to {priority.upper()}")
        self.save_targets()
    
    def set_category(self, target: str, category: str):
        """Set category for a target"""
        if 'categories' not in self.targets:
            self.targets['categories'] = {}
        
        self.targets['categories'][target] = category
        print(f"✓ Set category for '{target}' to '{category}'")
        self.save_targets()
    
    def get_priority(self, target: str) -> str:
        """Get priority of a target"""
        return self.targets.get('priority_targets', {}).get(target, '')
    
    def get_category(self, target: str) -> str:
        """Get category of a target"""
        return self.targets.get('categories', {}).get(target, '')
    
    def import_targets(self, filename: str):
        """Import targets from a file (one per line)"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            imported = 0
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Detect type
                if '.' in line and not ' ' in line:
                    target_type = 'domains'
                elif any(c in line for c in ['株式会社', '会社', '自動車', '銀行']):
                    target_type = 'company_names'
                else:
                    target_type = 'keywords'
                
                if line not in self.targets[target_type]:
                    self.targets[target_type].append(line)
                    imported += 1
            
            self.save_targets()
            print(f"✓ Imported {imported} new targets")
            
        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
    
    def export_targets(self, filename: str, priority_only: bool = False):
        """Export targets to a file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Darkweb Monitor Targets Export\n")
            f.write(f"# Priority only: {priority_only}\n\n")
            
            for cat in ['keywords', 'domains', 'company_names']:
                f.write(f"# {cat.upper()}\n")
                for item in self.targets.get(cat, []):
                    priority = self.get_priority(item)
                    
                    if priority_only and priority != 'HIGH':
                        continue
                    
                    category_name = self.get_category(item)
                    info = []
                    if priority:
                        info.append(f"Priority: {priority}")
                    if category_name:
                        info.append(f"Category: {category_name}")
                    
                    info_str = f" # {', '.join(info)}" if info else ""
                    f.write(f"{item}{info_str}\n")
                f.write("\n")
        
        print(f"✓ Exported to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Manage darkweb monitoring targets')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all targets')
    list_parser.add_argument('-c', '--category', help='Filter by category')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new target')
    add_parser.add_argument('target', help='Target to add')
    add_parser.add_argument('-t', '--type', 
                          choices=['keywords', 'domains', 'company_names'],
                          required=True, help='Target type')
    add_parser.add_argument('-p', '--priority',
                          choices=['HIGH', 'MEDIUM', 'LOW'],
                          help='Set priority')
    add_parser.add_argument('-c', '--category', help='Set category')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a target')
    remove_parser.add_argument('target', help='Target to remove')
    
    # Priority command
    priority_parser = subparsers.add_parser('priority', help='Set target priority')
    priority_parser.add_argument('target', help='Target')
    priority_parser.add_argument('level', choices=['HIGH', 'MEDIUM', 'LOW'])
    
    # Category command
    category_parser = subparsers.add_parser('category', help='Set target category')
    category_parser.add_argument('target', help='Target')
    category_parser.add_argument('name', help='Category name')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import targets from file')
    import_parser.add_argument('filename', help='File to import (one target per line)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export targets to file')
    export_parser.add_argument('filename', help='Output filename')
    export_parser.add_argument('--priority-only', action='store_true',
                             help='Export only high priority targets')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = TargetManager()
    
    if args.command == 'list':
        manager.list_targets(args.category)
    
    elif args.command == 'add':
        manager.add_target(args.target, args.type, args.priority, args.category)
    
    elif args.command == 'remove':
        manager.remove_target(args.target)
    
    elif args.command == 'priority':
        manager.set_priority(args.target, args.level)
    
    elif args.command == 'category':
        manager.set_category(args.target, args.name)
    
    elif args.command == 'import':
        manager.import_targets(args.filename)
    
    elif args.command == 'export':
        manager.export_targets(args.filename, args.priority_only)


if __name__ == '__main__':
    main()