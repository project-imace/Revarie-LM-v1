"""
test_working_memory_model.py
Integration test for Baddeley's Working Memory Model.
Simulates the complete multicomponent system: phonological loop,
visuospatial sketchpad, episodic buffer, and central executive.
"""

import sys
import os
import importlib.util
import time
import threading
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# -----------------------------------------------------------------------------
# Mock Rust FFI bindings (simulated for Python integration testing)
# -----------------------------------------------------------------------------

class Modality(Enum):
    ICONIC = "iconic"
    ECHOIC = "echoic"
    HAPTIC = "haptic"


class AttentionFocus(Enum):
    NONE = "none"
    PHONOLOGICAL = "phonological"
    VISUOSPATIAL = "visuospatial"
    EPISODIC = "episodic"
    DIVIDED = "divided"


@dataclass
class PhonologicalItem:
    content: str
    syllables: int


@dataclass
class VisualObject:
    id: str
    location: Tuple[float, float]
    color: Optional[str] = None
    shape: Optional[str] = None


@dataclass
class EpisodicChunk:
    id: str
    verbal_content: Optional[List[str]] = None
    visual_content: Optional[List[str]] = None
    emotional_valence: float = 0.0
    activation: float = 1.0


class MockPhonologicalLoop:
    """Mock of Rust PhonologicalLoop."""
    def __init__(self, syllable_capacity: int = 8, decay_ms: int = 2000):
        self.items: List[PhonologicalItem] = []
        self.syllable_capacity = syllable_capacity
        self.decay_ms = decay_ms
        self.current_syllables = 0

    def insert(self, content: str, syllables: int) -> bool:
        if self.current_syllables + syllables > self.syllable_capacity:
            return False
        self.items.append(PhonologicalItem(content, syllables))
        self.current_syllables += syllables
        return True

    def recall(self) -> List[str]:
        return [item.content for item in self.items]

    def rehearse(self):
        pass  # Simulated

    def clear(self):
        self.items.clear()
        self.current_syllables = 0


class MockVisuospatialSketchpad:
    """Mock of Rust VisuospatialSketchpad."""
    def __init__(self, capacity: int = 4):
        self.objects: List[VisualObject] = []
        self.locations: List[Tuple[float, float]] = []
        self.capacity = capacity

    def insert_object(self, obj: VisualObject) -> bool:
        if len(self.objects) >= self.capacity:
            self.objects.pop(0)
        self.objects.append(obj)
        return True

    def insert_location(self, loc: Tuple[float, float]):
        if len(self.locations) >= self.capacity:
            self.locations.pop(0)
        self.locations.append(loc)

    def recall_objects(self) -> List[VisualObject]:
        return self.objects.copy()

    def recall_locations(self) -> List[Tuple[float, float]]:
        return self.locations.copy()

    def clear(self):
        self.objects.clear()
        self.locations.clear()


class MockEpisodicBuffer:
    """Mock of Rust EpisodicBuffer."""
    def __init__(self, capacity: int = 4):
        self.chunks: List[EpisodicChunk] = []
        self.capacity = capacity

    def bind(self, chunk: EpisodicChunk):
        if len(self.chunks) >= self.capacity:
            self.chunks.pop(0)
        self.chunks.append(chunk)

    def recall(self) -> List[EpisodicChunk]:
        return self.chunks.copy()

    def attend_to(self, chunk_id: str) -> bool:
        for chunk in self.chunks:
            if chunk.id == chunk_id:
                chunk.activation = min(chunk.activation + 0.3, 2.0)
                return True
        return False

    def clear(self):
        self.chunks.clear()


class MockCentralExecutive:
    """Mock of C++ CentralExecutive."""
    def __init__(self):
        self.focus = AttentionFocus.NONE
        self.inhibited: List[str] = []
        self.switch_cost = 0.0

    def focus_on(self, focus: AttentionFocus):
        if self.focus != focus:
            self.switch_cost += 0.1
            self.focus = focus

    def inhibit(self, item_id: str) -> bool:
        if item_id not in self.inhibited:
            self.inhibited.append(item_id)
            return True
        return False

    def is_inhibited(self, item_id: str) -> bool:
        return item_id in self.inhibited

    def release_inhibition(self, item_id: str):
        if item_id in self.inhibited:
            self.inhibited.remove(item_id)

    def current_focus(self) -> AttentionFocus:
        return self.focus


# -----------------------------------------------------------------------------
# Working Memory System (integration of all components)
# -----------------------------------------------------------------------------

