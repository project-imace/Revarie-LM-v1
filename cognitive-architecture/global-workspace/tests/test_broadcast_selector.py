"""Unit tests for BroadcastSelector."""

import sys
import os
import importlib.util
import time

import pytest

# Dynamically load the module from its actual filesystem path (handles hyphens)
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "broadcast_selector.py")
)
spec = importlib.util.spec_from_file_location("broadcast_selector", module_path)
broadcast_selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(broadcast_selector)

BroadcastSelector = broadcast_selector.BroadcastSelector
BroadcastSignal = broadcast_selector.BroadcastSignal
ModuleType = broadcast_selector.ModuleType


def test_signal_creation():
    signal = BroadcastSignal(
        module_id="test_module",
        module_type=ModuleType.AFFECTIVE,
        content="Hello world",
        salience=0.8,
        confidence=0.9,
        novelty=0.5,
    )
    assert signal.module_id == "test_module"
    assert signal.salience == 0.8


def test_activation_computation():
    signal = BroadcastSignal(
        module_id="affective_1",
        module_type=ModuleType.AFFECTIVE,
        content="Distress",
        salience=0.9,
        confidence=0.8,
        novelty=0.7,
        timestamp=time.time() - 10.0, # FIXED: Nullify recency boost for accurate math check
    )
    weights = {"salience": 0.4, "confidence": 0.3, "novelty": 0.3}
    activation = signal.compute_activation(weights)
    expected = 0.4 * 0.9 + 0.3 * 0.8 + 0.3 * 0.7
    # Allow small float error
    assert abs(activation - expected) < 0.01


def test_selector_winner():
    selector = BroadcastSelector()
    s1 = BroadcastSignal(
        module_id="low",
        module_type=ModuleType.REASONING,
        content="low",
        salience=0.3,
        confidence=0.5,
        novelty=0.2,
    )
    s2 = BroadcastSignal(
        module_id="high",
        module_type=ModuleType.AFFECTIVE,
        content="high",
        salience=0.9,
        confidence=0.9,
        novelty=0.8,
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
    expected_ids = {"mod_4", "mod_3", "mod_2"}
    assert {s.module_id for s in top} == expected_ids


def test_clear_signals():
    selector = BroadcastSelector()
    selector.submit_signal(
        BroadcastSignal(
            module_id="test",
            module_type=ModuleType.REASONING,
            content="test",
            salience=0.5,
            confidence=0.5,
            novelty=0.5,
        )
    )
    assert selector.has_pending()
    selector.clear()
    assert not selector.has_pending()


def test_recent_winners():
    selector = BroadcastSelector()
    for i in range(3):
        selector.submit_signal(
            BroadcastSignal(
                module_id=f"mod_{i}",
                module_type=ModuleType.REASONING,
                content=f"content_{i}",
                salience=0.5,
                confidence=0.5,
                novelty=0.5,
            )
        )
    winner1 = selector.select_winner()
    winner2 = selector.select_winner()
    recent = selector.get_recent_winners(2)
    assert len(recent) == 2
    assert recent[0].module_id == winner1.module_id
    assert recent[1].module_id == winner2.module_id
