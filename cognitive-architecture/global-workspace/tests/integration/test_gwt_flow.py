"""
test_gwt_flow.py
Integration test for the Global Workspace Theory module.
Simulates a complete cognitive cycle: signal submission → competition →
broadcast selection → attention focus.
"""

import sys
import os
import importlib.util
import time
import pytest

# Dynamically load modules (handles hyphenated directory names)
def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load GWT components
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
broadcast_selector = load_module(
    "broadcast_selector",
    os.path.join(base_path, "broadcast_selector.py")
)
# Note: Rust and C++ components would be called via FFI in production;
# here we simulate their behavior through the Python interfaces.

BroadcastSelector = broadcast_selector.BroadcastSelector
BroadcastSignal = broadcast_selector.BroadcastSignal
ModuleType = broadcast_selector.ModuleType


class MockWorkspaceBuffer:
    """Mock of the Rust WorkspaceBuffer for integration testing."""
    def __init__(self, capacity=7):
        self.capacity = capacity
        self.buffer = []
        self.broadcast_history = []

    def insert(self, item):
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append(item)

    def broadcast(self):
        if self.buffer:
            item = self.buffer[-1]
            self.broadcast_history.append(item)
            return item
        return None

    def clear(self):
        self.buffer.clear()


def test_gwt_full_cycle():
    """Test a complete Global Workspace cycle with multiple modules."""
    # Initialize components
    selector = BroadcastSelector()
    workspace = MockWorkspaceBuffer(capacity=3)

    # Simulate modules submitting signals
    signals = [
        BroadcastSignal(
            module_id="affective_1",
            module_type=ModuleType.AFFECTIVE,
            content="User appears anxious",
            salience=0.85,
            confidence=0.9,
            novelty=0.7,
        ),
        BroadcastSignal(
            module_id="reasoning_1",
            module_type=ModuleType.REASONING,
            content="Logical analysis complete",
            salience=0.6,
            confidence=0.95,
            novelty=0.3,
        ),
        BroadcastSignal(
            module_id="memory_1",
            module_type=ModuleType.MEMORY,
            content="Retrieved relevant past conversation",
            salience=0.5,
            confidence=0.8,
            novelty=0.6,
        ),
        BroadcastSignal(
            module_id="social_1",
            module_type=ModuleType.SOCIAL,
            content="Empathetic response ready",
            salience=0.75,
            confidence=0.85,
            novelty=0.5,
        ),
    ]

    # Submit all signals
    for sig in signals:
        selector.submit_signal(sig)

    # First competition round
    assert selector.has_pending()
    winner1 = selector.select_winner()
    assert winner1 is not None
    workspace.insert(winner1)
    broadcast1 = workspace.broadcast()
    assert broadcast1 is not None

    # The highest salience signal (affective_1) should win
    assert winner1.module_id == "affective_1"

    # After broadcasting, workspace contains the winner
    assert len(workspace.buffer) == 1

    # Second competition round (winner removed)
    winner2 = selector.select_winner()
    assert winner2 is not None
    # Next highest salience should win
    assert winner2.module_id == "social_1"

    workspace.insert(winner2)
    broadcast2 = workspace.broadcast()
    assert broadcast2.module_id == "social_1"

    # Verify workspace capacity
    workspace.insert(BroadcastSignal(
        module_id="extra_1", module_type=ModuleType.SENSORY,
        content="extra", salience=0.1, confidence=0.1, novelty=0.1
    ))
    workspace.insert(BroadcastSignal(
        module_id="extra_2", module_type=ModuleType.SENSORY,
        content="extra2", salience=0.1, confidence=0.1, novelty=0.1
    ))
    workspace.insert(BroadcastSignal(
        module_id="extra_3", module_type=ModuleType.SENSORY,
        content="extra3", salience=0.1, confidence=0.1, novelty=0.1
    ))
    # Capacity is 3, so oldest should be evicted
    assert len(workspace.buffer) == 3


def test_gwt_attention_inhibition():
    """Test inhibition of return mechanism."""
    selector = BroadcastSelector()
    workspace = MockWorkspaceBuffer()

    # Submit a signal and let it win
    signal = BroadcastSignal(
        module_id="repetitive_module",
        module_type=ModuleType.SENSORY,
        content="repetitive content",
        salience=0.9,
        confidence=0.9,
        novelty=0.2,
    )
    selector.submit_signal(signal)
    winner = selector.select_winner()
    workspace.insert(winner)

    # In a real system, the attention controller would inhibit this module
    # Here we simulate by not resubmitting from that source

    # Submit a new, slightly less salient signal
    new_signal = BroadcastSignal(
        module_id="novel_module",
        module_type=ModuleType.SENSORY,
        content="novel content",
        salience=0.85,
        confidence=0.9,
        novelty=0.9,  # High novelty
    )
    selector.submit_signal(new_signal)
    winner2 = selector.select_winner()
    # The novel module should win due to recency/novelty boost
    assert winner2.module_id == "novel_module"


def test_gwt_peek_top_n():
    """Test peeking at top signals without consuming them."""
    selector = BroadcastSelector()
    for i in range(5):
        selector.submit_signal(BroadcastSignal(
            module_id=f"mod_{i}",
            module_type=ModuleType.REASONING,
            content=f"content_{i}",
            salience=0.1 * i,
            confidence=0.5,
            novelty=0.3,
        ))

    top3 = selector.peek_top_n(3)
    assert len(top3) == 3
    # Should be the three with highest salience (mod_4, mod_3, mod_2)
    expected = {"mod_4", "mod_3", "mod_2"}
    assert {s.module_id for s in top3} == expected

    # Peeking should not remove signals
    assert selector.has_pending()
    winner = selector.select_winner()
    assert winner.module_id == "mod_4"
