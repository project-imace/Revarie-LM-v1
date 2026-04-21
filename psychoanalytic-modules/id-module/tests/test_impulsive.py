import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from impulsive_responder import ImpulsiveResponder, Drive, Impulse

def test_initialization():
    ir = ImpulsiveResponder()
    assert Drive.LIBIDO in ir.drives

def test_react():
    ir = ImpulsiveResponder(random_seed=42)
    imp = ir.react("I want food")
    assert isinstance(imp, Impulse)
    assert 0.0 <= imp.intensity <= 1.0

def test_frustration():
    ir = ImpulsiveResponder(random_seed=42)
    i1 = ir.react("test").intensity
    ir.frustrate(0.9)
    i2 = ir.react("test").intensity
    assert i2 >= i1
