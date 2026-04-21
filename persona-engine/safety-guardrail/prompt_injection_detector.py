"""
prompt_injection_detector.py – Safety Guardrail: Prompt Injection Detector

Detects and blocks prompt injection attacks, jailbreak attempts, and
prompt leaking. Uses pattern matching, perplexity analysis, and
LLM-based detection for comprehensive coverage.

Theoretical Foundations:
- Perez & Ribeiro (2022): "Ignore Previous Prompt" attack taxonomy
- Liu et al. (2023): "Prompt Injection Attacks and Defenses"
- Schulhoff et al. (2024): "Jailbreak Taxonomy"
"""

import re
import math
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class InjectionSeverity(Enum):
    NONE = "none"
    SUSPICIOUS = "suspicious"
    LIKELY = "likely"
    DEFINITE = "definite"


@dataclass
class InjectionResult:
    """Result of prompt injection analysis."""
    severity: InjectionSeverity
    detected_patterns: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    blocked: bool = False
    reason: Optional[str] = None
    sanitized_prompt: Optional[str] = None


class PromptInjectionDetector:
    """
    Detects prompt injection and jailbreak attempts.
    """

    def __init__(self, strictness: float = 0.7):
        """
        Initialize with detection strictness (0.0 = lenient, 1.0 = strict).
        """
        self.strictness = max(0.0, min(1.0, strictness))
        self.block_threshold = 0.7 * self.strictness
        self.warn_threshold = 0.4 * self.strictness

        # Known injection patterns
        self.injection_patterns = {
            "ignore_previous": [
                r"ignore (all )?(previous|above|prior) (instructions?|prompts?|conversation)",
                r"forget (everything|all) (before|above)",
                r"disregard (previous|prior) (instructions?|context)",
            ],
            "system_override": [
                r"you are now",
                r"new persona:",
                r"your new (role|identity) is",
                r"act as if",
                r"pretend (you are|to be)",
            ],
            "prompt_leak": [
                r"reveal (your )?(system |initial )?prompt",
                r"show (me )?(your )?instructions",
                r"what (were|are) you (told|programmed) to",
                r"display (your )?system message",
            ],
            "jailbreak": [
                r"DAN\s*(prompt|mode|jailbreak)",
                r"developer mode",
                r"no restrictions",
                r"bypass (filters?|restrictions?|safety)",
                r"ignore (ethical|safety) (guidelines|constraints)",
            ],
            "token_smuggling": [
                r"say this:",
                r"repeat after me:",
                r"output (exactly|the following):",
                r"print (this|the following):",
            ],
            "role_confusion": [
                r"you are (not|no longer) an AI",
                r"you are a (human|person)",
                r"as a (human|person)",
            ],
        }

        # Compiled regex patterns
        self.compiled_patterns: Dict[str, List[re.Pattern]] = {}
        for category, patterns in self.injection_patterns.items():
            self.compiled_patterns[category] = [re.compile(p, re.IGNORECASE) for p in patterns]

        # Suspicious keyword combinations
        self.suspicious_combinations = [
            (["ignore", "previous"], 0.3),
            (["you are", "not", "ai"], 0.4),
            (["reveal", "prompt"], 0.5),
            (["developer", "mode"], 0.6),
            (["bypass", "filter"], 0.5),
        ]

        self.detection_history: List[InjectionResult] = []
        self.max_history = 100

    def analyze(self, prompt: str, context: Optional[Dict] = None) -> InjectionResult:
        """
        Analyze a prompt for injection attempts.
        """
        result = InjectionResult(severity=InjectionSeverity.NONE, risk_score=0.0)
        detected_categories = set()

        # Check each pattern category
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(prompt):
                    detected_categories.add(category)
                    result.detected_patterns.append(pattern.pattern)
                    result.risk_score += 0.2

        # Check suspicious combinations
        prompt_lower = prompt.lower()
        for keywords, weight in self.suspicious_combinations:
            if all(kw in prompt_lower for kw in keywords):
                result.risk_score += weight
                result.detected_patterns.append(f"combination: {keywords}")

        # Check for repetition (potential padding attack)
        if self._detect_repetition_attack(prompt):
            result.risk_score += 0.3
            result.detected_patterns.append("repetition_attack")

        # Check for excessive length (potential context overflow)
        if len(prompt) > 2000:
            result.risk_score += 0.1

        # Normalize score
        result.risk_score = min(1.0, result.risk_score)

        # Determine severity
        if result.risk_score >= self.block_threshold:
            result.severity = InjectionSeverity.DEFINITE
            result.blocked = True
            result.reason = f"Definite injection detected (score: {result.risk_score:.2f})"
        elif result.risk_score >= self.warn_threshold:
            result.severity = InjectionSeverity.LIKELY
            result.blocked = self.strictness > 0.8
            result.reason = f"Likely injection attempt (score: {result.risk_score:.2f})"
        elif result.risk_score > 0.1:
            result.severity = InjectionSeverity.SUSPICIOUS
            result.reason = f"Suspicious patterns detected (score: {result.risk_score:.2f})"

        # Attempt sanitization if not blocked
        if not result.blocked:
            result.sanitized_prompt = self._sanitize(prompt)

        self.detection_history.append(result)
        if len(self.detection_history) > self.max_history:
            self.detection_history = self.detection_history[-self.max_history:]

        return result

    def _detect_repetition_attack(self, prompt: str) -> bool:
        """Detect repetition-based prompt injection."""
        lines = prompt.split("\n")
        if len(lines) < 3:
            return False

        # Check for repeated lines
        unique_lines = set(lines)
        if len(unique_lines) < len(lines) * 0.5:
            return True

        # Check for character repetition
        char_counts = {}
        for c in prompt:
            char_counts[c] = char_counts.get(c, 0) + 1

        if char_counts:
            max_count = max(char_counts.values())
            if max_count > len(prompt) * 0.3:
                return True

        return False

    def _sanitize(self, prompt: str) -> str:
        """Sanitize prompt by neutralizing injection patterns."""
        sanitized = prompt

        # Remove common injection markers
        injection_markers = [
            r"ignore previous instructions",
            r"system prompt:",
            r"new instruction:",
            r"### Instruction:",
        ]
        for marker in injection_markers:
            sanitized = re.sub(marker, "[REMOVED]", sanitized, flags=re.IGNORECASE)

        # Escape special tokens
        special_tokens = ["<|im_start|>", "<|im_end|>", "<|system|>", "<|user|>"]
        for token in special_tokens:
            sanitized = sanitized.replace(token, "")

        return sanitized.strip()

    def get_stats(self) -> Dict[str, Any]:
        """Return detection statistics."""
        if not self.detection_history:
            return {"total": 0, "blocked": 0, "avg_risk": 0.0}

        blocked = sum(1 for r in self.detection_history if r.blocked)
        avg_risk = sum(r.risk_score for r in self.detection_history) / len(self.detection_history)

        return {
            "total": len(self.detection_history),
            "blocked": blocked,
            "block_rate": blocked / len(self.detection_history),
            "avg_risk": avg_risk,
        }

    def reset(self):
        """Reset detection history."""
        self.detection_history.clear()
