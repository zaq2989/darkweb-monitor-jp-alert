import json
import logging
import random
import time
from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timedelta
import requests
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class TorDiscoveryModule:
    """
    Automated Tor hidden service discovery module
    Discovers new .onion sites through various methods:
    1. Following links from known onion sites
    2. Checking common onion directories
    3. Monitoring paste sites for new onion URLs
    4. Using public onion link aggregators
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Known onion directories and link lists
        self.seed_directories = [
            "https://ahmia.fi/onions/",
            "https://thehiddenwiki.org",
            "https://tor.link"
        ]
        
        # Paste sites that might contain onion links
        self.paste_sites = [
            "https://pastebin.com/raw/",
            "https://gist.githubusercontent.com/"
        ]
        
        # Regex pattern for onion URLs
        self.onion_pattern = r'[a-z2-7]{16,56}\.onion'
        
        # Cache discovered onions
        self.discovered_onions = self._load_discovered_cache()
        self.new_discoveries = set()
        
        # Rate limiting
        self.min_delay = 2
        self.max_delay = 5
    
    def _load_discovered_cache(self) -> Set[str]:
        """Load previously discovered onion addresses"""
        cache_file = 'discovered_onions.json'
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return set(data.get('onions', []))
        except:
            return set()
    
    def _save_discovered_cache(self):
        """Save discovered onion addresses to cache"""
        cache_file = 'discovered_onions.json'
        try:
            all_onions = self.discovered_onions.union(self.new_discoveries)
            data = {
                'onions': list(all_onions),
                'last_updated': datetime.utcnow().isoformat()
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save discovery cache: {e}")
    
    def discover_from_directories(self) -> List[str]:
        """Discover onion URLs from known directories"""
        discovered = []
        
        for directory in self.seed_directories:
            try:
                logger.info(f"Checking directory: {directory}")
                response = self.session.get(directory, timeout=30)
                
                if response.status_code == 200:
                    # Extract onion URLs from content
                    import re
                    onions = re.findall(self.onion_pattern, response.text)
                    
                    for onion in onions:
                        full_url = f"http://{onion}"
                        if full_url not in self.discovered_onions:
                            discovered.append(full_url)
                            self.new_discoveries.add(full_url)
                
                # Rate limiting
                time.sleep(random.uniform(self.min_delay, self.max_delay))
                
            except Exception as e:
                logger.debug(f"Failed to check directory {directory}: {e}")
        
        return discovered
    
    def discover_from_paste_sites(self, search_terms: List[str]) -> List[str]:
        """Search paste sites for onion URLs related to search terms"""
        discovered = []
        
        # This is a simplified implementation
        # In production, you'd use paste site APIs
        for term in search_terms[:3]:  # Limit searches
            try:
                # Search for pastes containing the term + "onion"
                search_url = f"https://www.google.com/search?q=site:pastebin.com+{term}+onion"
                
                # Note: This is just a placeholder
                # Real implementation would use paste site APIs
                logger.info(f"Would search paste sites for: {term}")
                
            except Exception as e:
                logger.debug(f"Paste site search failed: {e}")
        
        return discovered
    
    def discover_from_onion_crawl(self, seed_onions: List[str], max_depth: int = 2) -> List[str]:
        """
        Crawl known onion sites to discover new ones
        Note: This requires Tor proxy to actually access .onion sites
        """
        discovered = []
        
        # This is a placeholder implementation
        # Real implementation would require Tor SOCKS proxy
        logger.info(f"Would crawl {len(seed_onions)} seed onions")
        
        # Simulate discovery
        for seed in seed_onions[:5]:  # Limit crawl
            # In reality, this would fetch the onion page through Tor
            # and extract links to other onion sites
            pass
        
        return discovered
    
    def check_onion_availability(self, onion_url: str) -> Dict[str, Any]:
        """
        Check if an onion site is available
        Note: Requires Tor proxy for actual checking
        """
        result = {
            'url': onion_url,
            'available': False,
            'title': None,
            'last_checked': datetime.utcnow().isoformat(),
            'error': None
        }
        
        # Placeholder - real implementation needs Tor
        # Would check through Tor SOCKS proxy
        logger.debug(f"Would check availability of: {onion_url}")
        
        return result
    
    def discover_related_to_targets(self, targets: List[str]) -> List[Dict[str, Any]]:
        """
        Discover onion sites potentially related to target terms
        
        Args:
            targets: List of target keywords/domains
            
        Returns:
            List of discovered onion sites with metadata
        """
        all_discoveries = []
        
        # 1. Check directories
        directory_finds = self.discover_from_directories()
        for url in directory_finds:
            all_discoveries.append({
                'url': url,
                'discovery_method': 'directory',
                'discovered_date': datetime.utcnow().isoformat(),
                'related_terms': []
            })
        
        # 2. Search paste sites
        paste_finds = self.discover_from_paste_sites(targets)
        for url in paste_finds:
            all_discoveries.append({
                'url': url,
                'discovery_method': 'paste_site',
                'discovered_date': datetime.utcnow().isoformat(),
                'related_terms': targets
            })
        
        # 3. Save discoveries
        self._save_discovered_cache()
        
        logger.info(f"Discovered {len(all_discoveries)} new onion sites")
        return all_discoveries
    
    def generate_discovery_report(self) -> Dict[str, Any]:
        """Generate a report of discovery activities"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_known_onions': len(self.discovered_onions),
            'new_discoveries': len(self.new_discoveries),
            'discovery_methods': {
                'directories': len([d for d in self.seed_directories]),
                'paste_sites': len(self.paste_sites)
            },
            'cache_size': len(self.discovered_onions.union(self.new_discoveries))
        }


class TorMonitor:
    """
    Monitor specific Tor hidden services for changes
    """
    
    def __init__(self, onion_urls: List[str]):
        self.monitored_sites = onion_urls
        self.site_hashes = {}  # Store content hashes for change detection
        
    def check_for_changes(self) -> List[Dict[str, Any]]:
        """
        Check monitored sites for content changes
        Note: Requires Tor proxy for actual monitoring
        """
        changes = []
        
        for site in self.monitored_sites:
            # Placeholder - would actually fetch through Tor
            logger.debug(f"Would check for changes at: {site}")
            
            # Simulate change detection
            change_info = {
                'url': site,
                'changed': False,
                'last_checked': datetime.utcnow().isoformat(),
                'change_type': None
            }
            changes.append(change_info)
        
        return changes


def discover_tor_sites(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    Main function to discover Tor sites related to targets
    
    Args:
        targets_file: Path to targets.json
        
    Returns:
        List of discovered sites
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
    
    # Initialize discovery module
    discovery = TorDiscoveryModule()
    
    # Combine all target terms
    all_terms = (
        targets.get('keywords', []) +
        targets.get('domains', []) +
        targets.get('company_names', [])
    )
    
    # Discover related sites
    discoveries = discovery.discover_related_to_targets(all_terms[:10])  # Limit terms
    
    # Generate report
    report = discovery.generate_discovery_report()
    logger.info(f"Discovery report: {json.dumps(report, indent=2)}")
    
    return discoveries


if __name__ == "__main__":
    # Test discovery
    discovery = TorDiscoveryModule()
    
    # Test directory discovery
    found = discovery.discover_from_directories()
    print(f"Found {len(found)} onion sites from directories")
    
    # Generate report
    report = discovery.generate_discovery_report()
    print(f"Discovery report: {json.dumps(report, indent=2)}")