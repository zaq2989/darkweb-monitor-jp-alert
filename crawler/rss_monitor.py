"""
RSSフィード監視モジュール
セキュリティ関連のRSSフィードから日本企業の言及を検出
"""
import feedparser
import json
import logging
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class RSSMonitor:
    """
    セキュリティ関連RSSフィードの監視
    """
    
    def __init__(self):
        # セキュリティ関連のRSSフィード
        self.feeds = [
            {
                "name": "BleepingComputer",
                "url": "https://www.bleepingcomputer.com/feed/",
                "category": "security_news"
            },
            {
                "name": "The Hacker News",
                "url": "https://feeds.feedburner.com/TheHackersNews",
                "category": "security_news"
            },
            {
                "name": "Krebs on Security",
                "url": "https://krebsonsecurity.com/feed/",
                "category": "security_blog"
            },
            {
                "name": "DataBreaches.net",
                "url": "https://www.databreaches.net/feed/",
                "category": "breach_news"
            },
            {
                "name": "Have I Been Pwned Latest Breaches",
                "url": "https://feeds.feedburner.com/HaveIBeenPwnedLatestBreaches",
                "category": "breach_alerts"
            },
            {
                "name": "Reddit - NetSec",
                "url": "https://www.reddit.com/r/netsec/.rss",
                "category": "community"
            },
            {
                "name": "Reddit - Onions",
                "url": "https://www.reddit.com/r/onions/.rss", 
                "category": "darkweb"
            },
            {
                "name": "Threatpost",
                "url": "https://threatpost.com/feed/",
                "category": "security_news"
            }
        ]
        
        # キャッシュファイル
        self.cache_file = "rss_cache.json"
        self.seen_entries = self._load_cache()
    
    def _load_cache(self) -> set:
        """Load previously seen RSS entries"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                return set(data.get('seen_ids', []))
        except:
            return set()
    
    def _save_cache(self):
        """Save seen RSS entries"""
        try:
            data = {
                'seen_ids': list(self.seen_entries),
                'last_updated': datetime.utcnow().isoformat()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save RSS cache: {e}")
    
    def check_feeds(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Check all RSS feeds for keyword mentions
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of matching entries
        """
        all_results = []
        
        for feed_info in self.feeds:
            try:
                logger.info(f"Checking RSS feed: {feed_info['name']}")
                
                # Parse feed
                feed = feedparser.parse(feed_info['url'])
                
                if feed.bozo:
                    logger.warning(f"Failed to parse feed {feed_info['name']}: {feed.bozo_exception}")
                    continue
                
                # Check entries
                for entry in feed.entries[:50]:  # Limit to recent 50 entries
                    # Skip if already seen
                    entry_id = entry.get('id', entry.get('link', ''))
                    if entry_id in self.seen_entries:
                        continue
                    
                    # Get entry content
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    content = entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
                    full_text = f"{title} {summary} {content}".lower()
                    
                    # Check for keywords
                    matched_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in full_text:
                            matched_keywords.append(keyword)
                    
                    if matched_keywords:
                        # Check publish date (only recent entries)
                        published = entry.get('published_parsed')
                        if published:
                            pub_date = datetime.fromtimestamp(time.mktime(published))
                            if pub_date < datetime.utcnow() - timedelta(days=30):
                                continue  # Skip old entries
                        
                        # Create result
                        result = self._create_result(entry, feed_info, matched_keywords)
                        all_results.append(result)
                        
                        # Mark as seen
                        self.seen_entries.add(entry_id)
                
                # Rate limit
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error checking feed {feed_info['name']}: {e}")
        
        # Save cache
        self._save_cache()
        
        return all_results
    
    def _create_result(self, entry: Dict, feed_info: Dict, matched_keywords: List[str]) -> Dict[str, Any]:
        """Create normalized result from RSS entry"""
        
        # Determine severity based on content
        severity = "INFO"
        content_lower = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
        
        if any(word in content_lower for word in ['breach', 'leak', 'hack', 'dump', 'credential', 'password']):
            severity = "HIGH"
        elif any(word in content_lower for word in ['vulnerability', 'exploit', 'security', 'attack']):
            severity = "MEDIUM"
        elif feed_info['category'] == 'darkweb':
            severity = "MEDIUM"
        
        # Get publish date
        published = entry.get('published_parsed')
        if published:
            pub_date = datetime.fromtimestamp(time.mktime(published)).isoformat()
        else:
            pub_date = datetime.utcnow().isoformat()
        
        return {
            "source": f"RSS-{feed_info['name']}",
            "matched_term": ", ".join(matched_keywords),
            "raw_text": entry.get('summary', '')[:1000],  # Limit length
            "title": entry.get('title', 'No title'),
            "url": entry.get('link', ''),
            "timestamp": datetime.utcnow().isoformat(),
            "discovered_date": pub_date,
            "severity": severity,
            "category": feed_info['category'],
            "metadata": {
                "feed_name": feed_info['name'],
                "author": entry.get('author', 'Unknown'),
                "tags": [tag['term'] for tag in entry.get('tags', [])]
            }
        }


