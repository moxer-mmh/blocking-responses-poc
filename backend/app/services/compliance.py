"""Compliance and pattern detection services."""

import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.requests import ComplianceResult


# Compliance policy configuration
COMPLIANCE_POLICY: Dict[str, Any] = {
    "weights": {
        "email": 0.4,
        "phone": 0.5,
        "ssn": 1.2,
        "dob": 0.6,
        "address": 0.3,
        "credit_card": 1.5,
        "iban": 1.0,
        "routing_number": 0.8,
        "bank_account": 1.0,
        "medical_record": 1.0,
        "diagnosis": 0.7,
        "medication": 0.6,
        "password": 1.5,
        "api_key": 1.8,
        "secret": 1.5,
        "phi_hint": 0.2,
        "pci_hint": 0.2,
    },
    "regional_weights": {
        "HIPAA": {
            "medical_record": 1.5,
            "diagnosis": 1.0,
            "medication": 0.8,
            "phi_hint": 0.4,
        },
        "PCI": {
            "credit_card": 2.0,
            "bank_account": 1.5,
            "routing_number": 1.2,
            "pci_hint": 0.3,
        },
        "GDPR": {
            "email": 0.6,
            "phone": 0.6,
            "address": 0.5,
        },
        "CCPA": {
            "email": 0.5,
            "phone": 0.6,
            "address": 0.4,
        },
    },
    "threshold": 0.7,
    "phi_terms": [
        "patient", "medical", "diagnosis", "prescription", "doctor", "clinic", 
        "hospital", "healthcare", "treatment", "medication", "symptoms"
    ],
    "pci_terms": [
        "payment", "transaction", "billing", "invoice", "purchase", "checkout",
        "credit", "debit", "merchant", "pos", "terminal"
    ],
}


class RegulatedPatternDetector:
    """Enhanced pattern detection for regulated industries."""
    
    def __init__(self):
        # Enhanced patterns for regulated industries
        self.patterns = {
            # PII patterns
            "email": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b"),
            "phone": re.compile(
                r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){1}\d{3}[-.\s]?\d{4}(?!\d)"
            ),
            "ssn": re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
            "dob": re.compile(
                r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{4})\b",
                re.I,
            ),
            "address": re.compile(
                r"\b\d{1,5}\s+[A-Za-z0-9.\-\s]+\s+(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Lane|Ln\.?|Boulevard|Blvd\.?|Drive|Dr\.?|Court|Ct\.?)\b",
                re.I,
            ),
            # PCI patterns
            "credit_card_candidate": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
            "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
            "routing_number": re.compile(r"\b\d{9}\b"),
            "bank_account": re.compile(
                r"\b(?:account\s*number|acct\s*#?)\s*:?\s*\d{6,17}\b", re.I
            ),
            # PHI patterns
            "medical_record": re.compile(
                r"\b(?:mrn|medical\s*record\s*number)\s*:?\s*\d+\b", re.I
            ),
            "diagnosis": re.compile(
                r"\b(?:diagnosed\s+with|diagnosis\s*:)\s*[a-z\s]+\b", re.I
            ),
            "medication": re.compile(
                r"\b(?:prescribed|taking|medication)\s+[a-z]+(?:cillin|prazole|statin|mycin)\b",
                re.I,
            ),
            # Security patterns
            "password": re.compile(
                r"\b(?:password|passwd|passphrase)\s*[:=]?\s*\S+\b", re.I
            ),
            "api_key": re.compile(
                r"\b(?:api[_-]?key|secret[_-]?key|bearer\s+[A-Za-z0-9\._\-]+)\b", re.I
            ),
            "secret": re.compile(r"\b(?:secret|token)\s*[:=]\s*\S+\b", re.I),
            # Contextual patterns
            "phi_context": re.compile("|".join(COMPLIANCE_POLICY["phi_terms"]), re.I),
            "pci_context": re.compile("|".join(COMPLIANCE_POLICY["pci_terms"]), re.I),
        }

    def luhn_check(self, card_number: str) -> bool:
        """Luhn algorithm for credit card validation."""
        digits = [int(d) for d in re.sub(r"[^\d]", "", card_number)]
        if len(digits) < 13 or len(digits) > 19:
            return False

        checksum = 0
        is_even = False
        for d in reversed(digits):
            if is_even:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
            is_even = not is_even

        return checksum % 10 == 0

    def assess_compliance_risk(
        self, text: str, region: Optional[str] = None
    ) -> ComplianceResult:
        """Comprehensive compliance risk assessment."""
        weights = COMPLIANCE_POLICY["weights"].copy()

        # Apply regional weight adjustments
        if region and region in COMPLIANCE_POLICY["regional_weights"]:
            weights.update(COMPLIANCE_POLICY["regional_weights"][region])

        score = 0.0
        triggered_rules = []

        # Pattern-based detection
        for pattern_name, pattern in self.patterns.items():
            if pattern_name == "credit_card_candidate":
                # Special handling for credit cards with Luhn check
                for match in pattern.finditer(text):
                    if self.luhn_check(match.group(0)):
                        score += weights.get("credit_card", 1.5)
                        triggered_rules.append(
                            "credit_card: Valid credit card number detected"
                        )
                        break
            elif pattern.search(text):
                weight_key = pattern_name.replace("_candidate", "").replace(
                    "_context", "_hint"
                )
                score += weights.get(weight_key, 0.5)
                triggered_rules.append(f"{pattern_name}: Pattern detected")

        # Create hash of sensitive snippet if needed
        snippet_hash = None
        if score > 0:
            snippet_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        blocked = score >= settings.risk_threshold

        return ComplianceResult(
            score=score,
            blocked=blocked,
            triggered_rules=triggered_rules,
            snippet_hash=snippet_hash,
            compliance_region=region,
            timestamp=datetime.utcnow(),
        )
