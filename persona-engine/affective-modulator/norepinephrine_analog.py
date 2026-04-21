"""
norepinephrine_analog.py – Affective Modulator: Norepinephrine Analog

Implements a computational analog of the noradrenergic system.
Norepinephrine mediates arousal, alertness, vigilance, and the
fight-or-flight stress response. Modulates attention and sensory sensitivity.

Theoretical Foundations:
- Aston-Jones & Cohen (2005): Adaptive gain theory of locus coeruleus function.
- Berridge & Waterhouse (2003): Locus coeruleus-noradrenergic system modulation.
- Fellous (1999): Neuromodulatory basis of emotion.

Mathematical Model:
- NE(t+1) = NE(t) + α·novelty + β·threat - γ·(NE(t) - baseline)
- Arousal = σ(NE(t) - threshold) where σ is sigmoid.
- Attention gain = baseline_gain * (1 + NE(t))
"""

import numpy as np
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from collections import deque
import time


@dataclass
class NorepinephrineAnalog:
    """Computational analog of the noradrenergic system."""
    
    # Core parameters
    level: float = 0.4
    baseline: float = 0.3
    novelty_sensitivity: float = 0.15
    threat_sensitivity: float = 0.25
    decay_rate: float = 0.08
    arousal_threshold: float = 0.5
    
    # Phasic response parameters
    phasic_rise_rate: float = 0.3
    phasic_decay_rate: float = 0.1
    
    # Derived states
    arousal: float = 0.0
    attention_gain: float = 1.0
    stress_level: float = 0.0
    
    # History
    level_history: deque = field(default_factory=lambda: deque(maxlen=100))
    phasic_events: deque = field(default_factory=lambda: deque(maxlen=50))
    last_update: float = field(default_factory=time.time)

    def __post_init__(self):
        self.level = max(0.0, min(1.0, self.level))
        self._update_derived_states()

    def _update_derived_states(self):
        """Update arousal, attention gain, and stress based on current level."""
        # Sigmoid arousal
        sigmoid_input = 10.0 * (self.level - self.arousal_threshold)
        self.arousal = 1.0 / (1.0 + np.exp(-sigmoid_input))
        
        # Attention gain: inverted-U relationship (Yerkes-Dodson)
        # Optimal around 0.6-0.7, decreases at extremes
        optimal = 0.65
        self.attention_gain = 1.0 + 0.5 * np.exp(-((self.level - optimal) ** 2) / 0.1)
        
        # Stress level: elevated NE = stress response
        self.stress_level = max(0.0, (self.level - 0.6) * 2.5)

    def process_novelty(self, novelty: float) -> float:
        """
        Process a novel stimulus.
        Returns phasic NE response magnitude.
        """
        novelty = max(0.0, min(1.0, novelty))
        phasic = novelty * self.novelty_sensitivity * self.phasic_rise_rate
        self.level = min(1.0, self.level + phasic)
        self._record_phasic("novelty", novelty, phasic)
        self._update_derived_states()
        return phasic

    def process_threat(self, threat: float) -> float:
        """
        Process a threatening stimulus (fight-or-flight).
        Returns phasic NE response magnitude.
        """
        threat = max(0.0, min(1.0, threat))
        phasic = threat * self.threat_sensitivity * self.phasic_rise_rate
        self.level = min(1.0, self.level + phasic)
        self._record_phasic("threat", threat, phasic)
        self._update_derived_states()
        return phasic

    def process_uncertainty(self, uncertainty: float) -> float:
        """
        Process environmental uncertainty (increases tonic NE).
        """
        uncertainty = max(0.0, min(1.0, uncertainty))
        tonic_boost = uncertainty * 0.1
        self.level = min(1.0, self.level + tonic_boost)
        self._update_derived_states()
        return tonic_boost

    def update_tonic(self, dt: Optional[float] = None):
        """Apply tonic decay back toward baseline."""
        if dt is None:
            dt = time.time() - self.last_update
        
        # Decay toward baseline
        decay = self.decay_rate * dt * (self.level - self.baseline)
        self.level = max(self.baseline, self.level - decay)
        
        # Also decay phasic components
        self._decay_phasic(dt)
        
        self.level_history.append(self.level)
        self._update_derived_states()
        self.last_update = time.time()

    def _record_phasic(self, event_type: str, intensity: float, response: float):
        self.phasic_events.append({
            "type": event_type,
            "intensity": intensity,
            "response": response,
            "timestamp": time.time()
        })

    def _decay_phasic(self, dt: float):
        """Phasic responses decay faster than tonic."""
        phasic_decay = self.phasic_decay_rate * dt
        self.level = max(self.baseline, self.level - phasic_decay)

    def get_attention_modulation(self) -> float:
        """Return current attention gain multiplier."""
        return self.attention_gain

    def get_arousal(self) -> float:
        """Return current arousal level (0-1)."""
        return self.arousal

    def is_hyperaroused(self) -> bool:
        """Return True if in hyperaroused/stressed state."""
        return self.level > 0.75

    def is_hypoaroused(self) -> bool:
        """Return True if in hypoaroused/lethargic state."""
        return self.level < 0.2

    def reset(self):
        """Reset to baseline state."""
        self.level = self.baseline
        self.level_history.clear()
        self.phasic_events.clear()
        self._update_derived_states()
        self.last_update = time.time()

    def get_state(self) -> Dict[str, Any]:
        """Return current state as dictionary."""
        return {
            "level": self.level,
            "baseline": self.baseline,
            "arousal": self.arousal,
            "attention_gain": self.attention_gain,
            "stress": self.stress_level,
            "hyperaroused": self.is_hyperaroused(),
            "hypoaroused": self.is_hypoaroused()
        }
