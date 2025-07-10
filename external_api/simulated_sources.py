"""
外部ソースシミュレーター
実際の外部APIの代わりにリアルなデータを生成
"""
import random
import json
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class SimulatedExternalSources:
    """
    外部ソースのシミュレーション
    本番環境では実際のAPIに置き換え
    """
    
    def __init__(self):
        # シミュレーション用のテンプレート
        self.breach_templates = [
            {
                "title": "{company} Database Leak Found on Dark Web Forum",
                "content": "A database containing {records} records from {company} has been discovered on a popular dark web forum. The data includes email addresses, hashed passwords, and user information.",
                "severity": "HIGH"
            },
            {
                "title": "Credentials for {company} Employees Exposed",
                "content": "Employee credentials for {company} were found in a recent ComboList release. The list contains {records} email/password combinations.",
                "severity": "HIGH"
            },
            {
                "title": "{company} Mentioned in Underground Forum",
                "content": "Discussion about {company} security practices observed in hacking forum. No immediate threat identified.",
                "severity": "LOW"
            },
            {
                "title": "Vulnerability in {company} Systems Discussed",
                "content": "Security researchers discussing potential vulnerability in {company} infrastructure. Patch status unknown.",
                "severity": "MEDIUM"
            }
        ]
        
        self.sources = [
            "DarkWeb-Forum-Alpha", "Underground-Market-Beta", "Breach-Database-X",
            "Security-Research-Forum", "Telegram-DarkChannel", "Reddit-r/darknet",
            "Twitter-@DarkWebNews", "Pastebin-Anonymous", "GitHub-Gist-Leak"
        ]
        
        self.random = random.Random()
        self.generated_count = 0
    
    def generate_results(self, keywords: List[str], count: int = 5) -> List[Dict[str, Any]]:
        """
        キーワードに基づいてリアルなシミュレーション結果を生成
        """
        results = []
        
        # 各キーワードに対してランダムに結果を生成
        for keyword in keywords[:10]:  # 最大10キーワード
            # 30%の確率で結果を生成
            if self.random.random() > 0.7:
                continue
            
            # 1-3件の結果を生成
            num_results = self.random.randint(1, min(3, count))
            
            for _ in range(num_results):
                template = self.random.choice(self.breach_templates)
                source = self.random.choice(self.sources)
                
                # ユニークなIDを生成
                unique_id = hashlib.md5(
                    f"{keyword}{source}{self.generated_count}".encode()
                ).hexdigest()[:8]
                
                self.generated_count += 1
                
                # 日時をランダムに生成（過去7日以内）
                days_ago = self.random.randint(0, 7)
                discovered_date = datetime.utcnow() - timedelta(days=days_ago)
                
                # レコード数をランダムに生成
                records = self.random.choice([
                    "1,000", "5,000", "10,000", "50,000", "100,000", "500,000"
                ])
                
                # 結果を生成
                result = {
                    "source": source,
                    "matched_term": keyword,
                    "raw_text": template["content"].format(
                        company=keyword,
                        records=records
                    ),
                    "title": template["title"].format(company=keyword),
                    "url": f"http://simulated{unique_id}.onion/{keyword.replace(' ', '_')}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "discovered_date": discovered_date.isoformat(),
                    "severity": template["severity"],
                    "category": "simulated",
                    "metadata": {
                        "simulation": True,
                        "unique_id": unique_id,
                        "records_affected": records
                    }
                }
                
                results.append(result)
                
                if len(results) >= count:
                    return results
        
        # 日本特有の脅威もシミュレート
        if self.random.random() > 0.5:
            jp_threats = [
                {
                    "company": "金融機関",
                    "content": "日本の主要銀行を標的としたフィッシングキャンペーンが確認されました。{keyword}も標的リストに含まれています。",
                    "severity": "HIGH"
                },
                {
                    "company": "製造業",
                    "content": "{keyword}の技術文書と思われるファイルがダークウェブ上で取引されているとの情報。真偽は不明。",
                    "severity": "MEDIUM"
                }
            ]
            
            for keyword in keywords[:3]:
                if "銀行" in keyword or "金融" in keyword or "bank" in keyword.lower():
                    threat = jp_threats[0]
                else:
                    threat = jp_threats[1]
                
                result = {
                    "source": "JP-ThreatIntel",
                    "matched_term": keyword,
                    "raw_text": threat["content"].format(keyword=keyword),
                    "title": f"Japanese Threat Intel: {keyword}",
                    "url": f"http://jpthreat{self.generated_count}.onion",
                    "timestamp": datetime.utcnow().isoformat(),
                    "discovered_date": datetime.utcnow().isoformat(),
                    "severity": threat["severity"],
                    "category": "jp_threat_intel",
                    "metadata": {
                        "simulation": True,
                        "region": "Japan"
                    }
                }
                results.append(result)
                self.generated_count += 1
        
        return results[:count]
    
    def get_status(self) -> Dict[str, Any]:
        """シミュレーターの状態を返す"""
        return {
            "status": "active",
            "mode": "simulation",
            "generated_count": self.generated_count,
            "message": "Using simulated data - replace with real APIs in production"
        }


# 実際のAPIが使えない場合のフォールバック
def get_external_results(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    外部ソースから結果を取得（シミュレーション版）
    """
    if targets_file is None:
        import os
        targets_file = os.path.join(
            os.path.dirname(__file__),
            '..',
            'config',
            'targets.json'
        )
    
    # Load targets
    with open(targets_file, 'r', encoding='utf-8') as f:
        targets = json.load(f)
    
    # 優先度の高いターゲットを抽出
    high_priority_targets = []
    priority_targets = targets.get('priority_targets', {})
    
    for target, priority in priority_targets.items():
        if priority == "HIGH":
            high_priority_targets.append(target)
    
    # その他のキーワードも追加
    all_keywords = (
        high_priority_targets +
        targets.get('keywords', [])[:10] +
        targets.get('domains', [])[:10] +
        targets.get('company_names', [])[:10]
    )
    
    # 重複を削除
    unique_keywords = list(dict.fromkeys(all_keywords))
    
    # シミュレーターで結果を生成
    simulator = SimulatedExternalSources()
    results = simulator.generate_results(unique_keywords[:20], count=10)
    
    logger.info(f"Simulated {len(results)} external source results")
    logger.info(f"Simulator status: {simulator.get_status()}")
    
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test simulation
    results = get_external_results()
    
    print(f"Generated {len(results)} simulated results")
    print("\nSample results:")
    for result in results[:5]:
        print(f"- [{result['source']}] {result['title']}")
        print(f"  Severity: {result['severity']}")
        print(f"  URL: {result['url']}")
        print()