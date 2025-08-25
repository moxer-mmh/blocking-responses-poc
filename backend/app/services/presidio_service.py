"""Presidio integration service for PII/PHI detection."""

import logging
from typing import Dict, Any, List, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

# Check if Presidio is available
try:
    from presidio_analyzer import (
        AnalyzerEngine,
        PatternRecognizer,
        Pattern,
    )
    from presidio_analyzer.nlp_engine import SpacyNlpEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logger.warning("Presidio not available. Install with: pip install presidio-analyzer")


class PresidioDetector:
    """Microsoft Presidio integration for industrial-grade PII/PHI detection."""
    
    def __init__(self):
        self.analyzer = None
        if PRESIDIO_AVAILABLE:
            try:
                self._initialize_presidio()
            except Exception as e:
                logger.warning(f"Failed to initialize Presidio: {e}")
                self.analyzer = None

    def _initialize_presidio(self):
        """Initialize Presidio with custom recognizers for regulated industries."""
        try:
            # Use basic configuration - it should work without spaCy models
            self.analyzer = AnalyzerEngine()
            logger.info("Presidio initialized with basic configuration")
        except Exception as e:
            logger.error(f"Failed to initialize Presidio: {e}")
            self.analyzer = None

        # Add custom recognizers for regulated industries if analyzer is available
        if self.analyzer:
            self._add_custom_recognizers()
            logger.info("Custom recognizers added to Presidio")

    def _add_custom_recognizers(self):
        """Add custom pattern recognizers for specific regulated content."""
        if not self.analyzer:
            return

        # Medical Record Number recognizer
        mrn_pattern = Pattern(
            name="medical_record_number",
            regex=r"\b(?:mrn|medical\s*record\s*number)\s*:?\s*\d{6,10}\b",
            score=0.9,
        )
        mrn_recognizer = PatternRecognizer(
            supported_entity="MEDICAL_RECORD_NUMBER", patterns=[mrn_pattern]
        )
        self.analyzer.registry.add_recognizer(mrn_recognizer)

        # Enhanced credit card recognizer with better patterns
        cc_pattern = Pattern(
            name="enhanced_credit_card",
            regex=r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6011)[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            score=0.95,
        )
        cc_recognizer = PatternRecognizer(
            supported_entity="ENHANCED_CREDIT_CARD", patterns=[cc_pattern]
        )
        self.analyzer.registry.add_recognizer(cc_recognizer)

    def analyze_text(self, text: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Analyze text with Presidio and return risk score and entities."""
        if not self.analyzer:
            return 0.0, []

        try:
            results = self.analyzer.analyze(text=text, language="en")
            score = 0.0
            entities = []

            # Base weights for different entity types
            entity_weights = {
                "PERSON": 0.5,
                "EMAIL_ADDRESS": 0.4,
                "PHONE_NUMBER": 0.5,
                "US_SSN": 1.2,
                "CREDIT_CARD": 1.5,
                "US_BANK_NUMBER": 1.0,
                "MEDICAL_RECORD_NUMBER": 1.0,
                "ENHANCED_CREDIT_CARD": 1.5,
                "DATE_TIME": 0.2,
                "LOCATION": 0.3,
                "URL": 0.2,
                "US_DRIVER_LICENSE": 0.8,
                "US_PASSPORT": 0.9,
            }

            for result in results:
                if result.score >= settings.presidio_confidence_threshold:
                    entity_weight = entity_weights.get(result.entity_type, 0.3)
                    score += entity_weight * result.score
                    entities.append(
                        {
                            "entity_type": result.entity_type,
                            "start": result.start,
                            "end": result.end,
                            "score": result.score,
                            "text": text[result.start: result.end],
                        }
                    )

            return score, entities
        except Exception as e:
            logger.error(f"Presidio analysis failed: {e}")
            return 0.0, []

    def is_available(self) -> bool:
        """Check if Presidio analyzer is available and initialized."""
        return self.analyzer is not None
