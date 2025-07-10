import requests
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

class AhmiaAdapter:
    """
    Ahmia.fi adapter for searching Tor hidden services
    Ahmia is a search engine for Tor hidden services that indexes .onion sites
    """
    
    def __init__(self):
        self.base_url = "https://ahmia.fi"
        self.search_endpoint = f"{self.base_url}/search/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2  # seconds between requests
    
    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search Ahmia for specific query terms
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of normalized search results
        """
        # Rate limiting
        self._rate_limit()
        
        try:
            # Ahmia search parameters
            params = {
                'q': query,
                'page': 1
            }
            
            all_results = []
            page = 1
            
            while len(all_results) < limit and page <= 5:  # Max 5 pages
                params['page'] = page
                
                response = requests.get(
                    self.search_endpoint,
                    params=params,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code != 200:
                    logger.error(f"Ahmia search failed with status: {response.status_code}")
                    break
                
                # Parse HTML response (Ahmia returns HTML, not JSON)
                results = self._parse_html_results(response.text, query)
                
                if not results:
                    break
                
                all_results.extend(results)
                page += 1
                
                # Rate limiting between pages
                if page <= 5:
                    time.sleep(1)
            
            # Limit results
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching Ahmia: {e}")
            return []
    
    def _parse_html_results(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """
        Parse HTML search results from Ahmia
        
        Args:
            html_content: HTML response from Ahmia
            query: Original search query
            
        Returns:
            List of parsed results
        """
        results = []
        
        try:
            # Simple HTML parsing without BeautifulSoup to avoid dependency
            # Look for result entries in the HTML
            
            # Split by result divs (this is a simplified parser)
            result_blocks = html_content.split('<li class="result"')
            
            for block in result_blocks[1:]:  # Skip first split
                result = self._extract_result_from_block(block, query)
                if result:
                    results.append(result)
        
        except Exception as e:
            logger.error(f"Error parsing Ahmia HTML: {e}")
        
        return results
    
    def _extract_result_from_block(self, block: str, query: str) -> Optional[Dict[str, Any]]:
        """
        Extract result data from HTML block
        
        Args:
            block: HTML block containing one result
            query: Original search query
            
        Returns:
            Normalized result or None
        """
        try:
            # Extract URL
            url_start = block.find('href="') + 6
            url_end = block.find('"', url_start)
            if url_start < 6 or url_end < 0:
                return None
            
            url = block[url_start:url_end]
            
            # Convert Ahmia redirect URL to actual onion URL
            if '/search/redirect?search_term=' in url:
                # Extract actual onion URL from redirect
                onion_start = url.find('redirect_url=') + 13
                url = url[onion_start:]
                if '&' in url:
                    url = url[:url.find('&')]
            
            # Extract title
            title_start = block.find('<h4>') + 4
            title_end = block.find('</h4>', title_start)
            title = block[title_start:title_end] if title_start > 4 and title_end > 0 else "No title"
            
            # Extract description/snippet
            desc_start = block.find('<p class="description">') + 23
            desc_end = block.find('</p>', desc_start)
            description = block[desc_start:desc_end] if desc_start > 23 and desc_end > 0 else ""
            
            # Clean up HTML entities
            title = self._clean_html_text(title)
            description = self._clean_html_text(description)
            
            # Create normalized result
            normalized_result = {
                "source": "Ahmia",
                "matched_term": query,
                "raw_text": description,
                "title": title,
                "url": url,
                "timestamp": datetime.utcnow().isoformat(),
                "discovered_date": datetime.utcnow().isoformat(),
                "site_type": "tor_hidden_service",
                "language": "unknown",
                "metadata": {
                    "search_engine": "ahmia.fi",
                    "is_onion": url.endswith('.onion')
                }
            }
            
            return normalized_result
            
        except Exception as e:
            logger.debug(f"Failed to extract result from block: {e}")
            return None
    
    def _clean_html_text(self, text: str) -> str:
        """Clean HTML entities and tags from text"""
        # Basic HTML entity replacement
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        
        # Remove any remaining HTML tags
        while '<' in text and '>' in text:
            start = text.find('<')
            end = text.find('>', start)
            if start >= 0 and end > start:
                text = text[:start] + text[end+1:]
            else:
                break
        
        return text.strip()
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to Ahmia"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_onion_info(self, onion_url: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific .onion site
        
        Args:
            onion_url: The .onion URL to get info about
            
        Returns:
            Site information or None
        """
        # Search for the specific onion domain
        domain = onion_url.replace('http://', '').replace('https://', '').split('/')[0]
        results = self.search(domain, limit=1)
        
        if results:
            return results[0]
        return None


# Convenience function for integration
def search_ahmia(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    Search Ahmia for all targets
    
    Args:
        targets_file: Path to targets.json file
        
    Returns:
        Combined results for all targets
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
    
    adapter = AhmiaAdapter()
    all_results = []
    
    # Search for each keyword
    for keyword in targets.get('keywords', []):
        logger.info(f"Searching Ahmia for: {keyword}")
        results = adapter.search(keyword, limit=20)  # Limit per keyword
        all_results.extend(results)
        
        # Be nice to Ahmia
        time.sleep(2)
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_results = []
    for result in all_results:
        if result['url'] not in seen_urls:
            seen_urls.add(result['url'])
            unique_results.append(result)
    
    return unique_results


if __name__ == "__main__":
    # Test the adapter
    adapter = AhmiaAdapter()
    
    # Test search
    test_results = adapter.search("bitcoin", limit=5)
    print(f"Found {len(test_results)} results for 'bitcoin'")
    
    for result in test_results:
        print(f"- {result['title'][:50]}... | {result['url']}")