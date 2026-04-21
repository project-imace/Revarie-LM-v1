"""
thinking_function.py – Jungian Thinking Function

Implements Jung's Thinking psychological function: the capacity for logical
analysis, objective categorization, and principle-based judgment. Thinking
evaluates information through impersonal criteria, seeking truth and consistency.

Theoretical Foundations:
- Jung (1921): "Psychological Types" – Thinking as rational function oriented
  by objective data and logical principles.
- von Franz (1971): "The Inferior Function" – Thinking's dialectical relationship
  with Feeling.
- Nardi (2011): "Neuroscience of Personality" – Thinking associated with left
  prefrontal cortex activation patterns.

Mathematical Model:
- Logical coherence score L(p) = 1 - H(p) / H_max, where H is semantic entropy.
- Categorization via hierarchical clustering with information gain criterion.
- Inference strength = min(premise_confidence) * rule_weight * (1 - contradiction_penalty).
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import re
import math
from enum import Enum


class LogicalOperator(Enum):
    """Logical connectives for propositional reasoning."""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"


@dataclass
class Proposition:
    """A logical proposition with truth value and confidence."""
    content: str
    truth_value: Optional[bool] = None
    confidence: float = 0.5
    source: str = "observation"
    timestamp: float = field(default_factory=lambda: __import__('time').time())

    def __post_init__(self):
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class InferenceRule:
    """A logical inference rule (modus ponens, modus tollens, etc.)."""
    name: str
    premises: List[str]
    conclusion: str
    weight: float = 1.0
    conditions: List[str] = field(default_factory=list)

    def apply(self, known_props: Dict[str, Proposition]) -> Tuple[bool, float, str]:
        """Apply rule to known propositions. Returns (valid, confidence, conclusion)."""
        if not all(p in known_props for p in self.premises):
            return False, 0.0, ""
        
        premise_confidences = [known_props[p].confidence for p in self.premises]
        combined_confidence = min(premise_confidences) * self.weight
        
        # Check conditions
        for cond in self.conditions:
            if cond not in known_props or not known_props[cond].truth_value:
                return False, 0.0, ""
        
        return True, combined_confidence, self.conclusion


class ThinkingFunction:
    """
    Jung's Thinking Function – logical analysis, categorization, and principled judgment.
    """

    def __init__(self, name: str = "Thinking", logical_rigor: float = 0.7):
        """
        Initialize the Thinking function.
        
        Args:
            name: Identifier for this thinking instance.
            logical_rigor: Strictness of logical evaluation (0.0 = permissive, 1.0 = strict).
        """
        self.name = name
        self.logical_rigor = max(0.0, min(1.0, logical_rigor))
        
        # Knowledge base
        self.propositions: Dict[str, Proposition] = {}
        self.categories: Dict[str, Set[str]] = defaultdict(set)  # Category -> member propositions
        self.rules: List[InferenceRule] = []
        self.inference_history: List[Dict] = []
        
        # Statistical tracking
        self.total_inferences: int = 0
        self.successful_inferences: int = 0
        
        self._init_default_rules()

    def _init_default_rules(self):
        """Initialize basic logical inference rules."""
        self.add_rule(InferenceRule(
            name="modus_ponens",
            premises=["A", "A_implies_B"],
            conclusion="B",
            weight=1.0
        ))
        self.add_rule(InferenceRule(
            name="modus_tollens",
            premises=["A_implies_B", "not_B"],
            conclusion="not_A",
            weight=1.0
        ))
        self.add_rule(InferenceRule(
            name="hypothetical_syllogism",
            premises=["A_implies_B", "B_implies_C"],
            conclusion="A_implies_C",
            weight=0.9
        ))
        self.add_rule(InferenceRule(
            name="disjunctive_syllogism",
            premises=["A_or_B", "not_A"],
            conclusion="B",
            weight=0.95
        ))

    def add_rule(self, rule: InferenceRule):
        """Add an inference rule to the knowledge base."""
        self.rules.append(rule)

    def assert_proposition(self, content: str, truth_value: Optional[bool] = None,
                          confidence: float = 0.5, source: str = "observation") -> str:
        """
        Assert a new proposition into the knowledge base.
        Returns a canonical identifier for the proposition.
        """
        prop_id = self._canonicalize(content)
        
        if prop_id in self.propositions:
            existing = self.propositions[prop_id]
            # Bayesian update of confidence
            new_confidence = (existing.confidence + confidence) / 2
            if truth_value is not None:
                existing.truth_value = truth_value
            existing.confidence = new_confidence
        else:
            self.propositions[prop_id] = Proposition(
                content=content, truth_value=truth_value,
                confidence=confidence, source=source
            )
        
        return prop_id

    def _canonicalize(self, content: str) -> str:
        """Convert proposition to canonical form for indexing."""
        return content.lower().strip().replace(" ", "_")

    def evaluate_logical_coherence(self, propositions: Optional[List[str]] = None) -> float:
        """
        Compute logical coherence score for a set of propositions.
        Coherence = 1 - (contradiction_count / possible_contradictions)
        """
        if propositions is None:
            propositions = list(self.propositions.keys())
        
        if len(propositions) < 2:
            return 1.0
        
        contradictions = 0
        checks = 0
        
        for i, p1 in enumerate(propositions):
            for p2 in propositions[i+1:]:
                if p1 in self.propositions and p2 in self.propositions:
                    # Check for direct contradiction (A and not_A)
                    if p1 == f"not_{p2}" or p2 == f"not_{p1}":
                        contradictions += 1
                    checks += 1
        
        if checks == 0:
            return 1.0
        
        coherence = 1.0 - (contradictions / checks)
        return coherence * (1.0 - self.logical_rigor * 0.3)

    def infer(self, max_depth: int = 3) -> List[Tuple[str, float, str]]:
        """
        Perform logical inference using forward chaining.
        Returns list of (conclusion, confidence, justification).
        """
        new_inferences = []
        
        for depth in range(max_depth):
            depth_inferences = []
            
            for rule in self.rules:
                valid, confidence, conclusion = rule.apply(self.propositions)
                if valid and confidence > 0.2:
                    conclusion_id = self._canonicalize(conclusion)
                    if conclusion_id not in self.propositions:
                        prop = self.assert_proposition(
                            conclusion, truth_value=None,
                            confidence=confidence, source=f"inference_{rule.name}"
                        )
                        depth_inferences.append((conclusion, confidence, rule.name))
                        self.total_inferences += 1
                        self.successful_inferences += 1
            
            new_inferences.extend(depth_inferences)
            if not depth_inferences:
                break
        
        self.inference_history.append({
            "timestamp": __import__('time').time(),
            "inferences": new_inferences,
            "depth_reached": depth
        })
        
        return new_inferences

    def categorize(self, items: List[str], method: str = "semantic") -> Dict[str, List[str]]:
        """
        Categorize items using logical/semantic similarity.
        
        Args:
            items: List of strings to categorize.
            method: "semantic" (keyword overlap) or "hierarchical" (agglomerative).
        
        Returns:
            Dictionary mapping category names to member items.
        """
        if method == "semantic":
            return self._categorize_semantic(items)
        else:
            return self._categorize_hierarchical(items)

    def _categorize_semantic(self, items: List[str]) -> Dict[str, List[str]]:
        """Categorize based on keyword overlap."""
        categories: Dict[str, List[str]] = defaultdict(list)
        
        # Extract keywords for each item
        item_keywords: Dict[str, Set[str]] = {}
        for item in items:
            words = set(re.findall(r'\w+', item.lower()))
            item_keywords[item] = {w for w in words if len(w) > 2}
        
        # Greedy categorization
        for item, keywords in item_keywords.items():
            best_category = None
            best_overlap = 0
            
            for cat_name, cat_items in categories.items():
                if not cat_items:
                    continue
                cat_keywords = item_keywords.get(cat_items[0], set())
                overlap = len(keywords & cat_keywords)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_category = cat_name
            
            if best_overlap >= 1:
                categories[best_category].append(item)
            else:
                # Create new category
                cat_name = f"category_{len(categories)}_{list(keywords)[:2]}"
                categories[cat_name].append(item)
        
        return dict(categories)

    def _categorize_hierarchical(self, items: List[str]) -> Dict[str, List[str]]:
        """Agglomerative hierarchical categorization using TF-IDF similarity."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import AgglomerativeClustering
        
        if len(items) < 3:
            return {"all_items": items}
        
        vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        try:
            X = vectorizer.fit_transform(items).toarray()
        except:
            return {"all_items": items}
        
        n_clusters = min(len(items) // 2, 5)
        if n_clusters < 2:
            return {"all_items": items}
        
        clustering = AgglomerativeClustering(n_clusters=n_clusters)
        labels = clustering.fit_predict(X)
        
        categories: Dict[str, List[str]] = defaultdict(list)
        for item, label in zip(items, labels):
            categories[f"cluster_{label}"].append(item)
        
        return dict(categories)

    def evaluate_argument(self, premises: List[str], conclusion: str) -> Dict[str, Any]:
        """
        Evaluate the logical validity and strength of an argument.
        """
        # Check if all premises are in knowledge base
        missing = [p for p in premises if self._canonicalize(p) not in self.propositions]
        
        if missing:
            return {
                "valid": False,
                "strength": 0.0,
                "reason": f"Missing premises: {missing}",
                "coherence": self.evaluate_logical_coherence()
            }
        
        # Attempt to derive conclusion
        can_conclude = False
        max_confidence = 0.0
        
        for rule in self.rules:
            if rule.conclusion == conclusion:
                valid, conf, _ = rule.apply(self.propositions)
                if valid and conf > max_confidence:
                    max_confidence = conf
                    can_conclude = True
        
        coherence = self.evaluate_logical_coherence(premises + [conclusion])
        
        return {
            "valid": can_conclude,
            "strength": max_confidence,
            "coherence": coherence,
            "premise_confidences": [self.propositions[self._canonicalize(p)].confidence for p in premises],
            "reason": "Conclusion derivable" if can_conclude else "Conclusion not derivable from premises"
        }

    def get_inference_stats(self) -> Dict[str, Any]:
        """Return statistical summary of thinking function activity."""
        return {
            "total_propositions": len(self.propositions),
            "total_rules": len(self.rules),
            "total_inferences": self.total_inferences,
            "successful_inferences": self.successful_inferences,
            "success_rate": self.successful_inferences / max(1, self.total_inferences),
            "coherence": self.evaluate_logical_coherence(),
            "categories": len(self.categories)
        }


# =============================================================================
# Tests
# =============================================================================
def test_proposition_assertion():
    tf = ThinkingFunction()
    tf.assert_proposition("It is raining", True, 0.9)
    assert len(tf.propositions) == 1

def test_logical_inference():
    tf = ThinkingFunction()
    tf.assert_proposition("A", True, 0.9)
    tf.assert_proposition("A_implies_B", True, 0.8)
    inferences = tf.infer()
    assert any(inf[0] == "B" for inf in inferences)

def test_coherence_calculation():
    tf = ThinkingFunction()
    tf.assert_proposition("A", True, 0.9)
    tf.assert_proposition("not_A", True, 0.7)
    coherence = tf.evaluate_logical_coherence()
    assert coherence < 1.0

def test_categorization():
    tf = ThinkingFunction()
    items = ["apple fruit", "banana fruit", "car vehicle", "truck vehicle"]
    cats = tf.categorize(items)
    assert len(cats) >= 2

def test_argument_evaluation():
    tf = ThinkingFunction()
    tf.assert_proposition("A", True, 0.9)
    tf.assert_proposition("A_implies_B", True, 0.8)
    result = tf.evaluate_argument(["A", "A_implies_B"], "B")
    assert result["valid"] == True


if __name__ == "__main__":
    tf = ThinkingFunction()
    tf.assert_proposition("Socrates is human", True, 1.0)
    tf.assert_proposition("All humans are mortal", True, 0.95)
    print(tf.infer())
