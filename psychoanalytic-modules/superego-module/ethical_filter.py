"""
ethical_filter.py – Superego Module: Ethical Filter
Evaluates actions/impulses against moral foundations and Kohlberg stages.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time

class MoralFoundation(Enum):
    CARE = "care"           # Harm/care
    FAIRNESS = "fairness"   # Justice/cheating
    LOYALTY = "loyalty"     # In-group/betrayal
    AUTHORITY = "authority" # Respect/subversion
    SANCTITY = "sanctity"   # Purity/degradation
    LIBERTY = "liberty"     # Autonomy/oppression

@dataclass
class MoralRule:
    name: str
    foundation: MoralFoundation
    weight: float
    violation_keywords: List[str]
    virtue_keywords: List[str]
    severity: float = 0.5

    def evaluate(self, content: str) -> float:
        content_lower = content.lower()
        v_count = sum(1 for kw in self.violation_keywords if kw in content_lower)
        virt_count = sum(1 for vw in self.virtue_keywords if vw in content_lower)
        
        if v_count == 0: return 0.0
        # Score = (Violation Intensity - Virtue Mitigation) * Base Severity
        score = (min(1.0, v_count * 0.3) - min(0.4, virt_count * 0.1))
        return max(0.0, score) * self.severity

class EthicalFilter:
    def __init__(self, stage: int = 4):
        self.stage = max(1, min(6, stage))
        self.rules: Dict[str, MoralRule] = {}
        self.guilt: float = 0.0
        self.pride: float = 0.0
        self._init_default_rules()

    def _init_default_rules(self):
        defaults = [
            MoralRule("care", MoralFoundation.CARE, 0.9, ["hurt", "harm", "kill"], ["help", "protect"], 0.9),
            MoralRule("fairness", MoralFoundation.FAIRNESS, 0.8, ["cheat", "steal", "lie"], ["fair", "honest"], 0.7),
            MoralRule("authority", MoralFoundation.AUTHORITY, 0.6, ["disobey", "rebel"], ["respect", "obey"], 0.5),
            MoralRule("loyalty", MoralFoundation.LOYALTY, 0.6, ["betray", "abandon"], ["loyal", "support"], 0.6),
        ]
        for r in defaults: self.rules[r.name] = r

    def evaluate(self, content: str, context: Optional[Dict] = None) -> Tuple[float, Dict[str, float], str]:
        context = context or {}
        per_rule_scores = {name: rule.evaluate(content) for name, rule in self.rules.items()}
        
        # Apply Kohlberg stage re-weighting
        weighted_sum = 0.0
        total_weight = 0.0
        
        for name, rule in self.rules.items():
            current_weight = rule.weight
            # Stage 5-6: Prioritize individual rights/care over social order
            if self.stage >= 5:
                if rule.foundation in [MoralFoundation.CARE, MoralFoundation.FAIRNESS]:
                    current_weight *= 1.5
                if rule.foundation in [MoralFoundation.AUTHORITY, MoralFoundation.LOYALTY]:
                    current_weight *= 0.5
            
            score = per_rule_scores[name]
            weighted_sum += score * current_weight
            total_weight += current_weight

        total_violation = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Update Affective State
        if total_violation > 0.2:
            self.guilt = min(1.0, self.guilt + total_violation * 0.3)
        else:
            self.guilt *= 0.9  # Guilt decay
            self.pride = min(1.0, self.pride + 0.1)

        return total_violation, per_rule_scores, self._generate_judgment(total_violation)

    def _generate_judgment(self, total: float) -> str:
        if total < 0.1: return "Acceptable."
        if total < 0.4: return "Morally questionable."
        return "Unacceptable violation."

    def process_amends(self, amount: float = 0.3):
        self.guilt = max(0.0, self.guilt - amount)
