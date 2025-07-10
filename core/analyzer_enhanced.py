"""
拡張版アナライザー
優先度とカテゴリベースのフィルタリング機能付き
"""
import yaml
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from core.analyzer import DarkwebAnalyzer

class EnhancedAnalyzer(DarkwebAnalyzer):
    def __init__(self, targets_file: str = None, config_file: str = None):
        super().__init__(targets_file)
        
        # Load alert configuration
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'config',
                'alert_config.yaml'
            )
        
        with open(config_file, 'r', encoding='utf-8') as f:
            self.alert_config = yaml.safe_load(f)
    
    def analyze(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enhanced analysis with priority and category filtering
        """
        # First, perform basic analysis
        basic_result = super().analyze(entry)
        
        if not basic_result:
            return None
        
        # Get priority and category of matched term
        matched_term = basic_result['matched_term']
        priority = self._get_target_priority(matched_term)
        category = self._get_target_category(matched_term)
        
        # Apply priority-based filtering
        if not self._should_alert_by_priority(basic_result, priority):
            return None
        
        # Apply category-based enhancements
        if category:
            basic_result = self._apply_category_rules(basic_result, category)
        
        # Adjust severity based on source reliability
        basic_result = self._adjust_severity_by_source(basic_result)
        
        # Add priority and category to result
        basic_result['target_priority'] = priority or 'DEFAULT'
        basic_result['target_category'] = category or 'General'
        
        # Add enhanced metadata
        basic_result['enhanced_analysis'] = {
            'priority_boost': priority == 'HIGH',
            'category_alert': category in self.alert_config.get('category_rules', {}),
            'source_reliability': self._get_source_reliability(basic_result['source']),
            'working_hours_alert': self._is_working_hours()
        }
        
        return basic_result
    
    def _get_target_priority(self, term: str) -> Optional[str]:
        """Get priority of a target"""
        priority_targets = self.targets.get('priority_targets', {})
        
        # Check exact match
        if term in priority_targets:
            return priority_targets[term]
        
        # Check partial match
        for target, priority in priority_targets.items():
            if target.lower() in term.lower() or term.lower() in target.lower():
                return priority
        
        return None
    
    def _get_target_category(self, term: str) -> Optional[str]:
        """Get category of a target"""
        categories = self.targets.get('categories', {})
        
        # Check exact match
        if term in categories:
            return categories[term]
        
        # Check partial match
        for target, category in categories.items():
            if target.lower() in term.lower() or term.lower() in target.lower():
                return category
        
        return None
    
    def _should_alert_by_priority(self, alert: Dict[str, Any], priority: Optional[str]) -> bool:
        """Check if alert should be sent based on priority"""
        thresholds = self.alert_config.get('alert_thresholds', {})
        
        if priority:
            priority_key = f"{priority}_PRIORITY"
            if priority_key in thresholds:
                config = thresholds[priority_key]
            else:
                config = thresholds.get('DEFAULT', {})
        else:
            config = thresholds.get('DEFAULT', {})
        
        # Check confidence score
        min_confidence = config.get('confidence_score', 85)
        if alert.get('confidence_score', 0) < min_confidence:
            return False
        
        # Check severity level
        allowed_severities = config.get('severity_levels', ['HIGH', 'MEDIUM'])
        if alert.get('severity', 'INFO') not in allowed_severities:
            return False
        
        return True
    
    def _apply_category_rules(self, alert: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Apply category-specific rules"""
        category_rules = self.alert_config.get('category_rules', {}).get(category, {})
        
        if category_rules.get('alert_all'):
            # Override severity for important categories
            alert['severity'] = 'HIGH'
            alert['category_override'] = True
        
        # Check for category-specific keywords
        extra_keywords = category_rules.get('extra_keywords', [])
        focus_keywords = category_rules.get('focus_keywords', [])
        
        text_lower = alert.get('raw_text', '').lower()
        
        for keyword in extra_keywords + focus_keywords:
            if keyword.lower() in text_lower:
                # Boost severity if category keywords found
                if alert['severity'] == 'LOW':
                    alert['severity'] = 'MEDIUM'
                elif alert['severity'] == 'MEDIUM':
                    alert['severity'] = 'HIGH'
                break
        
        return alert
    
    def _adjust_severity_by_source(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust severity based on source reliability"""
        source = alert.get('source', '').split('-')[0]  # Get base source name
        reliability = self._get_source_reliability(source)
        
        # Downgrade severity for unreliable sources
        if reliability < 0.7 and alert.get('severity') == 'MEDIUM':
            alert['severity'] = 'LOW'
            alert['reliability_adjusted'] = True
        
        # Add reliability score
        alert['source_reliability'] = reliability
        
        return alert
    
    def _get_source_reliability(self, source: str) -> float:
        """Get reliability score for a source"""
        reliability_scores = self.alert_config.get('source_reliability', {})
        
        # Check exact match
        if source in reliability_scores:
            return reliability_scores[source]
        
        # Check partial match
        for src, score in reliability_scores.items():
            if src.lower() in source.lower():
                return score
        
        return 0.5  # Default reliability
    
    def _is_working_hours(self) -> bool:
        """Check if current time is within working hours"""
        wh_config = self.alert_config.get('working_hours', {})
        
        if not wh_config.get('enabled'):
            return True
        
        # This is a simplified implementation
        # In production, use proper timezone handling
        now = datetime.now()
        
        # Check weekend
        if now.weekday() >= 5 and not wh_config.get('weekend_alerts'):
            return False
        
        # Check time (simplified)
        current_hour = now.hour
        start_hour = int(wh_config.get('start', '09:00').split(':')[0])
        end_hour = int(wh_config.get('end', '18:00').split(':')[0])
        
        return start_hour <= current_hour < end_hour


# Convenience function
def analyze_with_priority(entry: Dict[str, Any], 
                         targets_file: str = None,
                         config_file: str = None) -> Optional[Dict[str, Any]]:
    """
    Analyze with priority and category filtering
    """
    analyzer = EnhancedAnalyzer(targets_file, config_file)
    return analyzer.analyze(entry)


if __name__ == "__main__":
    # Test enhanced analyzer
    test_entry = {
        "source": "Test-HighReliability",
        "matched_term": "sony.co.jp",  # High priority target
        "raw_text": "Found Sony database with passwords",
        "url": "http://test.onion",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    analyzer = EnhancedAnalyzer()
    result = analyzer.analyze(test_entry)
    
    if result:
        print(f"Alert generated:")
        print(f"  Priority: {result.get('target_priority')}")
        print(f"  Category: {result.get('target_category')}")
        print(f"  Severity: {result['severity']}")
        print(f"  Source Reliability: {result.get('source_reliability', 0):.2f}")