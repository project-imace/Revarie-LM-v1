"""Unit tests for HeuristicResponder – works with hyphenated directory names."""

import sys
import os
import importlib.util

import pytest

# Dynamically load the module from its actual filesystem path
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "heuristic_responder.py")
)
spec = importlib.util.spec_from_file_location("heuristic_responder", module_path)
heuristic_responder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(heuristic_responder)

HeuristicResponder = heuristic_responder.HeuristicResponder
EmotionalTone = heuristic_responder.EmotionalTone
HeuristicRule = heuristic_responder.HeuristicRule


def test_default_rules_loaded():
    responder = HeuristicResponder()
    assert len(responder.rules) >= 6


def test_custom_rule():
    custom = HeuristicRule(
        pattern=r"\btest\b",
        emotional_tone=EmotionalTone.NEUTRAL,
        response_template="This is a test.",
    )
    responder = HeuristicResponder(rules=[custom])
    response = responder.respond("This is a test message.")
    assert response["text"] == "This is a test."


def test_priority_order():
    high = HeuristicRule(
        pattern=r"hello",
        emotional_tone=EmotionalTone.POSITIVE,
        response_template="High priority",
        priority=10,
    )
    low = HeuristicRule(
        pattern=r"hello",
        emotional_tone=EmotionalTone.POSITIVE,
        response_template="Low priority",
        priority=1,
    )
    responder = HeuristicResponder(rules=[low, high])
    response = responder.respond("hello")
    assert response["text"] == "High priority"


def test_no_match_returns_none():
    responder = HeuristicResponder()
    response = responder.respond("xyzabc")
    assert response["text"] is None
    assert response["confidence"] == 0.0
