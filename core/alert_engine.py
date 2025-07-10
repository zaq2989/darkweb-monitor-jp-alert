import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class AlertEngine:
    def __init__(self):
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not self.slack_webhook_url:
            print("Warning: SLACK_WEBHOOK_URL not found. Alerts will be printed to console only.")
    
    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send alert to configured channels
        
        Args:
            alert_data: Alert information including severity, matched_term, etc.
        
        Returns:
            True if alert was sent successfully
        """
        # Format alert message
        message = self._format_alert_message(alert_data)
        
        # Send to Slack if configured
        if self.slack_webhook_url:
            return self._send_slack_alert(message, alert_data)
        else:
            # Fallback to console output
            print("=" * 80)
            print(f"ALERT: {alert_data.get('severity', 'UNKNOWN')} SEVERITY")
            print(message)
            print("=" * 80)
            return True
    
    def _format_alert_message(self, alert_data: Dict[str, Any]) -> str:
        """
        Format alert data into readable message
        
        Args:
            alert_data: Alert information
        
        Returns:
            Formatted message string
        """
        severity = alert_data.get('severity', 'UNKNOWN')
        matched_term = alert_data.get('matched_term', 'N/A')
        source = alert_data.get('source', 'Unknown')
        url = alert_data.get('url', 'N/A')
        timestamp = alert_data.get('timestamp', datetime.utcnow().isoformat())
        category = alert_data.get('category', 'Unknown')
        confidence_score = alert_data.get('confidence_score', 0)
        
        # Extract snippet from raw text
        raw_text = alert_data.get('raw_text', '')
        snippet = self._extract_snippet(raw_text, matched_term)
        
        message = f"""
🚨 *Darkweb Alert - {severity} Severity*

*Matched Term:* {matched_term}
*Category:* {category}
*Confidence Score:* {confidence_score:.2f}%
*Source:* {source}
*URL:* {url}
*Detection Time:* {timestamp}

*Context Snippet:*
```
{snippet}
```
"""
        return message.strip()
    
    def _extract_snippet(self, text: str, term: str, context_chars: int = 200) -> str:
        """
        Extract relevant snippet around matched term
        
        Args:
            text: Full text content
            term: Matched term
            context_chars: Number of characters to show before/after match
        
        Returns:
            Text snippet with context
        """
        if not text:
            return "No content available"
        
        # Find term position (case-insensitive)
        lower_text = text.lower()
        lower_term = term.lower()
        
        pos = lower_text.find(lower_term)
        if pos == -1:
            # Term not found, return beginning of text
            return text[:context_chars * 2] + "..." if len(text) > context_chars * 2 else text
        
        # Extract snippet with context
        start = max(0, pos - context_chars)
        end = min(len(text), pos + len(term) + context_chars)
        
        snippet = text[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def _send_slack_alert(self, message: str, alert_data: Dict[str, Any]) -> bool:
        """
        Send alert to Slack webhook
        
        Args:
            message: Formatted message
            alert_data: Original alert data
        
        Returns:
            True if sent successfully
        """
        severity = alert_data.get('severity', 'UNKNOWN')
        
        # Color coding based on severity
        color_map = {
            'HIGH': '#ff0000',      # Red
            'MEDIUM': '#ff9900',    # Orange
            'LOW': '#ffcc00',       # Yellow
            'INFO': '#36a64f'       # Green
        }
        
        color = color_map.get(severity.upper(), '#808080')  # Default gray
        
        # Slack message payload
        payload = {
            "attachments": [
                {
                    "color": color,
                    "text": message,
                    "mrkdwn_in": ["text"],
                    "footer": "Darkweb Monitor JP",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }
        
        try:
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to send Slack alert: {e}")
            return False


# Convenience function for external use
def send_alert(alert_data: Dict[str, Any]) -> bool:
    """
    Send alert using default alert engine
    
    Args:
        alert_data: Alert information
    
    Returns:
        True if alert was sent successfully
    """
    engine = AlertEngine()
    return engine.send_alert(alert_data)


if __name__ == "__main__":
    # Test alert
    test_alert = {
        "severity": "HIGH",
        "matched_term": "sony.co.jp",
        "source": "DarkOwl",
        "url": "http://example.onion/leak123",
        "timestamp": datetime.utcnow().isoformat(),
        "category": "Domain",
        "confidence_score": 95.5,
        "raw_text": "Found database dump containing sony.co.jp employee credentials..."
    }
    
    send_alert(test_alert)