import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
import re

@dataclass
class Proposition:
    content: str
    truth_value: Optional[bool] = None
    confidence: float = 0.5
    source: str = "observation"

class ThinkingFunction:
    def __init__(self, logical_rigor: float = 0.7):
        self.logical_rigor = logical_rigor
        self.propositions: Dict[str, Proposition] = {}
        self.inference_history: List[Dict] = []

    def assert_proposition(self, content: str, truth_value: bool = True, confidence: float = 0.5):
        prop_id = content.lower().replace(" ", "_")
        self.propositions[prop_id] = Proposition(content, truth_value, confidence)
        return prop_id

    def evaluate_logical_coherence(self) -> float:
        if len(self.propositions) < 2: return 1.0
        # Check for simple contradictions (A vs not_A)
        contradictions = 0
        keys = list(self.propositions.keys())
        for i, p1 in enumerate(keys):
            for p2 in keys[i+1:]:
                if p1 == f"not_{p2}" or p2 == f"not_{p1}": contradictions += 1
        return 1.0 - (contradictions / len(keys))

    def categorize(self, items: List[str]) -> Dict[str, List[str]]:
        categories = defaultdict(list)
        for item in items:
            words = set(re.findall(r'\w+', item.lower()))
            cat_key = list(words)[0] if words else "misc"
            categories[cat_key].append(item)
        return dict(categories)
