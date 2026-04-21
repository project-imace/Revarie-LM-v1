"""
test_tomnet_inference.py
Unit tests for ToMNet inference module.
"""

import sys
import os
import importlib.util
import pytest

# Dynamically load the module to handle directory naming conventions
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tomnet_inference.py"))
spec = importlib.util.spec_from_file_location("tomnet_inference", module_path)
tomnet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tomnet)

ToMNetInference = tomnet.ToMNetInference


def test_tomnet_initialization():
    infer = ToMNetInference()
    assert infer.model_path is None
    assert infer.session is None


def test_infer_goal_returns_dict():
    infer = ToMNetInference()
    # Test internal heuristic when session is None
    goals = infer.infer_goal(["goto_kitchen", "open_fridge"], {"time": "morning"})
    assert isinstance(goals, dict)
    assert "food" in goals


def test_load_model_handles_missing():
    # Verify that trying to load a non-existent file doesn't crash the system
    infer = ToMNetInference(model_path="nonexistent.onnx")
    infer.load_model()
    assert infer.session is None
