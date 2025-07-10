import json
import re
from typing import Dict, Any, List, Optional, Tuple
from fuzzywuzzy import fuzz
from datetime import datetime

class DarkwebAnalyzer:
    def __init__(self, targets_file: str = None):
        if targets_file:
            with open(targets_file, 'r', encoding='utf-8') as f:
                self.targets = json.load(f)
        else:
            # Default empty targets
            self.targets = {
                "keywords": [],
                "domains": [],
                "company_names": []
            }
        
        # Severity keywords mapping
        self.severity_patterns = {
            "HIGH": [
                r"password[s]?\s*(:|=|dump|leak)",
                r"credential[s]?\s*(:|=|dump|leak)",
                r"database\s*dump",
                r"sql\s*dump",
                r"admin\s*access",
                r"root\s*access",
                r"api\s*key[s]?",
                r"private\s*key",
                r"secret\s*key",
                r"漏洩",
                r"流出",
                r"ハッキング",
                r"侵入"
            ],
            "MEDIUM": [
                r"email[s]?\s*(list|dump|leak)",
                r"user[s]?\s*(list|data|info)",
                r"employee[s]?\s*(list|data|info)",
                r"personal\s*data",
                r"個人情報",
                r"メールアドレス",
                r"社員"
            ],
            "LOW": [
                r"mention",
                r"discussion",
                r"forum",
                r"thread",
                r"言及",
                r"議論"
            ]
        }
        
        # Compile regex patterns
        self.compiled_severity_patterns = {}
        for severity, patterns in self.severity_patterns.items():
            self.compiled_severity_patterns[severity] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def analyze(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a darkweb entry for Japanese company mentions
        
        Args:
            entry: Normalized darkweb entry
        
        Returns:
            Alert data if match found, None otherwise
        """
        raw_text = entry.get('raw_text', '')
        title = entry.get('title', '')
        combined_text = f"{title} {raw_text}".lower()
        
        # Check for matches
        match_result = self._find_best_match(combined_text)
        
        if not match_result:
            return None
        
        matched_term, category, confidence_score = match_result
        
        # Only alert if confidence is above threshold
        if confidence_score < 85:
            return None
        
        # Determine severity
        severity = self._determine_severity(combined_text)
        
        # Build alert data
        alert_data = {
            **entry,  # Include all original entry data
            "matched_term": matched_term,
            "category": category,
            "confidence_score": confidence_score,
            "severity": severity,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "alert": True
        }
        
        return alert_data
    
    def _find_best_match(self, text: str) -> Optional[Tuple[str, str, float]]:
        """
        Find best matching target in text
        
        Args:
            text: Text to search in
        
        Returns:
            Tuple of (matched_term, category, confidence_score) or None
        """
        best_match = None
        best_score = 0
        best_category = None
        
        # Check domains (exact match preferred)
        for domain in self.targets.get('domains', []):
            if domain.lower() in text:
                # Exact domain match
                return (domain, "Domain", 100.0)
        
        # Check keywords with fuzzy matching
        for keyword in self.targets.get('keywords', []):
            # Try exact match first
            if keyword.lower() in text:
                return (keyword, "Keyword", 100.0)
            
            # Fuzzy match for longer terms
            if len(keyword) > 5:
                score = fuzz.partial_ratio(keyword.lower(), text)
                if score > best_score:
                    best_score = score
                    best_match = keyword
                    best_category = "Keyword"
        
        # Check company names with fuzzy matching
        for company in self.targets.get('company_names', []):
            # Japanese company names need special handling
            if self._is_japanese(company):
                # For Japanese, look for exact substring match
                if company in text:
                    return (company, "Company Name", 100.0)
            else:
                # For English names, use fuzzy matching
                score = fuzz.partial_ratio(company.lower(), text)
                if score > best_score:
                    best_score = score
                    best_match = company
                    best_category = "Company Name"
        
        if best_match and best_score >= 85:
            return (best_match, best_category, float(best_score))
        
        return None
    
    def _is_japanese(self, text: str) -> bool:
        """Check if text contains Japanese characters"""
        return bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', text))
    
    def _determine_severity(self, text: str) -> str:
        """
        Determine alert severity based on content
        
        Args:
            text: Text to analyze
        
        Returns:
            Severity level (HIGH, MEDIUM, LOW, INFO)
        """
        # Check patterns in order of severity
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            patterns = self.compiled_severity_patterns[severity]
            for pattern in patterns:
                if pattern.search(text):
                    return severity
        
        # Default to INFO if no specific patterns match
        return "INFO"
    
    def batch_analyze(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple entries
        
        Args:
            entries: List of darkweb entries
        
        Returns:
            List of alerts
        """
        alerts = []
        for entry in entries:
            alert = self.analyze(entry)
            if alert:
                alerts.append(alert)
        
        return alerts


# Convenience function
def analyze(entry: Dict[str, Any], targets_file: str = None) -> Optional[Dict[str, Any]]:
    """
    Analyze a single darkweb entry
    
    Args:
        entry: Darkweb entry to analyze
        targets_file: Optional path to targets.json
    
    Returns:
        Alert data if match found, None otherwise
    """
    if targets_file is None:
        import os
        targets_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'config', 
            'targets.json'
        )
    
    analyzer = DarkwebAnalyzer(targets_file)
    return analyzer.analyze(entry)


if __name__ == "__main__":
    # Test analyzer
    test_entry = {
        "source": "Test",
        "raw_text": "Found database dump with sony.co.jp employee passwords and personal information",
        "url": "http://example.onion/test",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    import os
    targets_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'targets.json')
    
    result = analyze(test_entry, targets_file)
    if result:
        print(f"Alert generated: {result['severity']} - {result['matched_term']}")
        print(f"Confidence: {result['confidence_score']}%")
    else:
        print("No alert generated")