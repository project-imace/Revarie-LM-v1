"""
Integration test for the complete neuromodulation system.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from neuromodulation_controller import NeuromodulationController


def test_full_cycle_samara():
    """Test a complete emotional cycle for Samara."""
    nc = NeuromodulationController("samara")
    
    # Social interaction sequence
    nc.process_social_feedback(0.8, 0.7)  # Positive feedback
    nc.process_reward(0.6)                 # Task reward
    nc.process_novelty(0.3)                # Novel element
    
    state = nc.get_state()
    
    # Samara should maintain positive mood
    assert state.mood_valence > 0.0
    assert state.serotonin > 0.5


def test_full_cycle_artery():
    """Test a complete cognitive cycle for Artery."""
    nc = NeuromodulationController("artery")
    
    # Task-focused sequence
    nc.focus_attention(0.9)                # High focus
    nc.process_novelty(0.2)                # Minor novelty
    nc.process_reward(0.5)                 # Neutral reward
    
    state = nc.get_state()
    
    # Artery should have high attention, lower social mood
    assert state.attention_quality > 0.6
    assert state.acetylcholine > 0.5


def test_persona_differentiation():
    """Test that Samara and Artery have distinct neuromodulatory profiles."""
    samara = NeuromodulationController("samara")
    artery = NeuromodulationController("artery")
    
    samara_state = samara.get_state()
    artery_state = artery.get_state()
    
    # Samara should have higher serotonin and dopamine
    assert samara_state.serotonin > artery_state.serotonin
    assert samara_state.dopamine > artery_state.dopamine
    
    # Artery should have higher acetylcholine
    assert artery_state.acetylcholine > samara_state.acetylcholine


def test_cross_modulator_interactions():
    """Test that modulators influence each other."""
    nc = NeuromodulationController()
    
    # Artificially set high dopamine
    nc.dopamine = 0.9
    nc._apply_cross_modulator_effects()
    
    # Dopamine should excite norepinephrine
    assert nc.norepinephrine > 0.5


def test_tonic_regulation():
    """Test that system returns to baseline over time."""
    nc = NeuromodulationController()
    
    # Push all levels high
    nc.dopamine = 0.9
    nc.serotonin = 0.9
    nc.norepinephrine = 0.9
    nc.acetylcholine = 0.9
    
    # Apply tonic decay multiple times
    for _ in range(10):
        nc.update_tonic()
    
    # Should trend toward baselines
    assert nc.dopamine < 0.9
    assert nc.serotonin < 0.9


if __name__ == "__main__":
    test_full_cycle_samara()
    test_full_cycle_artery()
    test_persona_differentiation()
    test_cross_modulator_interactions()
    test_tonic_regulation()
    print("All neuromodulation system integration tests passed.")