class LocalFileMonitor:
    """
    ローカルファイル監視
    指定ディレクトリ内のファイルから企業情報を検出
    """
    
    def __init__(self, watch_dirs: List[str] = None):
        if watch_dirs is None:
            watch_dirs = ["./watch_files"]
        
        self.watch_dirs = watch_dirs
        self.processed_files = self._load_processed_files()
    
    def _load_processed_files(self) -> set:
        """Load list of processed files"""
        try:
            with open('processed_files.json', 'r') as f:
                data = json.load(f)
                return set(data.get('files', []))
        except:
            return set()
    
    def _save_processed_files(self):
        """Save processed files list"""
        try:
            data = {
                'files': list(self.processed_files),
                'last_updated': datetime.utcnow().isoformat()
            }
            with open('processed_files.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processed files: {e}")
    
    def scan_files(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Scan local files for keywords
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            List of findings
        """
        import os
        results = []
        
        for watch_dir in self.watch_dirs:
            if not os.path.exists(watch_dir):
                logger.warning(f"Watch directory does not exist: {watch_dir}")
                continue
            
            # Scan all text files
            for root, dirs, files in os.walk(watch_dir):
                for filename in files:
                    if not filename.endswith(('.txt', '.log', '.json', '.csv')):
                        continue
                    
                    filepath = os.path.join(root, filename)
                    
                    # Skip if already processed
                    if filepath in self.processed_files:
                        continue
                    
                    try:
                        # Read file
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Check for keywords
                        matched_keywords = []
                        for keyword in keywords:
                            if keyword.lower() in content.lower():
                                matched_keywords.append(keyword)
                        
                        if matched_keywords:
                            # Create result
                            result = {
                                "source": "LocalFile",
                                "matched_term": ", ".join(matched_keywords),
                                "raw_text": self._extract_context(content, matched_keywords[0]),
                                "title": f"Local file: {filename}",
                                "url": f"file://{os.path.abspath(filepath)}",
                                "timestamp": datetime.utcnow().isoformat(),
                                "discovered_date": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                                "severity": "MEDIUM",
                                "category": "local_file",
                                "metadata": {
                                    "file_path": filepath,
                                    "file_size": os.path.getsize(filepath),
                                    "file_type": os.path.splitext(filename)[1]
                                }
                            }
                            results.append(result)
                        
                        # Mark as processed
                        self.processed_files.add(filepath)
                        
                    except Exception as e:
                        logger.error(f"Error reading file {filepath}: {e}")
        
        # Save processed files
        self._save_processed_files()
        
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


def monitor_local_sources(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    Monitor all local sources (RSS feeds, local files)
    
    Args:
        targets_file: Path to targets.json
        
    Returns:
        Combined results from all local sources
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
    
    # Get all keywords
    all_keywords = (
        targets.get('keywords', []) +
        targets.get('domains', []) +
        targets.get('company_names', [])
    )
    
    all_results = []
    
    # Monitor RSS feeds
    rss_monitor = RSSMonitor()
    logger.info("Checking RSS feeds...")
    rss_results = rss_monitor.check_feeds(all_keywords[:20])  # Limit keywords
    all_results.extend(rss_results)
    
    # Monitor local files
    file_monitor = LocalFileMonitor()
    logger.info("Scanning local files...")
    file_results = file_monitor.scan_files(all_keywords)
    all_results.extend(file_results)
    
    return all_results


if __name__ == "__main__":
    # Test RSS monitoring
    logging.basicConfig(level=logging.INFO)
    
    # Test with a few keywords
    test_keywords = ["sony", "toyota", "nintendo", "breach", "leak"]
    
    rss_monitor = RSSMonitor()
    results = rss_monitor.check_feeds(test_keywords)
    
    print(f"Found {len(results)} results from RSS feeds")
    for result in results[:5]:
        print(f"- [{result['source']}] {result['title'][:60]}...")
        print(f"  Matched: {result['matched_term']}")