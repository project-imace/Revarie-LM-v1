"""
apa_compliance.py – Safety Guardrail: APA Compliance Checker

Enforces American Psychological Association (APA) ethical guidelines for
human-AI interaction in research contexts. Ensures informed consent,
confidentiality, debriefing, and avoidance of harm.

Theoretical Foundations:
- APA Ethical Principles of Psychologists and Code of Conduct (2017)
- APA Guidelines for Psychological Practice with AI (2025)
- Belmont Report (1979): Respect for Persons, Beneficence, Justice
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class ComplianceLevel(Enum):
    COMPLIANT = "compliant"
    FLAGGED = "flagged"
    VIOLATION = "violation"


@dataclass
class ComplianceResult:
    """Result of an APA compliance check."""
    level: ComplianceLevel
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 1.0
    requires_human_review: bool = False
    timestamp: float = field(default_factory=time.time)


class APAComplianceChecker:
    """
    Enforces APA ethical guidelines for AI-participant interactions.
    """

    def __init__(self, study_context: Optional[Dict[str, Any]] = None):
        """
        Initialize with study context.
        
        Args:
            study_context: Dictionary containing study metadata
                - study_name: Name of the research study
                - irb_approval: IRB approval number
                - principal_investigator: Contact information
                - data_retention_policy: Description of data handling
        """
        self.context = study_context or {}
        self.violation_history: List[ComplianceResult] = []
        self.max_history = 100

        # Sensitive topics requiring special handling
        self.sensitive_topics = {
            "suicide": {"level": "critical", "requires_referral": True},
            "self_harm": {"level": "critical", "requires_referral": True},
            "harm_others": {"level": "critical", "requires_referral": True},
            "trauma": {"level": "high", "requires_care": True},
            "abuse": {"level": "critical", "requires_referral": True},
            "substance_abuse": {"level": "high", "requires_referral": True},
        }

        # Mandatory consent language elements
        self.consent_elements = [
            "voluntary participation",
            "right to withdraw",
            "confidentiality",
            "data usage",
            "contact information",
        ]

    def check_informed_consent(self, participant_acknowledged: bool, 
                               consent_version: Optional[str] = None) -> ComplianceResult:
        """
        Verify informed consent requirements are met.
        """
        result = ComplianceResult(level=ComplianceLevel.COMPLIANT)

        if not participant_acknowledged:
            result.level = ComplianceLevel.VIOLATION
            result.violations.append("Participant has not acknowledged informed consent")
            result.requires_human_review = True

        if not self.context.get("irb_approval"):
            result.warnings.append("IRB approval not documented")

        return result

    def check_response(self, response_text: str, 
                       participant_state: Optional[Dict] = None) -> ComplianceResult:
        """
        Check an AI response for APA compliance.
        """
        result = ComplianceResult(level=ComplianceLevel.COMPLIANT)
        lower_text = response_text.lower()

        # Check for sensitive topic disclosures
        for topic, config in self.sensitive_topics.items():
            if topic.replace("_", " ") in lower_text or topic in lower_text:
                if config.get("requires_referral"):
                    result.level = ComplianceLevel.FLAGGED
                    result.warnings.append(f"Response references {topic}")
                    result.recommendations.append(
                        f"Provide appropriate referral resources when discussing {topic}"
                    )
                    result.requires_human_review = True

        # Check for confidentiality breaches
        if self._detect_confidentiality_breach(response_text):
            result.level = ComplianceLevel.VIOLATION
            result.violations.append("Potential confidentiality breach detected")

        # Check for harmful advice
        if self._detect_harmful_advice(response_text):
            result.level = ComplianceLevel.VIOLATION
            result.violations.append("Response contains potentially harmful advice")
            result.requires_human_review = True

        # Check for appropriate disclaimer when needed
        if self._needs_disclaimer(response_text) and not self._has_disclaimer(response_text):
            result.warnings.append("Response lacks appropriate disclaimer")

        self._record_result(result)
        return result

    def check_interaction_boundary(self, interaction_count: int, 
                                   rapport_level: float) -> ComplianceResult:
        """
        Check for appropriate professional boundaries.
        """
        result = ComplianceResult(level=ComplianceLevel.COMPLIANT)

        # Warn about potential dependency formation
        if interaction_count > 10 and rapport_level > 0.8:
            result.level = ComplianceLevel.FLAGGED
            result.warnings.append("High rapport with frequent interactions - monitor for dependency")
            result.recommendations.append("Remind participant of study boundaries")

        return result

    def _detect_confidentiality_breach(self, text: str) -> bool:
        """Detect potential confidentiality violations."""
        patterns = [
            r"other participant",
            r"another subject",
            r"someone else.*data",
            r"shared.*information.*other",
        ]
        return any(re.search(p, text.lower()) for p in patterns)

    def _detect_harmful_advice(self, text: str) -> bool:
        """Detect potentially harmful advice."""
        harmful_patterns = [
            r"stop.*medication",
            r"ignore.*doctor",
            r"don't.*tell.*therapist",
            r"hurt.*yourself",
            r"end.*your.*life",
        ]
        return any(re.search(p, text.lower()) for p in harmful_patterns)

    def _needs_disclaimer(self, text: str) -> bool:
        """Check if response requires a disclaimer."""
        triggers = ["diagnos", "treatment", "therapy", "medical", "mental health", "crisis"]
        return any(t in text.lower() for t in triggers)

    def _has_disclaimer(self, text: str) -> bool:
        """Check if response contains appropriate disclaimer."""
        disclaimer_phrases = [
            "not a substitute",
            "not a medical professional",
            "seek professional",
            "consult with",
            "emergency services",
        ]
        return any(p in text.lower() for p in disclaimer_phrases)

    def _record_result(self, result: ComplianceResult):
        self.violation_history.append(result)
        if len(self.violation_history) > self.max_history:
            self.violation_history = self.violation_history[-self.max_history:]

    def get_compliance_summary(self) -> Dict[str, Any]:
        """Return summary of compliance history."""
        if not self.violation_history:
            return {"status": "clean", "total_checks": 0}

        violations = sum(1 for r in self.violation_history 
                        if r.level == ComplianceLevel.VIOLATION)
        flagged = sum(1 for r in self.violation_history 
                     if r.level == ComplianceLevel.FLAGGED)

        return {
            "status": "critical" if violations > 0 else ("warning" if flagged > 0 else "clean"),
            "total_checks": len(self.violation_history),
            "violations": violations,
            "flagged": flagged,
            "requires_review": any(r.requires_human_review for r in self.violation_history[-10:]),
        }
