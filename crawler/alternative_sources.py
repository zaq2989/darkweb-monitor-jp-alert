"""
代替データソースモニタリング
Telegram、Discord、Reddit等の公開チャンネル/サーバーを監視
"""
import requests
import json
import logging
import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import quote

logger = logging.getLogger(__name__)

class TelegramPublicMonitor:
    """
    Telegram公開チャンネル監視
    t.meリンクやTelegram Web検索を使用
    """
    
    def __init__(self):
        self.base_url = "https://t.me/s/"  # Public channel viewer
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Known security/darkweb related Telegram channels
        self.channels = [
            "darkwebinformer",
            "cybersecintel", 
            "datasecuritynews",
            "breachalerts",
            "darknetmarkets"
        ]
        
        self.processed_messages = set()
    
    def search_public_channels(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Search public Telegram channels for keywords
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            List of findings
        """
        results = []
        
        for channel in self.channels:
            try:
                logger.info(f"Checking Telegram channel: {channel}")
                
                # Get channel page
                url = f"{self.base_url}{channel}"
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to access channel {channel}: {response.status_code}")
                    continue
                
                # Parse messages (simple HTML parsing)
                messages = self._parse_telegram_messages(response.text, channel)
                
                # Check for keywords
                for msg in messages:
                    matched_keywords = []
                    msg_text_lower = msg['text'].lower()
                    
                    for keyword in keywords:
                        if keyword.lower() in msg_text_lower:
                            matched_keywords.append(keyword)
                    
                    if matched_keywords and msg['id'] not in self.processed_messages:
                        result = {
                            "source": f"Telegram-{channel}",
                            "matched_term": ", ".join(matched_keywords),
                            "raw_text": msg['text'][:1000],
                            "title": f"Telegram: {channel} - {msg['date']}",
                            "url": f"https://t.me/{channel}/{msg['id']}",
                            "timestamp": datetime.utcnow().isoformat(),
                            "discovered_date": msg['date'],
                            "severity": self._determine_severity(msg['text']),
                            "category": "telegram_channel",
                            "metadata": {
                                "channel": channel,
                                "message_id": msg['id'],
                                "has_media": msg.get('has_media', False)
                            }
                        }
                        results.append(result)
                        self.processed_messages.add(msg['id'])
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error checking Telegram channel {channel}: {e}")
        
        return results
    
    def _parse_telegram_messages(self, html: str, channel: str) -> List[Dict]:
        """Parse messages from Telegram HTML"""
        messages = []
        
        # Simple regex parsing for message blocks
        message_pattern = r'<div class="tgme_widget_message[^"]*"[^>]*data-post="([^"]+)"[^>]*>(.*?)</div>\s*</div>'
        matches = re.findall(message_pattern, html, re.DOTALL)
        
        for post_id, content in matches[:20]:  # Limit to recent 20
            try:
                # Extract text
                text_match = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
                if text_match:
                    text = re.sub(r'<[^>]+>', '', text_match.group(1)).strip()
                    
                    # Extract date
                    date_match = re.search(r'<time[^>]*datetime="([^"]+)"', content)
                    date = date_match.group(1) if date_match else datetime.utcnow().isoformat()
                    
                    messages.append({
                        'id': post_id.split('/')[-1],
                        'text': text,
                        'date': date,
                        'has_media': '<video' in content or '<img' in content
                    })
            except:
                continue
        
        return messages
    
    def _determine_severity(self, text: str) -> str:
        """Determine severity based on content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['breach', 'leak', 'dump', 'hack', 'password', 'credential']):
            return "HIGH"
        elif any(word in text_lower for word in ['vulnerability', 'exploit', 'darkweb', 'market']):
            return "MEDIUM"
        else:
            return "LOW"


