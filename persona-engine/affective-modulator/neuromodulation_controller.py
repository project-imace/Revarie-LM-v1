"""
neuromodulation_controller.py – Unified Neuromodulatory System

Orchestrates all four neuromodulatory analogs (dopamine, serotonin,
norepinephrine, acetylcholine) into a coherent affective system.
Provides integrated state and coordinates cross-modulator interactions.

Theoretical Foundations:
- Larue et al. (2013): Neuromodulatory emotions in cognitive architectures.
- Fellous (2004): From human emotions to robot emotions.
- Dayan (2012): Twenty-five lessons from computational neuromodulation.
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import time
import json

# Note: In production, these would import the actual Rust/C++ bindings.
# For now, we define Python analogs that mirror the behavior.


@dataclass
class NeuromodulationState:
    """Complete state of the neuromodulatory system."""
    dopamine: float
    serotonin: float
    norepinephrine: float
    acetylcholine: float
    
    motivation: float
    patience: float
    arousal: float
    attention_quality: float
    
    mood_valence: float
    stress_level: float
    learning_rate_mod: float
    
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dopamine": self.dopamine,
            "serotonin": self.serotonin,
            "norepinephrine": self.norepinephrine,
            "acetylcholine": self.acetylcholine,
            "motivation": self.motivation,
            "patience": self.patience,
            "arousal": self.arousal,
            "attention_quality": self.attention_quality,
            "mood_valence": self.mood_valence,
            "stress_level": self.stress_level,
            "learning_rate_mod": self.learning_rate_mod,
            "timestamp": self.timestamp
        }


class NeuromodulationController:
    """
    Unified controller for all neuromodulatory systems.
    Manages cross-modulator interactions and provides integrated state.
    """

    def __init__(self, persona: str = "samara"):
        """
        Initialize with persona-specific baseline parameters.
        
        Args:
            persona: "samara" (high serotonin, moderate dopamine) or 
                     "artery" (low serotonin, high acetylcholine)
        """
        self.persona = persona.lower()
        self._init_from_persona()
        
        # State history
        self.state_history: list = []
        self.max_history = 200
        
        # Cross-modulator interaction matrix
        # Format: (source, target) -> influence_factor
        self.interactions = {
            ("dopamine", "norepinephrine"): 0.2,   # DA excites NE
            ("serotonin", "dopamine"): -0.15,      # 5-HT inhibits DA
            ("norepinephrine", "acetylcholine"): 0.15,  # NE boosts ACh
            ("acetylcholine", "norepinephrine"): 0.1,   # ACh modulates NE
            ("serotonin", "norepinephrine"): -0.1,      # 5-HT calms NE
        }
        
        self.last_update = time.time()

    def _init_from_persona(self):
        """Initialize baseline levels based on persona."""
        if self.persona == "samara":
            self.dopamine = 0.70
            self.serotonin = 0.65
            self.norepinephrine = 0.50
            self.acetylcholine = 0.55
        elif self.persona == "artery":
            self.dopamine = 0.30
            self.serotonin = 0.35
            self.norepinephrine = 0.30
            self.acetylcholine = 0.70
        else:
            # Default neutral
            self.dopamine = 0.50
            self.serotonin = 0.50
            self.norepinephrine = 0.40
            self.acetylcholine = 0.50

    def process_reward(self, reward: float, expected: Optional[float] = None):
        """
        Process a reward signal.
        Updates dopamine and has downstream effects.
        """
        expected = expected if expected is not None else self.dopamine * 0.8
        prediction_error = reward - expected
        
        # Dopamine responds to prediction error
        if prediction_error > 0:
            self.dopamine = min(1.0, self.dopamine + prediction_error * 0.3)
        else:
            self.dopamine = max(0.1, self.dopamine + prediction_error * 0.15)
        
        # Positive reward also boosts serotonin slightly
        if reward > 0.6:
            self.serotonin = min(1.0, self.serotonin + 0.05)
        
        self._apply_cross_modulator_effects()
        self._record_state()

    def process_social_feedback(self, valence: float, intensity: float):
        """
        Process social feedback (praise, criticism, connection).
        """
        if valence > 0:
            # Positive social feedback boosts serotonin and dopamine
            self.serotonin = min(1.0, self.serotonin + intensity * valence * 0.15)
            self.dopamine = min(1.0, self.dopamine + intensity * valence * 0.1)
        else:
            # Negative social feedback decreases serotonin
            self.serotonin = max(0.1, self.serotonin - intensity * abs(valence) * 0.2)
        
        self._apply_cross_modulator_effects()
        self._record_state()

    def process_novelty(self, novelty: float):
        """
        Process a novel stimulus.
        Boosts norepinephrine and acetylcholine.
        """
        self.norepinephrine = min(1.0, self.norepinephrine + novelty * 0.2)
        self.acetylcholine = min(1.0, self.acetylcholine + novelty * 0.15)
        self._apply_cross_modulator_effects()
        self._record_state()

    def process_threat(self, threat: float):
        """
        Process a threatening stimulus.
        Strongly boosts norepinephrine, may decrease serotonin.
        """
        self.norepinephrine = min(1.0, self.norepinephrine + threat * 0.35)
        # Prolonged threat depletes serotonin
        if threat > 0.5:
            self.serotonin = max(0.1, self.serotonin - 0.05)
        self._apply_cross_modulator_effects()
        self._record_state()

    def focus_attention(self, intensity: float):
        """
        Engage focused attention.
        Boosts acetylcholine and norepinephrine.
        """
        self.acetylcholine = min(1.0, self.acetylcholine + intensity * 0.25)
        self.norepinephrine = min(1.0, self.norepinephrine + intensity * 0.1)
        self._apply_cross_modulator_effects()
        self._record_state()

    def _apply_cross_modulator_effects(self):
        """Apply cross-modulator interactions."""
        # Store current levels
        levels = {
            "dopamine": self.dopamine,
            "serotonin": self.serotonin,
            "norepinephrine": self.norepinephrine,
            "acetylcholine": self.acetylcholine
        }
        
        # Apply interactions
        for (src, tgt), factor in self.interactions.items():
            influence = levels[src] * factor
            new_val = levels[tgt] + influence
            levels[tgt] = max(0.0, min(1.0, new_val))
        
        self.dopamine = levels["dopamine"]
        self.serotonin = levels["serotonin"]
        self.norepinephrine = levels["norepinephrine"]
        self.acetylcholine = levels["acetylcholine"]

    def update_tonic(self):
        """Apply tonic regulation (decay toward baseline)."""
        dt = time.time() - self.last_update
        
        # Decay each modulator toward its persona-specific baseline
        decay_rate = 0.01 * dt
        
        if self.persona == "samara":
            self.dopamine = self._decay(self.dopamine, 0.70, decay_rate)
            self.serotonin = self._decay(self.serotonin, 0.65, decay_rate)
            self.norepinephrine = self._decay(self.norepinephrine, 0.50, decay_rate)
            self.acetylcholine = self._decay(self.acetylcholine, 0.55, decay_rate)
        else:  # artery
            self.dopamine = self._decay(self.dopamine, 0.30, decay_rate)
            self.serotonin = self._decay(self.serotonin, 0.35, decay_rate)
            self.norepinephrine = self._decay(self.norepinephrine, 0.30, decay_rate)
            self.acetylcholine = self._decay(self.acetylcholine, 0.70, decay_rate)
        
        self.last_update = time.time()
        self._record_state()

    def _decay(self, current: float, baseline: float, rate: float) -> float:
        """Decay current value toward baseline."""
        if current > baseline:
            return max(baseline, current - rate * (current - baseline))
        else:
            return min(baseline, current + rate * (baseline - current))

    def _record_state(self):
        """Record current state to history."""
        state = self.get_state()
        self.state_history.append(state)
        if len(self.state_history) > self.max_history:
            self.state_history = self.state_history[-self.max_history:]

    def get_state(self) -> NeuromodulationState:
        """Return the current integrated neuromodulatory state."""
        # Compute derived states
        motivation = self._sigmoid(self.dopamine - 0.4, 8.0)
        patience = 0.3 + self.serotonin * 0.7
        
        # Arousal from norepinephrine
        arousal = self._sigmoid(self.norepinephrine - 0.3, 10.0)
        
        # Attention quality (inverted-U on acetylcholine)
        opt = 0.65
        attention_quality = 1.0 - 0.4 * abs(self.acetylcholine - opt) / max(opt, 1.0 - opt)
        
        # Mood valence: serotonin positive, low serotonin negative
        mood_valence = (self.serotonin - 0.4) * 1.5
        
        # Stress from high norepinephrine
        stress_level = max(0.0, (self.norepinephrine - 0.5) * 2.0)
        
        # Learning rate modulation
        learning_rate_mod = 0.1 * (1.0 + self.acetylcholine) * (1.0 + self.dopamine * 0.5)
        
        return NeuromodulationState(
            dopamine=self.dopamine,
            serotonin=self.serotonin,
            norepinephrine=self.norepinephrine,
            acetylcholine=self.acetylcholine,
            motivation=motivation,
            patience=patience,
            arousal=arousal,
            attention_quality=attention_quality,
            mood_valence=mood_valence,
            stress_level=stress_level,
            learning_rate_mod=learning_rate_mod
        )

    def _sigmoid(self, x: float, k: float = 1.0) -> float:
        """Sigmoid activation function."""
        try:
            return 1.0 / (1.0 + (-k * x).exp())
        except:
            import math
            return 1.0 / (1.0 + math.exp(-k * x))

    def reset(self):
        """Reset to persona-specific baseline."""
        self._init_from_persona()
        self.state_history.clear()
        self.last_update = time.time()

    def get_summary(self) -> Dict[str, Any]:
        """Return a human-readable summary of current state."""
        state = self.get_state()
        return {
            "persona": self.persona,
            "mood": "positive" if state.mood_valence > 0.2 else ("negative" if state.mood_valence < -0.2 else "neutral"),
            "motivation": "high" if state.motivation > 0.6 else ("low" if state.motivation < 0.3 else "moderate"),
            "attention": "focused" if state.attention_quality > 0.7 else "distracted",
            "stress": "elevated" if state.stress_level > 0.5 else "normal",
            "levels": {
                "dopamine": round(self.dopamine, 2),
                "serotonin": round(self.serotonin, 2),
                "norepinephrine": round(self.norepinephrine, 2),
                "acetylcholine": round(self.acetylcholine, 2)
            }
        }
