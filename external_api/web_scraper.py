"""
Webスクレイピングベースの情報収集
プロキシ対応、User-Agent偽装、エラーハンドリング強化
"""
import requests
import json
import time
import random
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class RobustWebScraper:
    """
    堅牢なWebスクレイピング
    """
    
    def __init__(self, use_proxy: bool = False):
        self.session = requests.Session()
        
        # User-Agent リスト（ランダム選択）
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        # プロキシ設定（オプション）
        if use_proxy:
            self.proxies = {
                'http': 'socks5://127.0.0.1:9050',
                'https': 'socks5://127.0.0.1:9050'
            }
        else:
            self.proxies = None
        
        # デフォルトヘッダー
        self.default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """ランダムなUser-Agentでヘッダーを生成"""
        headers = self.default_headers.copy()
        headers['User-Agent'] = random.choice(self.user_agents)
        return headers
    
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """エラーハンドリング付きリクエスト"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if self.proxies:
                    kwargs['proxies'] = self.proxies
                
                kwargs['headers'] = kwargs.get('headers', self._get_headers())
                kwargs['timeout'] = kwargs.get('timeout', 30)
                kwargs['verify'] = kwargs.get('verify', False)  # SSL検証をスキップ
                
                if method == 'GET':
                    response = self.session.get(url, **kwargs)
                else:
                    response = self.session.post(url, **kwargs)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limit
                    wait_time = retry_delay * (attempt + 1)
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        return None


class GoogleSearchScraper(RobustWebScraper):
    """
    Google検索経由での情報収集
    """
    
    def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Google検索（CSE不要）"""
        results = []
        
        # ダークウェブ関連のクエリを追加
        enhanced_query = f'{query} (darkweb OR "dark web" OR breach OR leak OR ダークウェブ OR 漏洩)'
        
        # Google検索URL
        search_url = "https://www.google.com/search"
        params = {
            'q': enhanced_query,
            'num': num_results,
            'hl': 'ja'
        }
        
        response = self._make_request(search_url, method='GET', params=params)
        
        if response and response.text:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 検索結果を抽出
            for g in soup.find_all('div', class_='g'):
                try:
                    # タイトルとURL
                    title_elem = g.find('h3')
                    link_elem = g.find('a', href=True)
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text()
                        url = link_elem['href']
                        
                        # スニペット
                        snippet_elem = g.find('span', class_='aCOpRe') or g.find('div', class_='VwiC3b')
                        snippet = snippet_elem.get_text() if snippet_elem else ""
                        
                        result = {
                            "source": "Google",
                            "matched_term": query,
                            "raw_text": snippet,
                            "title": title,
                            "url": url,
                            "timestamp": datetime.utcnow().isoformat(),
                            "severity": self._determine_severity(title + " " + snippet),
                            "category": "web_search"
                        }
                        results.append(result)
                        
                except Exception as e:
                    logger.debug(f"Failed to parse result: {e}")
        
        return results
    
    def _determine_severity(self, text: str) -> str:
        """重要度判定"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['breach', 'leak', 'hack', 'password', '漏洩', '流出']):
            return "HIGH"
        elif any(word in text_lower for word in ['vulnerability', 'security', 'exploit']):
            return "MEDIUM"
        return "LOW"


class TorProjectScraper(RobustWebScraper):
    """
    Tor関連サイトの情報収集
    """
    
    def __init__(self):
        super().__init__(use_proxy=False)  # 通常のWebからアクセス
        
        # Torプロジェクト関連の情報源
        self.tor_sources = [
            {
                "name": "Dark.fail",
                "url": "https://dark.fail",
                "type": "directory"
            },
            {
                "name": "Tor Metrics",
                "url": "https://metrics.torproject.org",
                "type": "statistics"
            }
        ]
    
    def search_tor_mentions(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Tor関連サイトでキーワード検索"""
        results = []
        
        # dark.fail のミラーサイトをチェック
        darkfail_mirrors = [
            "https://darkfailenbsdla5mal2mxn2uz66od5vtzd5qozslagrfzachha3f3id.onion.ws",
            "https://darkfailenbsdla5mal2mxn2uz66od5vtzd5qozslagrfzachha3f3id.onion.ly"
        ]
        
        for mirror in darkfail_mirrors:
            try:
                response = self._make_request(mirror)
                if response and response.text:
                    # キーワードチェック
                    for keyword in keywords:
                        if keyword.lower() in response.text.lower():
                            results.append({
                                "source": "Dark.fail",
                                "matched_term": keyword,
                                "raw_text": f"Keyword '{keyword}' found in Tor directory listings",
                                "title": f"Tor Directory Mention: {keyword}",
                                "url": mirror,
                                "timestamp": datetime.utcnow().isoformat(),
                                "severity": "MEDIUM",
                                "category": "tor_directory"
                            })
                    break
            except:
                continue
        
        return results


