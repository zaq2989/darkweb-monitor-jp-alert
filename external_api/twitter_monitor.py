"""
Twitter/X モニタリング（Nitter経由）
APIキー不要でTwitterを監視
"""
import requests
import json
import logging
import time
import re
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
import random

logger = logging.getLogger(__name__)

class TwitterMonitor:
    """
    Twitter/X監視（Nitterインスタンス経由）
    """
    
    def __init__(self):
        # 公開Nitterインスタンス（定期的に変更が必要）
        self.nitter_instances = [
            "https://nitter.net",
            "https://nitter.privacydev.net", 
            "https://nitter.poast.org",
            "https://nitter.esmailelbob.xyz",
            "https://nitter.mint.lgbt"
        ]
        
        # 監視すべきセキュリティ関連アカウント
        self.security_accounts = [
            "malwarebytes",
            "threatpost", 
            "TheHackersNews",
            "bleepincomputer",
            "DarkWebInformer",
            "IntelligenceX"
        ]
        
        # 日本のセキュリティアカウント
        self.jp_security_accounts = [
            "IPA_anshin",      # IPA
            "nisc_forecast",   # NISC
            "jpcert_ac",       # JPCERT
            "lac_security",    # LAC
            "npa_koho"         # 警察庁
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _get_working_instance(self) -> str:
        """動作するNitterインスタンスを見つける"""
        for instance in self.nitter_instances:
            try:
                response = self.session.get(instance, timeout=10)
                if response.status_code == 200:
                    return instance
            except:
                continue
        
        logger.error("No working Nitter instance found")
        return self.nitter_instances[0]  # フォールバック
    
    def search_tweets(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """キーワードでツイートを検索"""
        results = []
        instance = self._get_working_instance()
        
        for keyword in keywords[:5]:  # 制限
            try:
                # Nitter検索URL
                search_url = f"{instance}/search"
                params = {
                    'q': keyword,
                    'f': 'tweets',  # ツイートのみ
                    'since': '',
                    'until': '',
                    'near': ''
                }
                
                response = self.session.get(search_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # ツイートを抽出
                    tweets = soup.find_all('div', class_='timeline-item')
                    
                    for tweet in tweets[:10]:  # 最新10件
                        try:
                            # ユーザー名
                            username_elem = tweet.find('a', class_='username')
                            username = username_elem.text if username_elem else 'unknown'
                            
                            # ツイート内容
                            content_elem = tweet.find('div', class_='tweet-content')
                            content = content_elem.text if content_elem else ''
                            
                            # 日時
                            time_elem = tweet.find('span', class_='tweet-date')
                            tweet_time = time_elem.get('title', '') if time_elem else ''
                            
                            # リンク
                            link_elem = tweet.find('a', class_='tweet-link')
                            tweet_link = instance + link_elem['href'] if link_elem else ''
                            
                            # 重要度判定
                            severity = self._determine_severity(content)
                            
                            results.append({
                                "source": f"Twitter-{username}",
                                "matched_term": keyword,
                                "raw_text": content[:500],
                                "title": f"Tweet by @{username}",
                                "url": tweet_link,
                                "timestamp": datetime.utcnow().isoformat(),
                                "discovered_date": tweet_time,
                                "severity": severity,
                                "category": "twitter",
                                "metadata": {
                                    "username": username,
                                    "platform": "twitter",
                                    "via": "nitter"
                                }
                            })
                            
                        except Exception as e:
                            logger.debug(f"Failed to parse tweet: {e}")
                
                # レート制限対策
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                logger.error(f"Error searching Twitter for '{keyword}': {e}")
        
        return results
    
    def monitor_security_accounts(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """セキュリティアカウントの投稿を監視"""
        results = []
        instance = self._get_working_instance()
        
        all_accounts = self.security_accounts + self.jp_security_accounts
        
        for account in all_accounts[:10]:  # 制限
            try:
                # アカウントのタイムライン
                account_url = f"{instance}/{account}"
                response = self.session.get(account_url, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    tweets = soup.find_all('div', class_='timeline-item')
                    
                    for tweet in tweets[:5]:  # 最新5件
                        content_elem = tweet.find('div', class_='tweet-content')
                        if content_elem:
                            content = content_elem.text.lower()
                            
                            # キーワードチェック
                            matched_keywords = []
                            for keyword in keywords:
                                if keyword.lower() in content:
                                    matched_keywords.append(keyword)
                            
                            if matched_keywords:
                                # ツイート情報を抽出
                                time_elem = tweet.find('span', class_='tweet-date')
                                tweet_time = time_elem.get('title', '') if time_elem else ''
                                
                                link_elem = tweet.find('a', class_='tweet-link')
                                tweet_link = instance + link_elem['href'] if link_elem else ''
                                
                                results.append({
                                    "source": f"Twitter-{account}",
                                    "matched_term": ", ".join(matched_keywords),
                                    "raw_text": content_elem.text[:500],
                                    "title": f"Security Alert from @{account}",
                                    "url": tweet_link,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "discovered_date": tweet_time,
                                    "severity": "HIGH" if account in self.jp_security_accounts else "MEDIUM",
                                    "category": "security_twitter",
                                    "metadata": {
                                        "account": account,
                                        "is_jp_security": account in self.jp_security_accounts
                                    }
                                })
                
                # レート制限対策
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.debug(f"Error monitoring account {account}: {e}")
        
        return results
    
    def _determine_severity(self, text: str) -> str:
        """ツイート内容から重要度を判定"""
        text_lower = text.lower()
        
        # 高優先度キーワード
        high_keywords = ['breach', 'leak', 'hack', 'compromise', 'attack', 
                        '漏洩', '流出', '攻撃', '侵入', '被害']
        
        # 中優先度キーワード  
        medium_keywords = ['vulnerability', 'security', 'warning', 'alert',
                          '脆弱性', '注意', '警告', 'セキュリティ']
        
        if any(keyword in text_lower for keyword in high_keywords):
            return "HIGH"
        elif any(keyword in text_lower for keyword in medium_keywords):
            return "MEDIUM"
        else:
            return "LOW"
    
    def search_darkweb_mentions(self) -> List[Dict[str, Any]]:
        """ダークウェブ関連の投稿を検索"""
        darkweb_queries = [
            "darkweb leak",
            "dark web breach", 
            "onion site hack",
            "tor market",
            "ダークウェブ 漏洩",
            "闇サイト"
        ]
        
        results = []
        instance = self._get_working_instance()
        
        for query in darkweb_queries:
            try:
                search_url = f"{instance}/search"
                params = {'q': query, 'f': 'tweets'}
                
                response = self.session.get(search_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    tweets = soup.find_all('div', class_='timeline-item')
                    
                    for tweet in tweets[:3]:  # 各クエリで3件まで
                        content_elem = tweet.find('div', class_='tweet-content')
                        if content_elem:
                            results.append({
                                "source": "Twitter-DarkwebSearch",
                                "matched_term": query,
                                "raw_text": content_elem.text[:500],
                                "title": f"Darkweb mention: {query}",
                                "url": instance + "/search?q=" + query,
                                "timestamp": datetime.utcnow().isoformat(),
                                "severity": "HIGH",
                                "category": "darkweb_twitter"
                            })
                
                time.sleep(random.uniform(3, 5))
                
            except Exception as e:
                logger.debug(f"Error searching for {query}: {e}")
        
        return results


def monitor_twitter(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    Twitter監視のメイン関数
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
    
    keywords = (
        targets.get('keywords', [])[:10] +
        targets.get('domains', [])[:10] +
        targets.get('company_names', [])[:10]
    )
    
    monitor = TwitterMonitor()
    all_results = []
    
    # キーワード検索
    logger.info("Searching Twitter for keywords...")
    keyword_results = monitor.search_tweets(keywords[:5])
    all_results.extend(keyword_results)
    
    # セキュリティアカウント監視
    logger.info("Monitoring security accounts...")
    account_results = monitor.monitor_security_accounts(keywords)
    all_results.extend(account_results)
    
    # ダークウェブ関連検索
    logger.info("Searching for darkweb mentions...")
    darkweb_results = monitor.search_darkweb_mentions()
    all_results.extend(darkweb_results)
    
    return all_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test Twitter monitoring
    results = monitor_twitter()
    
    print(f"Found {len(results)} results from Twitter")
    for result in results[:5]:
        print(f"- [{result['source']}] {result['title']}")
        print(f"  Matched: {result['matched_term']}")
        print(f"  Severity: {result['severity']}")