"""
heuristic_responder.py
System 1 – Fast, heuristic response generator.
Implements Kahneman's System 1 in Python: rapid, affect-driven, and associative.
This module complements the Rust pattern matcher with emotional and contextual heuristics.
"""

from typing import List, Dict, Optional, Tuple
import re
from dataclasses import dataclass, field
from enum import Enum


class EmotionalTone(Enum):
    """Basic emotional valence for heuristic responses."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    URGENT = "urgent"


@dataclass
class HeuristicRule:
    """A single heuristic rule for fast, intuitive responses."""
    pattern: str  # Regex pattern to match
    emotional_tone: EmotionalTone
    response_template: str
    confidence_boost: float = 0.7  # Base confidence for this heuristic
    priority: int = 1  # Higher priority rules are checked first


class HeuristicResponder:
    """
    A collection of fast, heuristic rules that generate System 1 responses.
    These rules operate before engaging slower, deliberate reasoning.
    """

    def __init__(self, rules: Optional[List[HeuristicRule]] = None):
        self.rules = rules or self._default_rules()
        # Sort rules by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    @staticmethod
    def _default_rules() -> List[HeuristicRule]:
        """Default set of psychologically grounded heuristic rules."""
        return [
            HeuristicRule(
                pattern=r"\b(hi|hello|hey|greetings)\b",
                emotional_tone=EmotionalTone.POSITIVE,
                response_template="Hello! It's good to hear from you.",
                priority=10,
            ),
            HeuristicRule(
                pattern=r"\b(help|urgent|emergency|stuck)\b",
                emotional_tone=EmotionalTone.URGENT,
                response_template="I'm here to help. Tell me what's wrong and I'll do my best.",
                priority=9,
            ),
            HeuristicRule(
                pattern=r"\b(sad|depressed|unhappy|lonely|heartbroken)\b",
                emotional_tone=EmotionalTone.NEGATIVE,
                response_template="I'm sorry you're feeling this way. I'm here to listen if you want to talk about it.",
                confidence_boost=0.8,
                priority=8,
            ),
            HeuristicRule(
                pattern=r"\b(happy|joy|excited|great|wonderful)\b",
                emotional_tone=EmotionalTone.POSITIVE,
                response_template="That's wonderful to hear! Tell me more about what's making you feel this way.",
                confidence_boost=0.8,
                priority=8,
            ),
            HeuristicRule(
                pattern=r"\b(thank|thanks|grateful|appreciate)\b",
                emotional_tone=EmotionalTone.POSITIVE,
                response_template="You're very welcome. I'm glad I could be of help.",
                priority=7,
            ),
            HeuristicRule(
                pattern=r"\?$",
                emotional_tone=EmotionalTone.NEUTRAL,
                response_template="That's an interesting question. Let me think about it.",
                confidence_boost=0.5,
                priority=5,
            ),
        ]

    def match(self, text: str) -> Tuple[Optional[HeuristicRule], float]:
        """
        Find the highest-priority rule that matches the input text.
        Returns the rule and a confidence score (0.0 to 1.0).
        """
        text_lower = text.lower()
        for rule in self.rules:
            if re.search(rule.pattern, text_lower):
                # Confidence is base boost, can be adjusted by context later
                return rule, rule.confidence_boost
        return None, 0.0

    def respond(self, text: str) -> Dict[str, object]:
        """
        Generate a System 1 response if a heuristic matches.
        Returns a dict with response text, confidence, and emotional tone.
        """
        rule, confidence = self.match(text)
        if rule:
            return {
                "text": rule.response_template,
                "confidence": confidence,
                "emotional_tone": rule.emotional_tone.value,
                "source": "heuristic",
            }
        return {
            "text": None,
            "confidence": 0.0,
            "emotional_tone": EmotionalTone.NEUTRAL.value,
            "source": "heuristic",
        }


# =============================================================================
# Tests (pytest compatible)
# =============================================================================
def test_heuristic_match_greeting():
    responder = HeuristicResponder()
    rule, conf = responder.match("Hello there!")
    assert rule is not None
    assert rule.emotional_tone == EmotionalTone.POSITIVE
    assert conf > 0.5


def test_heuristic_match_urgent():
    responder = HeuristicResponder()
    response = responder.respond("I need urgent help!")
    assert response["text"] is not None
    assert response["emotional_tone"] == "urgent"


def test_heuristic_no_match():
    responder = HeuristicResponder()
    rule, conf = responder.match("Blarg blarg blarg")
    assert rule is None
    assert conf == 0.0


if __name__ == "__main__":
    # Simple manual test
    responder = HeuristicResponder()
    for msg in ["Hello", "I'm so sad today", "What is the meaning of life?"]:
        print(f"Input: {msg}")
        print(f"Response: {responder.respond(msg)}")
        print()