class SecurityNewsScraper(RobustWebScraper):
    """
    セキュリティニュースサイトのスクレイピング
    """
    
    def __init__(self):
        super().__init__()
        
        # 日本のセキュリティニュースサイト
        self.jp_sources = [
            {
                "name": "Security NEXT",
                "url": "https://www.security-next.com",
                "search_path": "/search.php?q="
            },
            {
                "name": "ITmedia Security",
                "url": "https://www.itmedia.co.jp/enterprise/subtop/security/",
                "type": "static"
            },
            {
                "name": "IPA Security Center",
                "url": "https://www.ipa.go.jp/security/",
                "type": "static"
            }
        ]
    
    def search_japanese_sources(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """日本のセキュリティニュースを検索"""
        results = []
        
        for source in self.jp_sources:
            try:
                if source.get('search_path'):
                    # 検索機能があるサイト
                    for keyword in keywords[:5]:  # 制限
                        search_url = source['url'] + source['search_path'] + quote(keyword)
                        response = self._make_request(search_url)
                        
                        if response and response.text:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            # サイト固有のパース処理
                            # ...
                else:
                    # 静的ページのチェック
                    response = self._make_request(source['url'])
                    if response and response.text:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        text_content = soup.get_text().lower()
                        
                        for keyword in keywords:
                            if keyword.lower() in text_content:
                                results.append({
                                    "source": source['name'],
                                    "matched_term": keyword,
                                    "raw_text": f"Keyword '{keyword}' found on {source['name']}",
                                    "title": f"Security News Mention: {keyword}",
                                    "url": source['url'],
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "severity": "MEDIUM",
                                    "category": "security_news_jp"
                                })
                
                # レート制限
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {e}")
        
        return results


def scrape_web_sources(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    すべてのWebソースをスクレイピング
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
    
    all_results = []
    
    # Google検索
    google_scraper = GoogleSearchScraper()
    for keyword in keywords[:5]:  # 制限
        logger.info(f"Searching Google for: {keyword}")
        results = google_scraper.search(keyword, num_results=5)
        all_results.extend(results)
        time.sleep(random.uniform(5, 10))  # Google対策
    
    # Tor関連
    tor_scraper = TorProjectScraper()
    logger.info("Checking Tor directories...")
    tor_results = tor_scraper.search_tor_mentions(keywords[:10])
    all_results.extend(tor_results)
    
    # 日本のセキュリティニュース
    news_scraper = SecurityNewsScraper()
    logger.info("Checking Japanese security news...")
    news_results = news_scraper.search_japanese_sources(keywords[:10])
    all_results.extend(news_results)
    
    return all_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test scraping
    results = scrape_web_sources()
    
    print(f"Found {len(results)} results from web scraping")
    for result in results[:5]:
        print(f"- [{result['source']}] {result['title'][:60]}...")
        print(f"  Severity: {result['severity']}")