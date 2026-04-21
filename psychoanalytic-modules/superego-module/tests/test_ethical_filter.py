import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ethical_filter import EthicalFilter, MoralFoundation

def test_kohlberg_logic():
    # Stage 4 agent (Law and Order)
    ef4 = EthicalFilter(stage=4)
    # Stage 6 agent (Universal Principles)
    ef6 = EthicalFilter(stage=6)
    
    # Violation of authority
    violation = "I will disobey the rules"
    score4, _, _ = ef4.evaluate(violation)
    score6, _, _ = ef6.evaluate(violation)
    
    # In Stage 6, Authority violation weight is reduced
    assert score6 < score4

def test_guilt_and_amends():
    ef = EthicalFilter()
    ef.evaluate("I hurt my friend")
    assert ef.guilt > 0
    before = ef.guilt
    ef.process_amends(0.5)
    assert ef.guilt < before
