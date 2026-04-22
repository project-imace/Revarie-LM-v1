import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rapport_builder import RapportBuilder, RapportStage

def test_rapport_increases_with_positive_interaction():
    rb = RapportBuilder("samara")
    result = rb.process_interaction(
        "P001",
        "I really enjoy talking with you!",
        user_emotional_tone="positive",
        user_self_disclosure=0.4
    )
    assert result["rapport_level"] > 0.2

def test_samara_warmer_than_artery():
    samara = RapportBuilder("samara")
    artery = RapportBuilder("artery")
    
    samara_result = samara.process_interaction("P001", "Hello")
    artery_result = artery.process_interaction("P002", "Hello")
    
    assert samara.get_or_create_state("P001").trust > artery.get_or_create_state("P002").trust

def test_stage_progression():
    rb = RapportBuilder("samara")
    state = rb.get_or_create_state("P001")
    assert state.stage == RapportStage.INITIAL
    
    for _ in range(10):
        rb.process_interaction("P001", "Great conversation!", user_self_disclosure=0.5)
    
    assert rb.get_or_create_state("P001").stage != RapportStage.INITIAL
