import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from norepinephrine_analog import NorepinephrineAnalog

def test_hyperarousal_detection():
    ne = NorepinephrineAnalog()
    ne.level = 0.8
    assert ne.is_hyperaroused()

def test_hypoarousal_detection():
    ne = NorepinephrineAnalog()
    ne.level = 0.15
    assert ne.is_hypoaroused()

def test_uncertainty_increases_ne():
    ne = NorepinephrineAnalog()
    initial = ne.level
    ne.process_uncertainty(0.7)
    assert ne.level > initial
