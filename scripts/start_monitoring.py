#!/usr/bin/env python3
import os
import sys
import time
import schedule
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from external_api.darkowl_client import query_darkowl
from external_api.spycloud_client import check_spycloud_exposures
from crawler.ahmia_adapter import search_ahmia
from crawler.tor_discovery import discover_tor_sites
from core.analyzer import DarkwebAnalyzer
from core.alert_engine import AlertEngine
from storage.elasticsearch_loader import ElasticsearchLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('darkweb_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DarkwebMonitor:
    def __init__(self):
        self.analyzer = DarkwebAnalyzer(
            os.path.join(os.path.dirname(__file__), '..', 'config', 'targets.json')
        )
        self.alert_engine = AlertEngine()
        
        # Initialize Elasticsearch if configured
        try:
            self.es_loader = ElasticsearchLoader()
            self.use_elasticsearch = True
        except Exception as e:
            logger.warning(f"Elasticsearch not available: {e}")
            self.use_elasticsearch = False
        
        # Track processed URLs to avoid duplicate alerts
        self.processed_urls = set()
        self._load_processed_urls()
    
    def _load_processed_urls(self):
        """Load previously processed URLs from file"""
        urls_file = 'processed_urls.txt'
        if os.path.exists(urls_file):
            with open(urls_file, 'r') as f:
                self.processed_urls = set(line.strip() for line in f)
            logger.info(f"Loaded {len(self.processed_urls)} processed URLs")
    
    def _save_processed_urls(self):
        """Save processed URLs to file"""
        with open('processed_urls.txt', 'w') as f:
            for url in self.processed_urls:
                f.write(f"{url}\n")
    
    def monitor_cycle(self):
        """Execute one monitoring cycle"""
        logger.info("Starting monitoring cycle")
        
        try:
            # Collect results from all sources
            all_results = []
            
            # Query DarkOwl API
            logger.info("Querying DarkOwl API...")
            darkowl_results = query_darkowl()
            logger.info(f"Retrieved {len(darkowl_results)} results from DarkOwl")
            all_results.extend(darkowl_results)
            
            # Query Ahmia (Tor search)
            logger.info("Querying Ahmia for Tor sites...")
            ahmia_results = search_ahmia()
            logger.info(f"Retrieved {len(ahmia_results)} results from Ahmia")
            all_results.extend(ahmia_results)
            
            # Check SpyCloud for credential exposures
            logger.info("Checking SpyCloud for credential exposures...")
            spycloud_results = check_spycloud_exposures()
            logger.info(f"Retrieved {len(spycloud_results)} results from SpyCloud")
            all_results.extend(spycloud_results)
            
            # Discover new Tor sites (run less frequently)
            if hasattr(self, '_discovery_counter'):
                self._discovery_counter += 1
            else:
                self._discovery_counter = 0
            
            if self._discovery_counter % 10 == 0:  # Every 10 cycles
                logger.info("Running Tor discovery...")
                tor_discoveries = discover_tor_sites()
                logger.info(f"Discovered {len(tor_discoveries)} new Tor sites")
            
            results = all_results
            
            # Filter out already processed URLs
            new_results = [
                r for r in results 
                if r.get('url') and r['url'] not in self.processed_urls
            ]
            logger.info(f"Found {len(new_results)} new results to analyze")
            
            # Analyze results
            alerts = self.analyzer.batch_analyze(new_results)
            logger.info(f"Generated {len(alerts)} alerts")
            
            # Process alerts
            for alert in alerts:
                self._process_alert(alert)
            
            # Mark URLs as processed
            for result in new_results:
                if result.get('url'):
                    self.processed_urls.add(result['url'])
            
            # Save processed URLs
            self._save_processed_urls()
            
            logger.info(f"Monitoring cycle completed. Processed {len(new_results)} new items, generated {len(alerts)} alerts")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
    
    def _process_alert(self, alert: Dict[str, Any]):
        """Process a single alert"""
        try:
            # Log alert
            logger.warning(
                f"ALERT: {alert['severity']} - {alert['matched_term']} "
                f"(confidence: {alert['confidence_score']}%) - {alert['url']}"
            )
            
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
    
    def start(self, interval_minutes: int = 3):
        """Start the monitoring scheduler"""
        logger.info(f"Starting darkweb monitor with {interval_minutes} minute interval")
        
        # Run immediately on start
        self.monitor_cycle()
        
        # Schedule periodic runs
        schedule.every(interval_minutes).minutes.do(self.monitor_cycle)
        
        logger.info("Monitor started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
        except Exception as e:
            logger.error(f"Monitor stopped due to error: {e}", exc_info=True)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Darkweb Monitor for Japanese Companies')
    parser.add_argument(
        '--interval', 
        type=int, 
        default=3, 
        help='Monitoring interval in minutes (default: 3)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit'
    )
    
    args = parser.parse_args()
    
    # Check for required environment variables
    required_vars = ['DARKOWL_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please copy .env.example to .env and fill in the required values")
        sys.exit(1)
    
    # Initialize and start monitor
    monitor = DarkwebMonitor()
    
    if args.once:
        # Run once and exit
        monitor.monitor_cycle()
    else:
        # Start continuous monitoring
        monitor.start(interval_minutes=args.interval)


if __name__ == "__main__":
    main()