import hashlib
import time
import requests
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)

class HaveIBeenPwnedClient:
    """
    Have I Been Pwned (HIBP) - 無料API
    メールアドレスの漏洩チェックに特化
    """
    
    def __init__(self):
        self.base_url = "https://haveibeenpwned.com/api/v3"
        self.headers = {
            'User-Agent': 'DarkwebMonitor-JP/1.0',
            'hibp-api-key': ''  # HIBP now requires API key for some endpoints
        }
        # HIBP requires 6 seconds between requests for unauthenticated use
        self.rate_limit_delay = 6
        self.last_request_time = 0
    
    def check_email_breach(self, email: str) -> List[Dict[str, Any]]:
        """
        Check if email has been in any breaches
        
        Args:
            email: Email address to check
            
        Returns:
            List of breaches
        """
        # Rate limiting
        self._rate_limit()
        
        endpoint = f"{self.base_url}/breachedaccount/{quote(email)}"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                params={'truncateResponse': 'false'},
                timeout=30
            )
            
            if response.status_code == 404:
                # No breaches found
                return []
            elif response.status_code == 200:
                breaches = response.json()
                return self._normalize_hibp_results(breaches, email)
            else:
                logger.error(f"HIBP API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error checking HIBP: {e}")
            return []
    
    def _normalize_hibp_results(self, breaches: List[Dict], email: str) -> List[Dict[str, Any]]:
        """Normalize HIBP results to standard format"""
        normalized = []
        
        for breach in breaches:
            breach_date = breach.get('BreachDate', '')
            data_classes = breach.get('DataClasses', [])
            
            # Determine severity based on exposed data
            severity = "LOW"
            if "Passwords" in data_classes:
                severity = "HIGH"
            elif any(item in data_classes for item in ["Credit cards", "Bank accounts", "Social security numbers"]):
                severity = "HIGH"
            elif "Email addresses" in data_classes:
                severity = "MEDIUM"
            
            normalized_entry = {
                "source": "HaveIBeenPwned",
                "matched_term": email,
                "raw_text": f"Email {email} found in {breach.get('Title', 'Unknown')} breach. "
                           f"Exposed data: {', '.join(data_classes)}. "
                           f"Total {breach.get('PwnCount', 0):,} accounts affected.",
                "title": f"Breach Alert: {breach.get('Title', 'Unknown')}",
                "url": f"https://haveibeenpwned.com/breach/{breach.get('Name', '')}",
                "timestamp": datetime.utcnow().isoformat(),
                "discovered_date": breach_date,
                "severity": severity,
                "category": "Email Breach",
                "metadata": {
                    "breach_name": breach.get('Name'),
                    "breach_domain": breach.get('Domain'),
                    "pwn_count": breach.get('PwnCount', 0),
                    "is_verified": breach.get('IsVerified', False),
                    "data_classes": data_classes
                }
            }
            
            normalized.append(normalized_entry)
        
        return normalized
    
    def _rate_limit(self):
        """Implement HIBP rate limiting (6 seconds between requests)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class IntelligenceXFreeClient:
    """
    IntelligenceX Free Tier
    2週間の無料トライアル、その後も限定的な無料検索可能
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key  # Optional for free tier
        self.base_url = "https://public.intelx.io"
        self.headers = {
            'User-Agent': 'DarkwebMonitor-JP/1.0'
        }
    
    def search_free(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using IntelligenceX free/public interface
        
        Args:
            query: Search term
            
        Returns:
            Search results
        """
        # IntelligenceX public search endpoint
        search_url = f"{self.base_url}/search"
        
        try:
            # This is a simplified implementation
            # Real implementation would need to handle their search flow
            logger.info(f"Searching IntelligenceX for: {query}")
            
            # Placeholder results for now
            # In production, would parse their HTML or use their limited API
            return []
            
        except Exception as e:
            logger.error(f"IntelligenceX search error: {e}")
            return []


class GitHubSearchClient:
    """
    GitHub Code Search - 完全無料
    公開リポジトリでの企業情報漏洩を検出
    """
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'DarkwebMonitor-JP/1.0'
        }
        # GitHub allows 10 requests per minute for unauthenticated
        self.rate_limit_delay = 6
        self.last_request_time = 0
    
    def search_code(self, query: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Search GitHub code for sensitive information
        
        Args:
            query: Search query (e.g., "sony.co.jp password")
            limit: Maximum results
            
        Returns:
            List of findings
        """
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_request_time < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - (current_time - self.last_request_time))
        
        endpoint = f"{self.base_url}/search/code"
        
        # Add filters to find potential leaks
        enhanced_query = f'{query} (password OR api_key OR secret OR token OR credential)'
        
        params = {
            'q': enhanced_query,
            'per_page': min(limit, 100),
            'sort': 'indexed',
            'order': 'desc'
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                return self._normalize_github_results(data.get('items', []), query)
            else:
                logger.error(f"GitHub API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"GitHub search error: {e}")
            return []
    
    def _normalize_github_results(self, items: List[Dict], query: str) -> List[Dict[str, Any]]:
        """Normalize GitHub search results"""
        normalized = []
        
        for item in items:
            # Check if it looks like a credential leak
            severity = "LOW"
            if any(word in item.get('name', '').lower() for word in ['password', 'secret', 'token', 'key']):
                severity = "MEDIUM"
            
            normalized_entry = {
                "source": "GitHub",
                "matched_term": query,
                "raw_text": f"Found in {item.get('repository', {}).get('full_name', 'Unknown repo')}: "
                           f"{item.get('name', 'Unknown file')}. "
                           f"Path: {item.get('path', 'Unknown path')}",
                "title": f"GitHub: Potential exposure in {item.get('repository', {}).get('name', 'Unknown')}",
                "url": item.get('html_url', ''),
                "timestamp": datetime.utcnow().isoformat(),
                "discovered_date": datetime.utcnow().isoformat(),
                "severity": severity,
                "category": "Code Repository",
                "metadata": {
                    "repository": item.get('repository', {}).get('full_name'),
                    "file_path": item.get('path'),
                    "file_name": item.get('name'),
                    "sha": item.get('sha')
                }
            }
            
            normalized.append(normalized_entry)
        
        return normalized


class PastebinMonitor:
    """
    Pastebin monitoring through Google Custom Search
    完全無料だが制限あり
    """
    
    def __init__(self):
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        # Google Custom Search allows 100 queries/day for free
        self.daily_limit = 100
        self.queries_today = 0
    
    def search_pastebin(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Pastebin via Google
        
        Args:
            query: Search term
            
        Returns:
            Pastebin findings
        """
        if self.queries_today >= self.daily_limit:
            logger.warning("Daily Google search limit reached")
            return []
        
        # Use site-specific search
        search_query = f'site:pastebin.com "{query}"'
        
        # This would need Google Custom Search API key for production
        # For now, return empty list
        logger.info(f"Would search Pastebin for: {query}")
        self.queries_today += 1
        
        return []


def search_free_sources(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    Search all free sources for targets
    
    Args:
        targets_file: Path to targets.json
        
    Returns:
        Combined results from all free sources
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
    hibp = HaveIBeenPwnedClient()
    github = GitHubSearchClient()
    
    # Check domains with GitHub
    for domain in targets.get('domains', [])[:5]:  # Limit to avoid rate limits
        logger.info(f"Searching GitHub for: {domain}")
        results = github.search_code(domain, limit=10)
        all_results.extend(results)
    
    # Check specific email patterns with HIBP
    # (In production, would get actual employee emails from config)
    for domain in targets.get('domains', [])[:3]:
        test_emails = [
            f"admin@{domain}",
            f"info@{domain}",
            f"support@{domain}"
        ]
        
        for email in test_emails:
            logger.info(f"Checking HIBP for: {email}")
            breaches = hibp.check_email_breach(email)
            all_results.extend(breaches)
    
    return all_results


if __name__ == "__main__":
    # Test free APIs
    
    # Test HIBP
    hibp = HaveIBeenPwnedClient()
    test_email = "test@example.com"
    breaches = hibp.check_email_breach(test_email)
    print(f"HIBP found {len(breaches)} breaches for {test_email}")
    
    # Test GitHub
    github = GitHubSearchClient()
    results = github.search_code("example.com password", limit=5)
    print(f"GitHub found {len(results)} potential exposures")