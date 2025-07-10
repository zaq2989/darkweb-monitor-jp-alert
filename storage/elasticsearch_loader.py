import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class ElasticsearchLoader:
    def __init__(self):
        self.host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        self.port = int(os.getenv('ELASTICSEARCH_PORT', '9200'))
        self.index_name = os.getenv('ELASTICSEARCH_INDEX', 'darkweb-alerts')
        
        # Initialize Elasticsearch client
        self.es = Elasticsearch(
            [{'host': self.host, 'port': self.port}],
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        # Create index if it doesn't exist
        self._create_index_if_not_exists()
    
    def _create_index_if_not_exists(self):
        """Create Elasticsearch index with proper mapping"""
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "analysis_timestamp": {"type": "date"},
                        "discovered_date": {"type": "date"},
                        "source": {"type": "keyword"},
                        "matched_term": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "category": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "confidence_score": {"type": "float"},
                        "raw_text": {"type": "text"},
                        "title": {"type": "text"},
                        "url": {"type": "keyword"},
                        "site_name": {"type": "keyword"},
                        "site_type": {"type": "keyword"},
                        "language": {"type": "keyword"},
                        "alert": {"type": "boolean"},
                        "metadata": {
                            "type": "object",
                            "dynamic": True
                        }
                    }
                }
            }
            
            try:
                self.es.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Created Elasticsearch index: {self.index_name}")
            except Exception as e:
                logger.error(f"Failed to create index: {e}")
                raise
    
    def store_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Store alert in Elasticsearch
        
        Args:
            alert_data: Alert data to store
        
        Returns:
            Document ID
        """
        try:
            # Ensure timestamps are properly formatted
            if 'timestamp' in alert_data:
                alert_data['timestamp'] = self._ensure_iso_format(alert_data['timestamp'])
            if 'analysis_timestamp' in alert_data:
                alert_data['analysis_timestamp'] = self._ensure_iso_format(alert_data['analysis_timestamp'])
            if 'discovered_date' in alert_data:
                alert_data['discovered_date'] = self._ensure_iso_format(alert_data['discovered_date'])
            
            # Index the document
            response = self.es.index(
                index=self.index_name,
                body=alert_data
            )
            
            logger.debug(f"Stored alert in Elasticsearch: {response['_id']}")
            return response['_id']
            
        except Exception as e:
            logger.error(f"Failed to store alert in Elasticsearch: {e}")
            raise
    
    def store_batch(self, alerts: List[Dict[str, Any]]) -> int:
        """
        Store multiple alerts in batch
        
        Args:
            alerts: List of alerts to store
        
        Returns:
            Number of successfully stored alerts
        """
        if not alerts:
            return 0
        
        # Prepare bulk operations
        bulk_data = []
        for alert in alerts:
            # Ensure timestamps are properly formatted
            if 'timestamp' in alert:
                alert['timestamp'] = self._ensure_iso_format(alert['timestamp'])
            if 'analysis_timestamp' in alert:
                alert['analysis_timestamp'] = self._ensure_iso_format(alert['analysis_timestamp'])
            if 'discovered_date' in alert:
                alert['discovered_date'] = self._ensure_iso_format(alert['discovered_date'])
            
            bulk_data.append({"index": {"_index": self.index_name}})
            bulk_data.append(alert)
        
        try:
            response = self.es.bulk(body=bulk_data)
            
            # Count successful operations
            success_count = sum(1 for item in response['items'] if item['index']['status'] < 300)
            
            logger.info(f"Stored {success_count}/{len(alerts)} alerts in Elasticsearch")
            return success_count
            
        except Exception as e:
            logger.error(f"Failed to bulk store alerts: {e}")
            raise
    
    def search_alerts(self, query: Dict[str, Any], size: int = 100) -> List[Dict[str, Any]]:
        """
        Search alerts in Elasticsearch
        
        Args:
            query: Elasticsearch query
            size: Maximum number of results
        
        Returns:
            List of matching alerts
        """
        try:
            response = self.es.search(
                index=self.index_name,
                body={"query": query, "size": size, "sort": [{"timestamp": {"order": "desc"}}]}
            )
            
            alerts = []
            for hit in response['hits']['hits']:
                alert = hit['_source']
                alert['_id'] = hit['_id']
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to search alerts: {e}")
            raise
    
    def get_recent_alerts(self, hours: int = 24, severity: str = None) -> List[Dict[str, Any]]:
        """
        Get recent alerts from Elasticsearch
        
        Args:
            hours: Number of hours to look back
            severity: Optional severity filter
        
        Returns:
            List of recent alerts
        """
        query = {
            "bool": {
                "must": [
                    {
                        "range": {
                            "timestamp": {
                                "gte": f"now-{hours}h"
                            }
                        }
                    }
                ]
            }
        }
        
        if severity:
            query["bool"]["must"].append({
                "term": {"severity": severity}
            })
        
        return self.search_alerts(query)
    
    def _ensure_iso_format(self, timestamp: Any) -> str:
        """Ensure timestamp is in ISO format"""
        if isinstance(timestamp, str):
            # Already a string, assume it's properly formatted
            return timestamp
        elif isinstance(timestamp, datetime):
            return timestamp.isoformat()
        else:
            # Try to convert to datetime
            try:
                dt = datetime.fromisoformat(str(timestamp))
                return dt.isoformat()
            except:
                # Fallback to current time
                return datetime.utcnow().isoformat()


if __name__ == "__main__":
    # Test Elasticsearch loader
    loader = ElasticsearchLoader()
    
    test_alert = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": "Test",
        "matched_term": "sony.co.jp",
        "category": "Domain",
        "severity": "HIGH",
        "confidence_score": 95.5,
        "raw_text": "Test alert for Elasticsearch",
        "url": "http://example.onion/test",
        "alert": True
    }
    
    try:
        doc_id = loader.store_alert(test_alert)
        print(f"Stored test alert with ID: {doc_id}")
        
        # Search for recent alerts
        recent = loader.get_recent_alerts(hours=1)
        print(f"Found {len(recent)} recent alerts")
    except Exception as e:
        print(f"Elasticsearch test failed: {e}")