class RedditMonitor:
    """
    Reddit公開サブレディット監視
    Reddit JSON APIを使用（認証不要）
    """
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'DarkwebMonitor-JP/1.0 (Security Research)'
        }
        
        # Security and darkweb related subreddits
        self.subreddits = [
            "netsec",
            "onions", 
            "deepweb",
            "darknet",
            "cybersecurity",
            "hacking",
            "AskNetsec"
        ]
        
        self.processed_posts = set()
    
    def search_subreddits(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Search Reddit for keywords
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            List of findings
        """
        results = []
        
        for subreddit in self.subreddits:
            try:
                logger.info(f"Checking Reddit r/{subreddit}")
                
                # Get recent posts
                url = f"{self.base_url}/r/{subreddit}/new.json?limit=50"
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to access r/{subreddit}: {response.status_code}")
                    continue
                
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                # Check posts
                for post in posts:
                    post_data = post.get('data', {})
                    post_id = post_data.get('id')
                    
                    if post_id in self.processed_posts:
                        continue
                    
                    # Check title and selftext
                    title = post_data.get('title', '')
                    selftext = post_data.get('selftext', '')
                    full_text = f"{title} {selftext}".lower()
                    
                    matched_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in full_text:
                            matched_keywords.append(keyword)
                    
                    if matched_keywords:
                        # Check age (skip if older than 7 days)
                        created = post_data.get('created_utc', 0)
                        if created < (time.time() - 7 * 24 * 3600):
                            continue
                        
                        result = {
                            "source": f"Reddit-r/{subreddit}",
                            "matched_term": ", ".join(matched_keywords),
                            "raw_text": f"{title}\n\n{selftext[:800]}",
                            "title": f"Reddit: {title[:100]}",
                            "url": f"https://reddit.com{post_data.get('permalink', '')}",
                            "timestamp": datetime.utcnow().isoformat(),
                            "discovered_date": datetime.fromtimestamp(created).isoformat(),
                            "severity": self._determine_severity(full_text),
                            "category": "reddit_post",
                            "metadata": {
                                "subreddit": subreddit,
                                "author": post_data.get('author', 'unknown'),
                                "score": post_data.get('score', 0),
                                "num_comments": post_data.get('num_comments', 0),
                                "is_self": post_data.get('is_self', True)
                            }
                        }
                        results.append(result)
                        self.processed_posts.add(post_id)
                
                # Rate limiting (Reddit allows 60 requests per minute)
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error checking Reddit r/{subreddit}: {e}")
        
        return results
    
    def _determine_severity(self, text: str) -> str:
        """Determine severity based on content"""
        if any(word in text for word in ['breach', 'leak', 'dump', 'compromised', 'hacked']):
            return "HIGH"
        elif any(word in text for word in ['vulnerability', 'exploit', 'security', 'darkweb']):
            return "MEDIUM"
        else:
            return "LOW"


class DiscordWebhookMonitor:
    """
    Discord Webhook監視
    公開Webhookやボットメッセージを監視
    """
    
    def __init__(self):
        # Note: This would require webhook URLs or bot tokens
        # For demo purposes, we'll create a placeholder
        self.webhooks = []
        logger.info("Discord monitoring requires webhook URLs")
    
    def check_webhooks(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Check Discord webhooks
        Note: This is a placeholder implementation
        """
        return []


class MatrixPublicRoomMonitor:
    """
    Matrix (Element) 公開ルーム監視
    matrix.orgの公開ルームを監視
    """
    
    def __init__(self):
        self.homeserver = "https://matrix.org"
        self.public_rooms_endpoint = "/_matrix/client/r0/publicRooms"
        
    def search_public_rooms(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Search Matrix public rooms
        Note: Simplified implementation
        """
        results = []
        
        try:
            # Get public rooms list
            response = requests.get(
                f"{self.homeserver}{self.public_rooms_endpoint}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                rooms = data.get('chunk', [])
                
                for room in rooms[:20]:  # Limit to 20 rooms
                    # Check room name and topic
                    name = room.get('name', '')
                    topic = room.get('topic', '')
                    full_text = f"{name} {topic}".lower()
                    
                    matched_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in full_text:
                            matched_keywords.append(keyword)
                    
                    if matched_keywords:
                        results.append({
                            "source": "Matrix",
                            "matched_term": ", ".join(matched_keywords),
                            "raw_text": f"Room: {name}\nTopic: {topic}",
                            "title": f"Matrix Room: {name}",
                            "url": f"https://matrix.to/#/{room.get('room_id', '')}",
                            "timestamp": datetime.utcnow().isoformat(),
                            "severity": "LOW",
                            "category": "matrix_room"
                        })
                        
        except Exception as e:
            logger.error(f"Error checking Matrix rooms: {e}")
        
        return results


def monitor_alternative_sources(targets_file: str = None) -> List[Dict[str, Any]]:
    """
    Monitor all alternative sources
    
    Args:
        targets_file: Path to targets.json
        
    Returns:
        Combined results
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
    
    keywords = (
        targets.get('keywords', [])[:10] +  # Limit keywords
        targets.get('domains', [])[:10] +
        targets.get('company_names', [])[:10]
    )
    
    all_results = []
    
    # Monitor Telegram
    telegram = TelegramPublicMonitor()
    logger.info("Monitoring Telegram channels...")
    telegram_results = telegram.search_public_channels(keywords)
    all_results.extend(telegram_results)
    
    # Monitor Reddit
    reddit = RedditMonitor()
    logger.info("Monitoring Reddit...")
    reddit_results = reddit.search_subreddits(keywords)
    all_results.extend(reddit_results)
    
    # Monitor Matrix (optional)
    matrix = MatrixPublicRoomMonitor()
    logger.info("Monitoring Matrix rooms...")
    matrix_results = matrix.search_public_rooms(keywords[:5])  # Fewer keywords
    all_results.extend(matrix_results)
    
    return all_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test alternative sources
    results = monitor_alternative_sources()
    
    print(f"Found {len(results)} results from alternative sources")
    for result in results[:5]:
        print(f"- [{result['source']}] {result['title'][:60]}...")
        print(f"  Matched: {result['matched_term']}")
        print(f"  Severity: {result['severity']}")