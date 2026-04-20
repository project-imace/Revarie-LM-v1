"""
broadcast_selector.py
Global Workspace Theory – Broadcast selection mechanism.
Implements the competitive process by which specialized modules
(processors) vie for access to the global workspace.

Based on Baars (1988) and Dehaene's Conscious Workspace Model.
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import heapq


class ModuleType(Enum):
    """Types of specialized processors in the cognitive architecture."""
    SENSORY = "sensory"
    AFFECTIVE = "affective"
    REASONING = "reasoning"
    MEMORY = "memory"
    SOCIAL = "social"
    METACOGNITIVE = "metacognitive"


@dataclass
class BroadcastSignal:
    """A signal sent by a module competing for workspace access."""
    module_id: str
    module_type: ModuleType
    content: Any
    salience: float          # 0.0 to 1.0 – how important/urgent
    confidence: float        # 0.0 to 1.0 – how certain the module is
    novelty: float           # 0.0 to 1.0 – how new/unexpected
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_activation(self, weights: Dict[str, float]) -> float:
        """
        Compute the overall activation strength of this signal.
        Combines salience, confidence, and novelty using weighted sum.
        """
        w_salience = weights.get("salience", 0.4)
        w_confidence = weights.get("confidence", 0.3)
        w_novelty = weights.get("novelty", 0.3)

        # Recency bonus: newer signals get a slight boost.
        age = time.time() - self.timestamp
        recency_boost = max(0.0, 0.1 * (1.0 - min(age / 5.0, 1.0)))

        base = (w_salience * self.salience +
                w_confidence * self.confidence +
                w_novelty * self.novelty)
        return min(1.0, base + recency_boost)


class BroadcastSelector:
    """
    Selects which signal gains access to the global workspace.
    Implements the "fame in the brain" competition described by Dennett.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "salience": 0.4,
            "confidence": 0.3,
            "novelty": 0.3,
        }
        # Priority queue (max‑heap via negative activation)
        self._signal_queue: List[Tuple[float, int, BroadcastSignal]] = []
        self._counter = 0  # tie‑breaker for stable ordering
        self._history: List[BroadcastSignal] = []  # recent winners

    def submit_signal(self, signal: BroadcastSignal) -> None:
        """Submit a signal from a module for competition."""
        activation = signal.compute_activation(self.weights)
        # Use negative activation for max‑heap behavior.
        heapq.heappush(self._signal_queue, (-activation, self._counter, signal))
        self._counter += 1

    def select_winner(self) -> Optional[BroadcastSignal]:
        """
        Select the signal with highest activation to enter the workspace.
        Returns None if no signals are waiting.
        """
        if not self._signal_queue:
            return None

        neg_activation, _, signal = heapq.heappop(self._signal_queue)
        self._history.append(signal)
        # Keep history bounded.
        if len(self._history) > 100:
            self._history = self._history[-50:]

        return signal

    def peek_top_n(self, n: int = 3) -> List[BroadcastSignal]:
        """Return the top N signals without removing them."""
        if not self._signal_queue:
            return []

        # Copy the heap and extract top N.
        heap_copy = self._signal_queue[:]
        top_signals = []
        for _ in range(min(n, len(heap_copy))):
            neg_act, _, signal = heapq.heappop(heap_copy)
            top_signals.append(signal)
        return top_signals

    def clear(self) -> None:
        """Clear all pending signals."""
        self._signal_queue.clear()

    def get_recent_winners(self, n: int = 5) -> List[BroadcastSignal]:
        """Return the most recent winners."""
        return self._history[-n:]

    def has_pending(self) -> bool:
        """Return True if there are signals waiting."""
        return len(self._signal_queue) > 0


# =============================================================================
# Tests (pytest compatible)
# =============================================================================
def test_signal_activation():
    signal = BroadcastSignal(
        module_id="affective_1",
        module_type=ModuleType.AFFECTIVE,
        content="User appears distressed",
        salience=0.9,
        confidence=0.8,
        novelty=0.7,
        timestamp=time.time() - 10.0, # FIXED: Push past 5s window to nullify recency boost
    )
    weights = {"salience": 0.4, "confidence": 0.3, "novelty": 0.3}
    activation = signal.compute_activation(weights)
    expected = 0.4*0.9 + 0.3*0.8 + 0.3*0.7
    assert abs(activation - expected) < 0.01


def test_selector_winner():
    selector = BroadcastSelector()
    s1 = BroadcastSignal(
        module_id="low", module_type=ModuleType.REASONING,
        content="low", salience=0.3, confidence=0.5, novelty=0.2,
    )
    s2 = BroadcastSignal(
        module_id="high", module_type=ModuleType.AFFECTIVE,
        content="high", salience=0.9, confidence=0.9, novelty=0.8,
    )
    selector.submit_signal(s1)
    selector.submit_signal(s2)

    winner = selector.select_winner()
    assert winner is not None
    assert winner.module_id == "high"


def test_empty_selector():
    selector = BroadcastSelector()
    assert selector.select_winner() is None
    assert not selector.has_pending()


def test_peek_top_n():
    selector = BroadcastSelector()
    for i in range(5):
        signal = BroadcastSignal(
            module_id=f"mod_{i}",
            module_type=ModuleType.REASONING,
            content=f"content_{i}",
            salience=0.1 * i,
            confidence=0.5,
            novelty=0.3,
        )
        selector.submit_signal(signal)

    top = selector.peek_top_n(3)
    assert len(top) == 3
    # Should be the ones with highest salience (4, 3, 2)
    expected_ids = {"mod_4", "mod_3", "mod_2"}
    assert {s.module_id for s in top} == expected_ids
