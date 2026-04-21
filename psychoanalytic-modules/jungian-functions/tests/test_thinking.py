import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from thinking_function import ThinkingFunction, InferenceRule

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
