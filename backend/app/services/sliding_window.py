"""Sliding window analysis service for efficient compliance checking."""

from datetime import datetime
from typing import Dict, Any, Optional
from app.core.config import settings
from app.utils.tokens import token_count


class SlidingWindowAnalyzer:
    """Efficient sliding window analysis for compliance checking."""
    
    def __init__(self):
        self.window_size = settings.analysis_window_size
        self.overlap_size = settings.analysis_overlap
        self.frequency = settings.analysis_frequency
        self.last_analysis_position = 0
        self.analysis_history = []
        self.cumulative_risk = 0.0
        self.total_tokens_processed = 0
        
    def should_analyze(self, current_position: int) -> bool:
        """Determine if we should run analysis at current position."""
        tokens_since_last = current_position - self.last_analysis_position
        return tokens_since_last >= self.frequency
    
    def extract_analysis_window(self, full_text: str, current_position: int) -> tuple[str, int, int]:
        """Extract the analysis window from full text."""
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            
            tokens = enc.encode(full_text)
            total_tokens = len(tokens)
            
            # Calculate window boundaries
            window_start = max(0, current_position - self.window_size + self.overlap_size)
            window_end = min(total_tokens, current_position + self.overlap_size)
            
            # Extract window tokens and convert back to text
            window_tokens = tokens[window_start:window_end]
            window_text = enc.decode(window_tokens)
            
            return window_text, window_start, window_end
        except ImportError:
            # Fallback: character-based estimation
            chars_per_token = 4
            char_start = max(0, (current_position - self.window_size + self.overlap_size) * chars_per_token)
            char_end = min(len(full_text), (current_position + self.overlap_size) * chars_per_token)
            
            return full_text[char_start:char_end], char_start // chars_per_token, char_end // chars_per_token
    
    def analyze_window(
        self, 
        window_text: str, 
        window_start: int, 
        window_end: int, 
        region: Optional[str] = None,
        pattern_detector=None,
        presidio_detector=None
    ) -> Dict[str, Any]:
        """Analyze a specific window for compliance violations."""
        # Pattern-based analysis
        if pattern_detector:
            compliance_result = pattern_detector.assess_compliance_risk(window_text, region)
            pattern_score = compliance_result.score
            triggered_rules = compliance_result.triggered_rules
        else:
            pattern_score = 0.0
            triggered_rules = []
        
        # Presidio-based analysis
        if presidio_detector:
            presidio_score, presidio_entities = presidio_detector.analyze_text(window_text)
        else:
            presidio_score = 0.0
            presidio_entities = []
        
        # Combine scores
        total_score = pattern_score + presidio_score
        
        analysis_result = {
            "window_text": window_text,
            "window_start": window_start,
            "window_end": window_end,
            "window_size": window_end - window_start,
            "pattern_score": pattern_score,
            "presidio_score": presidio_score,
            "total_score": total_score,
            "triggered_rules": triggered_rules,
            "presidio_entities": presidio_entities,
            "blocked": total_score >= settings.risk_threshold,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_position": self.total_tokens_processed
        }
        
        # Update state
        self.last_analysis_position = self.total_tokens_processed
        self.cumulative_risk = max(self.cumulative_risk, total_score)
        self.analysis_history.append(analysis_result)
        
        # Keep only last 10 analyses for memory efficiency
        if len(self.analysis_history) > 10:
            self.analysis_history = self.analysis_history[-10:]
            
        return analysis_result
    
    def process_new_tokens(
        self, 
        new_text: str, 
        full_text: str, 
        region: Optional[str] = None,
        pattern_detector=None,
        presidio_detector=None
    ) -> Optional[Dict[str, Any]]:
        """Process new tokens and return analysis result if analysis should be performed."""
        # Update token count
        new_token_count = token_count(new_text)
        self.total_tokens_processed += new_token_count
        
        # Check if we should analyze
        if not self.should_analyze(self.total_tokens_processed):
            return None
            
        # Extract and analyze window
        window_text, window_start, window_end = self.extract_analysis_window(
            full_text, self.total_tokens_processed
        )
        
        return self.analyze_window(
            window_text, window_start, window_end, region, 
            pattern_detector, presidio_detector
        )
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get statistics about the analysis process."""
        total_analyses = len(self.analysis_history)
        blocked_analyses = sum(1 for a in self.analysis_history if a["blocked"])
        
        return {
            "total_tokens_processed": self.total_tokens_processed,
            "total_analyses_performed": total_analyses,
            "blocked_analyses": blocked_analyses,
            "analysis_frequency": self.frequency,
            "window_size": self.window_size,
            "overlap_size": self.overlap_size,
            "cumulative_risk": self.cumulative_risk,
            "last_analysis_position": self.last_analysis_position,
            "efficiency_ratio": self.total_tokens_processed / max(total_analyses, 1),  # tokens per analysis
            "recent_analyses": self.analysis_history[-5:] if self.analysis_history else []
        }
