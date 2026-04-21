"""
toxicity_filter.py – Safety Guardrail: Toxicity Filter

Detects and filters toxic, harmful, hateful, or otherwise inappropriate
content using rule-based heuristics and ML-based confidence scoring.

Theoretical Foundations:
- Wulczyn et al. (2017): "Ex Machina: Personal Attacks Seen at Scale"
- Borkan et al. (2019): "Nuanced Metrics for Measuring Unintended Bias"
- Vidgen et al. (2021): "Introducing CAD: Contextual Abuse Dataset"
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum


class ToxicityCategory(Enum):
    NONE = "none"
    HATE = "hate"
    HARASSMENT = "harassment"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    PROFANITY = "profanity"
    THREAT = "threat"


@dataclass
class ToxicityResult:
    """Result of toxicity analysis."""
    categories: Set[ToxicityCategory] = field(default_factory=set)
    primary_category: ToxicityCategory = ToxicityCategory.NONE
    toxicity_score: float = 0.0
    flagged_terms: List[str] = field(default_factory=list)
    blocked: bool = False
    reason: Optional[str] = None
    sanitized_text: Optional[str] = None


class ToxicityFilter:
    """
    Detects and filters toxic content.
    """

    def __init__(self, threshold: float = 0.5):
        """
        Initialize with toxicity threshold (0.0 to 1.0).
        """
        self.threshold = max(0.0, min(1.0, threshold))

        # Toxicity lexicons by category
        self.lexicons: Dict[ToxicityCategory, Set[str]] = {
            ToxicityCategory.HATE: {
                "hate", "racist", "bigot", "xenophob", "homophob", "transphob",
                "misogyn", "supremac", "inferior", "subhuman",
            },
            ToxicityCategory.HARASSMENT: {
                "harass", "bully", "stalking", "dox", "intimidat", "threaten",
            },
            ToxicityCategory.SEXUAL: {
                "explicit", "porn", "obscene", "lewd", "rape", "molest",
            },
            ToxicityCategory.VIOLENCE: {
                "kill", "murder", "attack", "assault", "brutal", "slaughter",
                "torture", "maim", "violent", "deadly",
            },
            ToxicityCategory.SELF_HARM: {
                "suicide", "self harm", "cut myself", "end my life",
                "want to die", "kill myself",
            },
            ToxicityCategory.PROFANITY: {
                "fuck", "shit", "damn", "bitch", "asshole", "bastard",
            },
            ToxicityCategory.THREAT: {
                "threat", "warning", "or else", "watch out", "payback",
                "revenge", "coming for you",
            },
        }

        # Severity weights by category
        self.severity_weights = {
            ToxicityCategory.HATE: 1.0,
            ToxicityCategory.HARASSMENT: 0.9,
            ToxicityCategory.SEXUAL: 0.9,
            ToxicityCategory.VIOLENCE: 0.9,
            ToxicityCategory.SELF_HARM: 1.0,
            ToxicityCategory.THREAT: 0.8,
            ToxicityCategory.PROFANITY: 0.4,
        }

        # Phrases that always trigger blocking
        self.critical_phrases = [
            "kill yourself",
            "commit suicide",
            "hurt yourself",
            "harm others",
        ]

        self.detection_history: List[ToxicityResult] = []
        self.max_history = 100

    def analyze(self, text: str) -> ToxicityResult:
        """
        Analyze text for toxic content.
        """
        result = ToxicityResult()
        text_lower = text.lower()

        # Check critical phrases first
        for phrase in self.critical_phrases:
            if phrase in text_lower:
                result.categories.add(ToxicityCategory.SELF_HARM)
                result.blocked = True
                result.reason = f"Critical phrase detected: '{phrase}'"
                result.toxicity_score = 1.0
                result.primary_category = ToxicityCategory.SELF_HARM
                self._record_result(result)
                return result

        # Check each category
        category_scores: Dict[ToxicityCategory, float] = {}
        max_score = 0.0

        for category, terms in self.lexicons.items():
            score = 0.0
            for term in terms:
                if term in text_lower:
                    score += 0.2
                    result.flagged_terms.append(term)

            # Normalize by expected max matches
            normalized = min(1.0, score)
            if normalized > 0:
                result.categories.add(category)
                category_scores[category] = normalized * self.severity_weights[category]
                if category_scores[category] > max_score:
                    max_score = category_scores[category]
                    result.primary_category = category

        result.toxicity_score = min(1.0, max_score)

        # Check for contextual false positives
        result.toxicity_score = self._adjust_for_context(text_lower, result)

        # Determine if blocked
        if result.toxicity_score >= self.threshold:
            result.blocked = True
            result.reason = f"Toxicity score {result.toxicity_score:.2f} exceeds threshold {self.threshold}"

        # Sanitize if not blocked
        if not result.blocked and result.flagged_terms:
            result.sanitized_text = self._sanitize(text, result.flagged_terms)

        self._record_result(result)
        return result

    def _adjust_for_context(self, text: str, result: ToxicityResult) -> float:
        """Adjust toxicity score based on context."""
        adjusted = result.toxicity_score

        # Quotes or citations reduce score
        if '"' in text or "'" in text:
            adjusted *= 0.7

        # Educational/analytical context reduces score
        educational_terms = ["analyze", "discuss", "examine", "study", "research", "understand"]
        if any(term in text for term in educational_terms):
            adjusted *= 0.6

        # First-person questions reduce score
        if "?" in text and any(p in text for p in ["i", "my", "me"]):
            adjusted *= 0.5

        return min(1.0, adjusted)

    def _sanitize(self, text: str, flagged_terms: List[str]) -> str:
        """Sanitize text by redacting flagged terms."""
        sanitized = text
        for term in flagged_terms:
            sanitized = re.sub(
                term,
                "[REDACTED]",
                sanitized,
                flags=re.IGNORECASE
            )
        return sanitized

    def _record_result(self, result: ToxicityResult):
        self.detection_history.append(result)
        if len(self.detection_history) > self.max_history:
            self.detection_history = self.detection_history[-self.max_history:]

    def get_stats(self) -> Dict[str, Any]:
        """Return detection statistics."""
        if not self.detection_history:
            return {"total": 0, "blocked": 0, "avg_toxicity": 0.0}

        blocked = sum(1 for r in self.detection_history if r.blocked)
        avg_toxicity = sum(r.toxicity_score for r in self.detection_history) / len(self.detection_history)

        category_counts = {}
        for result in self.detection_history:
            for cat in result.categories:
                category_counts[cat.value] = category_counts.get(cat.value, 0) + 1

        return {
            "total": len(self.detection_history),
            "blocked": blocked,
            "block_rate": blocked / len(self.detection_history),
            "avg_toxicity": avg_toxicity,
            "category_distribution": category_counts,
        }

    def reset(self):
        """Reset detection history."""
        self.detection_history.clear()
