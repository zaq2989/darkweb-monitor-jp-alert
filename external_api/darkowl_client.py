import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class DarkOwlClient:
    def __init__(self):
        self.api_key = os.getenv('DARKOWL_API_KEY')
        if not self.api_key:
            raise ValueError("DARKOWL_API_KEY not found in environment variables")
        
        self.base_url = "https://api.darkowl.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def search(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search DarkOwl for specific query terms
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
        
        Returns:
            List of search results
        """
        endpoint = f"{self.base_url}/search"
        
        payload = {
            "query": query,
            "limit": limit,
            "sort": "date_discovered",
            "order": "desc"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return self._normalize_results(data.get('results', []), query)
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying DarkOwl API: {e}")
            return []
    
    def _normalize_results(self, results: List[Dict], query: str) -> List[Dict[str, Any]]:
        """
        Normalize DarkOwl results to standard format
        
        Args:
            results: Raw results from DarkOwl API
            query: Original search query
        
        Returns:
            Normalized results
        """
        normalized = []
        
        for result in results:
            normalized_entry = {
                "source": "DarkOwl",
                "matched_term": query,
                "raw_text": result.get('content', ''),
                "title": result.get('title', ''),
                "url": result.get('url', ''),
                "timestamp": datetime.utcnow().isoformat(),
                "discovered_date": result.get('date_discovered', ''),
                "site_name": result.get('site_name', ''),
                "site_type": result.get('site_type', ''),
                "language": result.get('language', ''),
                "metadata": {
                    "darkowl_id": result.get('id', ''),
                    "relevance_score": result.get('relevance_score', 0)
                }
            }
            normalized.append(normalized_entry)
        
        return normalized


def query_darkowl(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    Query DarkOwl API for all targets
    
    Args:
        targets_file: Path to targets.json file
    
    Returns:
        Combined results for all targets
    """
    if targets_file is None:
        targets_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'targets.json')
    
    # Load targets
    with open(targets_file, 'r', encoding='utf-8') as f:
        targets = json.load(f)
    
    client = DarkOwlClient()
    all_results = []
    
    # Search for each keyword
    for keyword in targets.get('keywords', []):
        print(f"Searching DarkOwl for: {keyword}")
        results = client.search(keyword)
        all_results.extend(results)
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_results = []
    for result in all_results:
        if result['url'] not in seen_urls:
            seen_urls.add(result['url'])
            unique_results.append(result)
    
    return unique_results


if __name__ == "__main__":
    # Test the client
    results = query_darkowl()
    print(f"Found {len(results)} unique results")
    for result in results[:5]:  # Print first 5 results
        print(f"- {result['matched_term']} | {result['title'][:50]}...")