"""
test_habit_strengthener.py
Unit tests for Habit Strengthener.
"""

import sys
import os
import importlib.util
import time

import pytest

module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "habit_strengthener.py"))
spec = importlib.util.spec_from_file_location("habit_strengthener", module_path)
hs_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hs_module)

HabitStrengthener = hs_module.HabitStrengthener
Habit = hs_module.Habit


def test_habit_creation():
    hs = HabitStrengthener()
    habit = hs.get_or_create("morning", "stretch")
    assert habit.cue == "morning"
    assert habit.response == "stretch"
    assert habit.strength == 0.1


def test_strengthen_increases_strength():
    hs = HabitStrengthener()
    initial = hs.get_strength("morning", "stretch")
    for _ in range(5):
        hs.strengthen("morning", "stretch")
    assert hs.get_strength("morning", "stretch") > initial


def test_automation_threshold():
    hs = HabitStrengthener(automation_threshold=0.3)
    for _ in range(10):
        hs.strengthen("cue", "response")
    assert hs.is_automated("cue", "response")


def test_predict_response():
    hs = HabitStrengthener()
    hs.strengthen("greeting", "Hello!")
    hs.strengthen("greeting", "Hi there")
    for _ in range(3):
        hs.strengthen("greeting", "Hello!")
    response, confidence = hs.predict_response("greeting")
    assert response == "Hello!"
    assert confidence > 0.0


def test_predict_response_no_habit():
    hs = HabitStrengthener()
    result = hs.predict_response("unknown")
    assert result is None


def test_decay():
    hs = HabitStrengthener(decay_rate=0.5)
    hs.strengthen("cue", "response")
    initial = hs.get_strength("cue", "response")
    habit = hs.habits["cue->response"]
    habit.last_performed = time.time() - 10 * 86400
    hs.apply_decay()
    assert hs.get_strength("cue", "response") < initial


def test_context_modulation():
    hs = HabitStrengthener()
    hs.strengthen("cue", "response1", context={"location": 1.0})
    hs.strengthen("cue", "response2", context={"location": -1.0})
    response, _ = hs.predict_response("cue", context={"location": 1.0})
    assert response == "response1"


def test_get_automated_habits():
    hs = HabitStrengthener(automation_threshold=0.3)
    hs.strengthen("cue1", "resp1")
    for _ in range(10):
        hs.strengthen("cue2", "resp2")
    automated = hs.get_automated_habits()
    assert len(automated) == 1
    assert automated[0].response == "resp2"


def test_reset():
    hs = HabitStrengthener()
    hs.strengthen("cue", "response")
    assert len(hs.habits) == 1
    hs.reset()
    assert len(hs.habits) == 0
    assert len(hs.history) == 0