class WorkingMemorySystem:
    """Complete Baddeley working memory model."""

    def __init__(self):
        self.phonological_loop = MockPhonologicalLoop()
        self.visuospatial = MockVisuospatialSketchpad()
        self.episodic_buffer = MockEpisodicBuffer()
        self.central_executive = MockCentralExecutive()

    def encode_verbal(self, words: List[Tuple[str, int]]) -> int:
        """Encode verbal information into phonological loop."""
        self.central_executive.focus_on(AttentionFocus.PHONOLOGICAL)
        encoded = 0
        for word, syllables in words:
            if self.phonological_loop.insert(word, syllables):
                encoded += 1
        return encoded

    def encode_visual(self, objects: List[VisualObject]) -> int:
        """Encode visual objects into visuospatial sketchpad."""
        self.central_executive.focus_on(AttentionFocus.VISUOSPATIAL)
        encoded = 0
        for obj in objects:
            if self.visuospatial.insert_object(obj):
                encoded += 1
        return encoded

    def encode_locations(self, locations: List[Tuple[float, float]]):
        """Encode spatial locations."""
        self.central_executive.focus_on(AttentionFocus.VISUOSPATIAL)
        for loc in locations:
            self.visuospatial.insert_location(loc)

    def bind_episode(self, chunk_id: str, verbal: List[str], visual: List[str]) -> bool:
        """Bind information from subsystems into episodic buffer."""
        self.central_executive.focus_on(AttentionFocus.EPISODIC)
        chunk = EpisodicChunk(
            id=chunk_id,
            verbal_content=verbal,
            visual_content=visual
        )
        self.episodic_buffer.bind(chunk)
        return True

    def recall_verbal(self) -> List[str]:
        """Recall verbal information from phonological loop."""
        self.central_executive.focus_on(AttentionFocus.PHONOLOGICAL)
        return self.phonological_loop.recall()

    def recall_visual(self) -> List[VisualObject]:
        """Recall visual objects from visuospatial sketchpad."""
        self.central_executive.focus_on(AttentionFocus.VISUOSPATIAL)
        return self.visuospatial.recall_objects()

    def recall_episode(self, chunk_id: Optional[str] = None) -> List[EpisodicChunk]:
        """Recall episodic chunks."""
        self.central_executive.focus_on(AttentionFocus.EPISODIC)
        chunks = self.episodic_buffer.recall()
        if chunk_id:
            return [c for c in chunks if c.id == chunk_id]
        return chunks

    def inhibit_distractor(self, distractor_id: str) -> bool:
        """Inhibit distracting information."""
        return self.central_executive.inhibit(distractor_id)

    def reset(self):
        """Clear all memory stores."""
        self.phonological_loop.clear()
        self.visuospatial.clear()
        self.episodic_buffer.clear()
        self.central_executive = MockCentralExecutive()


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_verbal_encoding_recall():
    wm = WorkingMemorySystem()
    words = [("apple", 2), ("banana", 3), ("cat", 1)]
    encoded = wm.encode_verbal(words)
    assert encoded == 3
    recalled = wm.recall_verbal()
    assert recalled == ["apple", "banana", "cat"]
    print("[PASS] test_verbal_encoding_recall")


def test_visual_encoding_recall():
    wm = WorkingMemorySystem()
    obj1 = VisualObject("obj1", (0.2, 0.3), "red", "circle")
    obj2 = VisualObject("obj2", (0.8, 0.7), "blue", "square")
    encoded = wm.encode_visual([obj1, obj2])
    assert encoded == 2
    recalled = wm.recall_visual()
    assert len(recalled) == 2
    assert recalled[0].color == "red"
    print("[PASS] test_visual_encoding_recall")


def test_spatial_location_encoding():
    wm = WorkingMemorySystem()
    locations = [(0.1, 0.9), (0.5, 0.5), (0.9, 0.1)]
    wm.encode_locations(locations)
    recalled = wm.visuospatial.recall_locations()
    assert recalled == locations
    print("[PASS] test_spatial_location_encoding")


def test_episodic_binding():
    wm = WorkingMemorySystem()
    wm.encode_verbal([("hello", 2), ("world", 1)])
    wm.encode_visual([VisualObject("obj1", (0.5, 0.5), "green", "triangle")])
    wm.bind_episode("ep1", ["hello", "world"], ["obj1"])
    chunks = wm.recall_episode("ep1")
    assert len(chunks) == 1
    assert chunks[0].verbal_content == ["hello", "world"]
    assert chunks[0].visual_content == ["obj1"]
    print("[PASS] test_episodic_binding")


def test_attention_switching():
    wm = WorkingMemorySystem()
    assert wm.central_executive.switch_cost == 0.0
    wm.encode_verbal([("test", 1)])
    assert wm.central_executive.current_focus() == AttentionFocus.PHONOLOGICAL
    cost1 = wm.central_executive.switch_cost
    wm.encode_visual([VisualObject("obj", (0.0, 0.0))])
    assert wm.central_executive.current_focus() == AttentionFocus.VISUOSPATIAL
    cost2 = wm.central_executive.switch_cost
    assert cost2 > cost1
    print("[PASS] test_attention_switching")


def test_inhibition():
    wm = WorkingMemorySystem()
    assert not wm.central_executive.is_inhibited("noise")
    wm.inhibit_distractor("noise")
    assert wm.central_executive.is_inhibited("noise")
    wm.central_executive.release_inhibition("noise")
    assert not wm.central_executive.is_inhibited("noise")
    print("[PASS] test_inhibition")


def test_capacity_limits():
    wm = WorkingMemorySystem()
    wm.phonological_loop.syllable_capacity = 4
    words = [("long", 1), ("word", 1), ("list", 1), ("full", 1), ("extra", 1)]
    encoded = wm.encode_verbal(words)
    assert encoded == 4  # Fifth word rejected
    print("[PASS] test_capacity_limits")


def test_clear_resets_all():
    wm = WorkingMemorySystem()
    wm.encode_verbal([("test", 1)])
    wm.encode_visual([VisualObject("obj", (0.0, 0.0))])
    wm.bind_episode("ep", ["test"], ["obj"])
    assert len(wm.recall_verbal()) == 1
    assert len(wm.recall_visual()) == 1
    assert len(wm.recall_episode()) == 1
    wm.reset()
    assert len(wm.recall_verbal()) == 0
    assert len(wm.recall_visual()) == 0
    assert len(wm.recall_episode()) == 0
    print("[PASS] test_clear_resets_all")


if __name__ == "__main__":
    test_verbal_encoding_recall()
    test_visual_encoding_recall()
    test_spatial_location_encoding()
    test_episodic_binding()
    test_attention_switching()
    test_inhibition()
    test_capacity_limits()
    test_clear_resets_all()
    print("\nAll Working Memory integration tests passed.")
