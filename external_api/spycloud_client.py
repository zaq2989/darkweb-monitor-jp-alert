import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class SpyCloudClient:
    """
    SpyCloud API client for monitoring compromised credentials and PII
    SpyCloud specializes in detecting exposed employee credentials from breaches
    """
    
    def __init__(self):
        self.api_key = os.getenv('SPYCLOUD_API_KEY')
        if not self.api_key:
            logger.warning("SPYCLOUD_API_KEY not found. SpyCloud monitoring disabled.")
            self.enabled = False
            return
        
        self.enabled = True
        self.base_url = "https://api.spycloud.io/enterprise/v2"
        self.headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def check_domain_exposure(self, domain: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Check for exposed credentials associated with a domain
        
        Args:
            domain: Company domain to check (e.g., "sony.co.jp")
            days_back: Number of days to look back
            
        Returns:
            List of exposed credential records
        """
        if not self.enabled:
            return []
        
        endpoint = f"{self.base_url}/breach/data/domain"
        
        # Calculate date range
        since_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        params = {
            "domain": domain,
            "since": since_date,
            "severity": "2,3",  # Medium and High severity
            "limit": 100
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            return self._normalize_credential_results(results, domain)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SpyCloud API error for domain {domain}: {e}")
            return []
    
    def check_email_exposure(self, email: str) -> List[Dict[str, Any]]:
        """
        Check if specific email has been exposed in breaches
        
        Args:
            email: Email address to check
            
        Returns:
            List of breach records
        """
        if not self.enabled:
            return []
        
        endpoint = f"{self.base_url}/breach/data/email"
        
        params = {
            "email": email,
            "limit": 50
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            return self._normalize_credential_results(results, email)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SpyCloud API error for email {email}: {e}")
            return []
    
    def get_watchlist_alerts(self, watchlist_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get alerts from SpyCloud watchlists
        
        Args:
            watchlist_id: Specific watchlist ID (optional)
            
        Returns:
            List of watchlist alerts
        """
        if not self.enabled:
            return []
        
        endpoint = f"{self.base_url}/watchlist/alerts"
        
        params = {}
        if watchlist_id:
            params['watchlist_id'] = watchlist_id
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            alerts = data.get('alerts', [])
            
            normalized_alerts = []
            for alert in alerts:
                normalized = self._normalize_watchlist_alert(alert)
                if normalized:
                    normalized_alerts.append(normalized)
            
            return normalized_alerts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SpyCloud watchlist API error: {e}")
            return []
    
    def _normalize_credential_results(self, results: List[Dict], search_term: str) -> List[Dict[str, Any]]:
        """
        Normalize SpyCloud credential results to standard format
        
        Args:
            results: Raw results from SpyCloud
            search_term: Original search term
            
        Returns:
            Normalized results
        """
        normalized = []
        
        for result in results:
            # Extract breach information
            breach_title = result.get('breach_title', 'Unknown Breach')
            breach_date = result.get('spycloud_publish_date', '')
            severity = result.get('severity', 1)
            
            # Extract exposed data
            email = result.get('email', '')
            username = result.get('username', '')
            domain = result.get('domain', '')
            password = result.get('password', '[REDACTED]')
            plaintext_password = result.get('password_plaintext', False)
            
            # Build description
            exposed_items = []
            if email:
                exposed_items.append(f"Email: {email}")
            if username:
                exposed_items.append(f"Username: {username}")
            if plaintext_password:
                exposed_items.append("Password: EXPOSED IN PLAINTEXT")
            elif password:
                exposed_items.append("Password: EXPOSED (hashed)")
            
            description = f"Breach: {breach_title}. Exposed data: {', '.join(exposed_items)}"
            
            # Map SpyCloud severity to our severity levels
            severity_map = {
                3: "HIGH",      # Critical
                2: "MEDIUM",    # High
                1: "LOW"        # Medium/Low
            }
            
            normalized_entry = {
                "source": "SpyCloud",
                "matched_term": search_term,
                "raw_text": description,
                "title": f"Credential Exposure: {breach_title}",
                "url": f"spycloud:breach:{result.get('id', 'unknown')}",
                "timestamp": datetime.utcnow().isoformat(),
                "discovered_date": breach_date,
                "site_type": "credential_monitoring",
                "severity": severity_map.get(severity, "MEDIUM"),
                "category": "Credential Breach",
                "metadata": {
                    "breach_id": result.get('breach_id'),
                    "breach_title": breach_title,
                    "email": email,
                    "domain": domain,
                    "has_plaintext_password": plaintext_password,
                    "infected_machine": result.get('infected_machine_id') is not None,
                    "target_url": result.get('target_url', ''),
                    "severity_score": severity
                }
            }
            
            normalized.append(normalized_entry)
        
        return normalized
    
    def _normalize_watchlist_alert(self, alert: Dict) -> Optional[Dict[str, Any]]:
        """
        Normalize SpyCloud watchlist alert to standard format
        
        Args:
            alert: Raw watchlist alert
            
        Returns:
            Normalized alert or None
        """
        try:
            watchlist_type = alert.get('watchlist_type', 'unknown')
            breach_title = alert.get('breach_title', 'Unknown Breach')
            severity = alert.get('severity', 2)
            
            # Map severity
            severity_map = {
                3: "HIGH",
                2: "MEDIUM", 
                1: "LOW"
            }
            
            normalized = {
                "source": "SpyCloud Watchlist",
                "matched_term": alert.get('watchlist_name', 'Watchlist Alert'),
                "raw_text": alert.get('description', f"New exposure detected in {breach_title}"),
                "title": f"Watchlist Alert: {breach_title}",
                "url": f"spycloud:watchlist:{alert.get('id', 'unknown')}",
                "timestamp": datetime.utcnow().isoformat(),
                "discovered_date": alert.get('discovered_date', ''),
                "severity": severity_map.get(severity, "MEDIUM"),
                "category": "Watchlist Alert",
                "metadata": {
                    "watchlist_type": watchlist_type,
                    "breach_id": alert.get('breach_id'),
                    "record_count": alert.get('record_count', 0)
                }
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize watchlist alert: {e}")
            return None


def check_spycloud_exposures(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    Check SpyCloud for exposures related to all targets
    
    Args:
        targets_file: Path to targets.json file
        
    Returns:
        Combined exposure results
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
    
    client = SpyCloudClient()
    if not client.enabled:
        logger.warning("SpyCloud client not enabled. Skipping credential checks.")
        return []
    
    all_results = []
    
    # Check each domain
    for domain in targets.get('domains', []):
        logger.info(f"Checking SpyCloud for domain: {domain}")
        results = client.check_domain_exposure(domain)
        all_results.extend(results)
    
    # Check watchlist alerts
    logger.info("Checking SpyCloud watchlist alerts")
    watchlist_alerts = client.get_watchlist_alerts()
    all_results.extend(watchlist_alerts)
    
    # Remove duplicates
    seen_ids = set()
    unique_results = []
    for result in all_results:
        result_id = result.get('url', '')
        if result_id not in seen_ids:
            seen_ids.add(result_id)
            unique_results.append(result)
    
    return unique_results


if __name__ == "__main__":
    # Test the client
    client = SpyCloudClient()
    
    if client.enabled:
        # Test domain check
        test_results = client.check_domain_exposure("example.com", days_back=90)
        print(f"Found {len(test_results)} exposures for example.com")
        
        for result in test_results[:3]:
            print(f"- {result['title']}")
            print(f"  Severity: {result['severity']}")
            print(f"  {result['raw_text'][:100]}...")
    else:
        print("SpyCloud client not enabled. Set SPYCLOUD_API_KEY in .env file.")