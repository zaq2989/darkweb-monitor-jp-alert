#!/usr/bin/env python3
"""
無料API版モニタリングスクリプト
有料APIを使わず、無料のリソースのみでダークウェブ監視を実行
"""
import os
import sys
import time
import schedule
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from external_api.truly_free_apis import search_truly_free_sources
from external_api.web_scraper import scrape_web_sources
from external_api.twitter_monitor import monitor_twitter
from external_api.simulated_sources import get_external_results
from crawler.ahmia_adapter import search_ahmia
from crawler.tor_discovery import discover_tor_sites
from crawler.onionscan_adapter import scan_discovered_onions
from crawler.rss_monitor import monitor_local_sources
from crawler.alternative_sources import monitor_alternative_sources
from core.analyzer import DarkwebAnalyzer
from core.alert_engine import AlertEngine
# Optional: Elasticsearch support
try:
    from storage.elasticsearch_loader import ElasticsearchLoader
except ImportError:
    ElasticsearchLoader = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('darkweb_monitor_free.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FreeAPIMonitor:
    """無料APIのみを使用するモニター"""
    
    def __init__(self):
        self.analyzer = DarkwebAnalyzer(
            os.path.join(os.path.dirname(__file__), '..', 'config', 'targets.json')
        )
        self.alert_engine = AlertEngine()
        
        # Initialize Elasticsearch if configured
        self.use_elasticsearch = False
        if ElasticsearchLoader:
            try:
                self.es_loader = ElasticsearchLoader()
                self.use_elasticsearch = True
            except Exception as e:
                logger.warning(f"Elasticsearch not available: {e}")
                self.use_elasticsearch = False
        else:
            logger.info("Elasticsearch support not installed (optional)")
        
        # Track processed items
        self.processed_urls = set()
        self.processed_hashes = set()  # For deduplication
        self._load_processed_data()
        
        # Counters for rate limiting
        self.api_counters = {
            'github': 0,
            'hibp': 0,
            'ahmia': 0,
            'discovery_cycle': 0
        }
    
    def _load_processed_data(self):
        """Load previously processed URLs and hashes"""
        urls_file = 'processed_urls_free.txt'
        if os.path.exists(urls_file):
            with open(urls_file, 'r') as f:
                self.processed_urls = set(line.strip() for line in f)
            logger.info(f"Loaded {len(self.processed_urls)} processed URLs")
    
    def _save_processed_data(self):
        """Save processed URLs"""
        with open('processed_urls_free.txt', 'w') as f:
            for url in self.processed_urls:
                f.write(f"{url}\n")
    
    def _create_content_hash(self, content: str) -> str:
        """Create hash of content for deduplication"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    def monitor_cycle(self):
        """Execute one monitoring cycle with free APIs only"""
        logger.info("Starting free API monitoring cycle")
        
        try:
            all_results = []
            
            # 1. Web scraping sources (Google, Security sites)
            logger.info("Scraping web sources...")
            try:
                web_results = scrape_web_sources()
                logger.info(f"Retrieved {len(web_results)} results from web scraping")
                all_results.extend(web_results)
            except Exception as e:
                logger.error(f"Web scraping failed: {e}")
            
            # 2. Twitter monitoring
            logger.info("Monitoring Twitter...")
            try:
                twitter_results = monitor_twitter()
                logger.info(f"Retrieved {len(twitter_results)} results from Twitter")
                all_results.extend(twitter_results)
            except Exception as e:
                logger.error(f"Twitter monitoring failed: {e}")
            
            # 3. Original free sources (as backup)
            logger.info("Searching other free sources...")
            try:
                free_results = search_truly_free_sources()
                logger.info(f"Retrieved {len(free_results)} results from free sources")
                all_results.extend(free_results)
            except Exception as e:
                logger.error(f"Free sources failed: {e}")
            
            # 4. Monitor local sources (RSS feeds, local files)
            logger.info("Monitoring local sources (RSS, files)...")
            local_results = monitor_local_sources()
            logger.info(f"Retrieved {len(local_results)} results from local sources")
            all_results.extend(local_results)
            
            # 3. Monitor alternative sources (Telegram, Reddit, etc.)
            logger.info("Monitoring alternative sources (Telegram, Reddit)...")
            alt_results = monitor_alternative_sources()
            logger.info(f"Retrieved {len(alt_results)} results from alternative sources")
            all_results.extend(alt_results)
            
            # 4. Search Ahmia (free Tor search)
            logger.info("Searching Ahmia for Tor sites...")
            ahmia_results = search_ahmia()
            logger.info(f"Retrieved {len(ahmia_results)} results from Ahmia")
            all_results.extend(ahmia_results)
            
            # 5. Tor discovery (every 10 cycles to avoid overload)
            self.api_counters['discovery_cycle'] += 1
            if self.api_counters['discovery_cycle'] % 10 == 0:
                logger.info("Running Tor discovery...")
                discoveries = discover_tor_sites()
                logger.info(f"Discovered {len(discoveries)} new Tor sites")
                
                # Optional: Scan some discovered onions with OnionScan
                if discoveries:
                    onion_urls = [d['url'] for d in discoveries[:5]]  # Limit to 5
                    scan_results = scan_discovered_onions(onion_urls)
                    all_results.extend(scan_results)
            
            # 6. Fallback to simulated sources if needed
            if len(all_results) == 0:
                logger.warning("No results from external sources, using simulated fallback...")
                simulated_results = get_external_results()
                logger.info(f"Generated {len(simulated_results)} simulated results")
                all_results.extend(simulated_results)
            
            # Filter and deduplicate results
            new_results = []
            for result in all_results:
                # Check URL
                url = result.get('url', '')
                if url and url in self.processed_urls:
                    continue
                
                # Check content hash for deduplication
                content_hash = self._create_content_hash(
                    f"{result.get('source', '')}{result.get('raw_text', '')}"
                )
                if content_hash in self.processed_hashes:
                    continue
                
                new_results.append(result)
                if url:
                    self.processed_urls.add(url)
                self.processed_hashes.add(content_hash)
            
            logger.info(f"Found {len(new_results)} new unique results to analyze")
            
            # Analyze results
            alerts = self.analyzer.batch_analyze(new_results)
            logger.info(f"Generated {len(alerts)} alerts")
            
            # Process alerts
            for alert in alerts:
                self._process_alert(alert)
            
            # Save processed data
            self._save_processed_data()
            
            # Log API usage
            logger.info(
                f"Monitoring cycle completed. "
                f"Processed {len(new_results)} new items, "
                f"generated {len(alerts)} alerts"
            )
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
    
    def _process_alert(self, alert: Dict[str, Any]):
        """Process a single alert"""
        try:
            # Log alert
            logger.warning(
                f"ALERT: {alert['severity']} - {alert['matched_term']} "
                f"(confidence: {alert['confidence_score']}%) - {alert['source']}"
            )
            
            # Add source info for free version
            alert['raw_text'] = f"[FREE API - {alert['source']}] " + alert.get('raw_text', '')
            
            # Send notification
            success = self.alert_engine.send_alert(alert)
            if success:
                logger.info(f"Alert sent successfully for {alert['matched_term']}")
            else:
                logger.error(f"Failed to send alert for {alert['matched_term']}")
            
            # Store in Elasticsearch if available
            if self.use_elasticsearch:
                try:
                    self.es_loader.store_alert(alert)
                    logger.info(f"Alert stored in Elasticsearch")
                except Exception as e:
                    logger.error(f"Failed to store alert in Elasticsearch: {e}")
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}", exc_info=True)
    
    def start(self, interval_minutes: int = 10):
        """
        Start the monitoring scheduler
        Note: Longer interval for free APIs to respect rate limits
        """
        logger.info(f"Starting free API darkweb monitor with {interval_minutes} minute interval")
        
        # Run immediately on start
        self.monitor_cycle()
        
        # Schedule periodic runs
        schedule.every(interval_minutes).minutes.do(self.monitor_cycle)
        
        logger.info("Free API Monitor started. Press Ctrl+C to stop.")
        logger.info("Using only free resources: Ahmia, HIBP, GitHub, OnionScan")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
        except Exception as e:
            logger.error(f"Monitor stopped due to error: {e}", exc_info=True)


def main():
    """Main entry point for free API monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Free API Darkweb Monitor for Japanese Companies'
    )
    parser.add_argument(
        '--interval', 
        type=int, 
        default=10, 
        help='Monitoring interval in minutes (default: 10, recommended for free APIs)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit'
    )
    
    args = parser.parse_args()
    
    # No API keys required for free version!
    logger.info("Starting FREE API version - No paid API keys required")
    logger.info("Available sources: Ahmia, GitHub, HIBP, OnionScan")
    
    # Initialize and start monitor
    monitor = FreeAPIMonitor()
    
    if args.once:
        # Run once and exit
        monitor.monitor_cycle()
    else:
        # Start continuous monitoring
        monitor.start(interval_minutes=args.interval)


if __name__ == "__main__":
    main()