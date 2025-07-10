import json
import subprocess
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class OnionScanAdapter:
    """
    OnionScan - 無料のオープンソースTorスキャナー
    .onionサイトの詳細情報を取得
    """
    
    def __init__(self):
        self.onionscan_path = self._find_onionscan()
        self.tor_proxy = "127.0.0.1:9050"  # Default Tor SOCKS proxy
        
    def _find_onionscan(self) -> Optional[str]:
        """Find OnionScan binary"""
        # Check common locations
        paths = [
            "/usr/local/bin/onionscan",
            "/usr/bin/onionscan",
            "./onionscan",
            "onionscan"
        ]
        
        for path in paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(["which", "onionscan"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        logger.warning("OnionScan not found. Install from: https://github.com/s-rah/onionscan")
        return None
    
    def scan_onion(self, onion_url: str) -> Optional[Dict[str, Any]]:
        """
        Scan a single .onion site
        
        Args:
            onion_url: The .onion URL to scan
            
        Returns:
            Scan results or None
        """
        if not self.onionscan_path:
            return None
        
        # Clean URL
        if not onion_url.startswith("http"):
            onion_url = f"http://{onion_url}"
        
        try:
            # Run OnionScan
            cmd = [
                self.onionscan_path,
                "--torProxyAddress", self.tor_proxy,
                "--jsonReport",
                onion_url
            ]
            
            logger.info(f"Scanning {onion_url} with OnionScan...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0 and result.stdout:
                # Parse JSON output
                scan_data = json.loads(result.stdout)
                return self._normalize_scan_results(scan_data, onion_url)
            else:
                logger.error(f"OnionScan failed for {onion_url}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.warning(f"OnionScan timeout for {onion_url}")
            return None
        except Exception as e:
            logger.error(f"OnionScan error: {e}")
            return None
    
    def _normalize_scan_results(self, scan_data: Dict, url: str) -> Dict[str, Any]:
        """Normalize OnionScan results to standard format"""
        
        # Extract interesting findings
        interesting_files = scan_data.get("interestingFiles", [])
        open_directories = scan_data.get("openDirectories", [])
        bitcoin_addresses = scan_data.get("bitcoinAddresses", [])
        email_addresses = scan_data.get("emailAddresses", [])
        
        # Build description
        findings = []
        if interesting_files:
            findings.append(f"{len(interesting_files)} interesting files found")
        if open_directories:
            findings.append(f"{len(open_directories)} open directories")
        if bitcoin_addresses:
            findings.append(f"{len(bitcoin_addresses)} Bitcoin addresses")
        if email_addresses:
            findings.append(f"{len(email_addresses)} email addresses")
        
        description = f"OnionScan findings: {', '.join(findings) if findings else 'No special findings'}"
        
        # Determine severity based on findings
        severity = "INFO"
        if interesting_files or open_directories:
            severity = "MEDIUM"
        if any(file.endswith(('.sql', '.db', '.csv')) for file in interesting_files):
            severity = "HIGH"
        
        normalized = {
            "source": "OnionScan",
            "matched_term": url,
            "raw_text": description,
            "title": f"OnionScan: {scan_data.get('hiddenService', url)}",
            "url": url,
            "timestamp": datetime.utcnow().isoformat(),
            "discovered_date": datetime.utcnow().isoformat(),
            "severity": severity,
            "category": "Onion Site Scan",
            "metadata": {
                "online": scan_data.get("online", False),
                "interesting_files": interesting_files,
                "open_directories": open_directories,
                "bitcoin_addresses": bitcoin_addresses,
                "email_addresses": email_addresses,
                "ssh_key": scan_data.get("sshKey", None) is not None,
                "ftp_banner": scan_data.get("ftpBanner", ""),
                "smtp_banner": scan_data.get("smtpBanner", "")
            }
        }
        
        return normalized


class TorCrawlerOSS:
    """
    その他の無料Torクローラー/ツールの統合
    """
    
    def __init__(self):
        self.tools = {
            "ahmia": True,  # Already implemented
            "torch": self._check_torch_available(),
            "notevil": self._check_notevil_available()
        }
    
    def _check_torch_available(self) -> bool:
        """Check if TORCH search is accessible"""
        # TORCH is often down, so check availability
        return False  # Placeholder
    
    def _check_notevil_available(self) -> bool:
        """Check if NotEvil search is accessible"""
        return False  # Placeholder
    
    def search_all_engines(self, query: str) -> List[Dict[str, Any]]:
        """Search across all available Tor search engines"""
        results = []
        
        # Already have Ahmia implemented
        # Would add other engines here as they become available
        
        return results


def scan_discovered_onions(onion_urls: List[str]) -> List[Dict[str, Any]]:
    """
    Scan discovered onion sites with OnionScan
    
    Args:
        onion_urls: List of .onion URLs to scan
        
    Returns:
        Scan results
    """
    scanner = OnionScanAdapter()
    results = []
    
    for url in onion_urls[:10]:  # Limit to prevent long runs
        result = scanner.scan_onion(url)
        if result:
            results.append(result)
    
    return results


if __name__ == "__main__":
    # Test OnionScan
    scanner = OnionScanAdapter()
    
    if scanner.onionscan_path:
        # Test with a known onion site
        test_url = "http://thehiddenwiki.onion"
        result = scanner.scan_onion(test_url)
        
        if result:
            print(f"Scan successful: {result['title']}")
            print(f"Severity: {result['severity']}")
            print(f"Findings: {result['raw_text']}")
    else:
        print("OnionScan not installed. Please install it first.")