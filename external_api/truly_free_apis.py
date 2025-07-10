"""
完全無料で使えるAPIとWebスクレイピング
認証不要のソースのみ使用
"""
import requests
import json
import time
import logging
from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import quote
import re

logger = logging.getLogger(__name__)

class DuckDuckGoSearch:
    """
    DuckDuckGo HTML search - 完全無料、API不要
    """
    def __init__(self):
        self.base_url = "https://duckduckgo.com/html/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search DuckDuckGo for darkweb mentions"""
        try:
            # Search for darkweb/onion mentions
            search_query = f'{query} (darkweb OR "dark web" OR onion OR tor)'
            
            params = {
                'q': search_query,
                'kl': 'jp-jp'  # Japanese region
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return self._parse_results(response.text, query)
            else:
                logger.error(f"DuckDuckGo search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def _parse_results(self, html: str, query: str) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo HTML results"""
        results = []
        
        # Simple HTML parsing for result snippets
        result_pattern = r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]+)</a>'
        
        matches = re.findall(result_pattern, html, re.DOTALL)
        
        for url, title, snippet in matches[:20]:  # Limit results
            # Check if it's potentially darkweb related
            if any(word in snippet.lower() for word in ['onion', 'tor', 'darkweb', 'dark web', 'leak', '漏洩']):
                severity = "MEDIUM"
                if any(word in snippet.lower() for word in ['password', 'credential', 'breach', 'dump']):
                    severity = "HIGH"
                
                results.append({
                    "source": "DuckDuckGo",
                    "matched_term": query,
                    "raw_text": snippet,
                    "title": title,
                    "url": url,
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": severity,
                    "category": "Web Search"
                })
        
        return results


class PublicPastebinSearch:
    """
    Pastebin public pastes - trending/recent pastes
    完全無料、認証不要
    """
    def __init__(self):
        self.base_url = "https://pastebin.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_recent(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Check recent public pastes for keywords"""
        results = []
        
        try:
            # Get recent pastes page
            response = requests.get(
                f"{self.base_url}/archive",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                # Extract paste IDs from archive
                paste_ids = re.findall(r'href="/([a-zA-Z0-9]{8})"', response.text)[:10]
                
                for paste_id in paste_ids:
                    time.sleep(1)  # Be nice to Pastebin
                    
                    # Get raw paste content
                    raw_url = f"{self.base_url}/raw/{paste_id}"
                    try:
                        paste_response = requests.get(raw_url, headers=self.headers, timeout=10)
                        if paste_response.status_code == 200:
                            content = paste_response.text[:5000]  # Limit content size
                            
                            # Check for keywords
                            for keyword in keywords:
                                if keyword.lower() in content.lower():
                                    results.append({
                                        "source": "Pastebin",
                                        "matched_term": keyword,
                                        "raw_text": self._extract_context(content, keyword),
                                        "title": f"Pastebin: {paste_id}",
                                        "url": f"{self.base_url}/{paste_id}",
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "severity": "MEDIUM",
                                        "category": "Paste Site"
                                    })
                                    break
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"Pastebin search error: {e}")
        
        return results
    
    def _extract_context(self, content: str, keyword: str, context_size: int = 200) -> str:
        """Extract context around keyword"""
        lower_content = content.lower()
        lower_keyword = keyword.lower()
        
        pos = lower_content.find(lower_keyword)
        if pos == -1:
            return content[:context_size]
        
        start = max(0, pos - context_size // 2)
        end = min(len(content), pos + len(keyword) + context_size // 2)
        
        return "..." + content[start:end] + "..."


class URLHausAbuse:
    """
    URLHaus by abuse.ch - マルウェアURL無料データベース
    日本企業を装ったフィッシングサイトを検出
    """
    def __init__(self):
        self.base_url = "https://urlhaus-api.abuse.ch/v1"
        self.headers = {
            'User-Agent': 'DarkwebMonitor-JP/1.0'
        }
    
    def check_domain_abuse(self, domain: str) -> List[Dict[str, Any]]:
        """Check if domain is being abused in phishing/malware"""
        try:
            # Search for URLs containing the domain
            response = requests.post(
                f"{self.base_url}/host/",
                data={'host': domain},
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('query_status') == 'ok' and data.get('urls'):
                    return self._parse_urlhaus_results(data['urls'], domain)
            
            return []
            
        except Exception as e:
            logger.error(f"URLHaus API error: {e}")
            return []
    
    def _parse_urlhaus_results(self, urls: List[Dict], domain: str) -> List[Dict[str, Any]]:
        """Parse URLHaus results"""
        results = []
        
        for url_data in urls[:10]:  # Limit results
            results.append({
                "source": "URLHaus",
                "matched_term": domain,
                "raw_text": f"Malicious URL detected: {url_data.get('url', '')}. "
                           f"Threat: {url_data.get('threat', 'Unknown')}. "
                           f"Tags: {', '.join(url_data.get('tags', []))}",
                "title": f"Phishing/Malware: {domain}",
                "url": url_data.get('url', ''),
                "timestamp": datetime.utcnow().isoformat(),
                "discovered_date": url_data.get('date_added', ''),
                "severity": "HIGH",
                "category": "Malware/Phishing",
                "metadata": {
                    "threat_type": url_data.get('threat'),
                    "tags": url_data.get('tags', []),
                    "urlhaus_reference": url_data.get('urlhaus_reference', '')
                }
            })
        
        return results


def search_truly_free_sources(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    完全無料のソースのみで検索
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
    
    all_results = []
    
    # Initialize clients
    ddg = DuckDuckGoSearch()
    pastebin = PublicPastebinSearch()
    urlhaus = URLHausAbuse()
    
    # Search with DuckDuckGo
    for keyword in targets.get('keywords', [])[:5]:  # Limit searches
        logger.info(f"Searching DuckDuckGo for: {keyword}")
        results = ddg.search(keyword)
        all_results.extend(results)
        time.sleep(2)  # Be respectful
    
    # Check recent Pastebin
    logger.info("Checking recent Pastebin posts...")
    paste_results = pastebin.search_recent(targets.get('keywords', [])[:10])
    all_results.extend(paste_results)
    
    # Check URLHaus for domain abuse
    for domain in targets.get('domains', [])[:5]:
        logger.info(f"Checking URLHaus for domain abuse: {domain}")
        abuse_results = urlhaus.check_domain_abuse(domain)
        all_results.extend(abuse_results)
        time.sleep(1)
    
    return all_results


if __name__ == "__main__":
    # Test free sources
    results = search_truly_free_sources()
    print(f"Found {len(results)} results from truly free sources")
    
    for result in results[:5]:
        print(f"- [{result['source']}] {result['title'][:50]}...")
        print(f"  Severity: {result['severity']}")