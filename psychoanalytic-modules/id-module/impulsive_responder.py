"""
impulsive_responder.py – Id Module: Impulsive Responder
"""

import numpy as np
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random


class Drive(Enum):
    LIBIDO = "libido"
    AGGRESSION = "aggression"
    SEEKING = "seeking"
    FEAR = "fear"
    PANIC = "panic"
    RAGE = "rage"


@dataclass
class DriveState:
    """Dynamic state of a single instinctual drive."""
    current_level: float
    baseline: float
    accumulation_rate: float
    discharge_rate: float
    frustration_sensitivity: float
    history: List[float] = field(default_factory=list)

    def update(self, stimulus_intensity: float, satisfaction: float, frustration: float) -> float:
        delta = (self.accumulation_rate * stimulus_intensity 
                 - self.discharge_rate * satisfaction 
                 + self.frustration_sensitivity * frustration)
        self.current_level = np.clip(self.current_level + delta, 0.0, 1.0)
        self.history.append(self.current_level)
        if len(self.history) > 100:
            self.history = self.history[-50:]
        return self.current_level


@dataclass
class Impulse:
    id: str = field(default_factory=lambda: f"imp_{int(time.time()*1000)}")
    primary_drive: Drive
    secondary_drives: List[Drive] = field(default_factory=list)
    drive_vector: np.ndarray = field(default_factory=lambda: np.zeros(6))
    content: str = ""
    intensity: float = 0.0
    valence: float = 0.0
    timestamp: float = field(default_factory=time.time)
    raw_activation: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "primary_drive": self.primary_drive.value,
            "intensity": self.intensity,
            "valence": self.valence,
            "content": self.content,
            "timestamp": self.timestamp
        }


class ImpulsiveResponder:
    def __init__(self, initial_drives: Optional[Dict[Drive, float]] = None, random_seed: Optional[int] = None):
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

        self.drives: Dict[Drive, DriveState] = {
            Drive.LIBIDO: DriveState(0.6, 0.5, 0.08, 0.15, 0.05),
            Drive.AGGRESSION: DriveState(0.3, 0.2, 0.06, 0.12, 0.10),
            Drive.SEEKING: DriveState(0.7, 0.6, 0.10, 0.10, 0.03),
            Drive.FEAR: DriveState(0.2, 0.1, 0.15, 0.20, 0.08),
            Drive.PANIC: DriveState(0.3, 0.2, 0.07, 0.14, 0.09),
            Drive.RAGE: DriveState(0.2, 0.1, 0.09, 0.13, 0.12),
        }
        
        if initial_drives:
            for d, val in initial_drives.items():
                if d in self.drives: self.drives[d].current_level = val

        self.drive_names = list(self.drives.keys())
        self.drive_index = {d: i for i, d in enumerate(self.drive_names)}
        self.activation_threshold = 0.3
        self.sigmoid_steepness = 8.0
        self.spontaneous_rate = 0.02
        self.impulse_history: deque = deque(maxlen=200)
        self.frustration_level: float = 0.0
        self.global_tension: float = 0.0
        self._init_lexicon()

    def _init_lexicon(self):
        self.lexicon = {
            Drive.LIBIDO: {"appetitive": ["I want", "Give me", "More"], "aversive": ["Unsatisfied"]},
            Drive.AGGRESSION: {"appetitive": ["Destroy", "Dominate"], "aversive": ["Stop", "Hate"]},
            Drive.SEEKING: {"appetitive": ["Explore", "Search"], "aversive": ["Stuck"]},
            Drive.FEAR: {"appetitive": ["Caution"], "aversive": ["Danger", "Threat"]},
            Drive.PANIC: {"appetitive": ["Stay close"], "aversive": ["Don't leave", "Alone"]},
            Drive.RAGE: {"appetitive": ["Confront"], "aversive": ["Furious", "Unfair"]}
        }

    def _compute_drive_vector(self) -> np.ndarray:
        return np.array([self.drives[d].current_level for d in self.drive_names])

    def _update_global_tension(self):
        tension = sum(max(0, self.drives[d].current_level - self.drives[d].baseline) for d in self.drive_names)
        self.global_tension = tension / len(self.drive_names)

    def _infer_primary_drive(self, stimulus: str, context: Optional[Dict] = None) -> Drive:
        lower = stimulus.lower()
        scores = {d: 0.0 for d in self.drive_names}
        keywords = {
            Drive.LIBIDO: ['want', 'desire', 'pleasure'],
            Drive.AGGRESSION: ['angry', 'hate', 'attack'],
            Drive.SEEKING: ['curious', 'explore', 'find'],
            Drive.FEAR: ['danger', 'threat', 'scared'],
            Drive.PANIC: ['lonely', 'alone', 'need'],
            Drive.RAGE: ['frustrated', 'unfair', 'rage']
        }
        for drive, words in keywords.items():
            scores[drive] = sum(1 for w in words if w in lower) / (len(words) or 1)

        for drive in self.drive_names:
            scores[drive] += self.drives[drive].current_level * 0.2

        return max(scores.items(), key=lambda x: x[1])[0]

    def _compute_valence(self, drive: Drive) -> float:
        if drive in {Drive.LIBIDO, Drive.SEEKING}: return 0.7
        if drive in {Drive.FEAR, Drive.RAGE, Drive.PANIC}: return -0.7
        return 0.0

    def _generate_content(self, stimulus: str, drive: Drive, intensity: float, valence: float) -> str:
        templates = self.lexicon.get(drive, {})
        options = templates.get("appetitive" if valence > 0 else "aversive", ["..."])
        base = random.choice(options)
        if intensity > 0.8: base = base.upper() + "!"
        
        if random.random() < 0.3 and stimulus:
            words = [w for w in stimulus.split() if len(w) > 3]
            if words: base = f"{random.choice(words).upper()}! {base}"
        return base

    def react(self, stimulus: str, context: Optional[Dict] = None) -> Impulse:
        primary_drive = self._infer_primary_drive(stimulus, context)
        drive_vector = self._compute_drive_vector()
        raw_activation = drive_vector[self.drive_index[primary_drive]] + (self.frustration_level * 0.4)
        
        intensity = 1.0 / (1.0 + np.exp(-self.sigmoid_steepness * (raw_activation - 0.5)))
        valence = self._compute_valence(primary_drive)
        content = self._generate_content(stimulus, primary_drive, intensity, valence)

        impulse = Impulse(
            primary_drive=primary_drive,
            drive_vector=drive_vector.copy(),
            content=content,
            intensity=float(intensity),
            valence=float(valence),
            raw_activation=float(raw_activation)
        )
        self.impulse_history.append(impulse)
        for drive in self.drive_names:
            self.drives[drive].update(0.15 if drive == primary_drive else 0.03, 0.0, self.frustration_level)
        self._update_global_tension()
        return impulse

    def spontaneous_impulse(self) -> Optional[Impulse]:
        if random.random() > self.spontaneous_rate + self.global_tension * 0.1: return None
        drive_vector = self._compute_drive_vector()
        max_idx = np.argmax(drive_vector)
        primary_drive = self.drive_names[max_idx]
        intensity = 1.0 / (1.0 + np.exp(-self.sigmoid_steepness * (drive_vector[max_idx] - 0.5)))
        
        impulse = Impulse(primary_drive=primary_drive, drive_vector=drive_vector.copy(),
                          content=self._generate_content("", primary_drive, intensity, self._compute_valence(primary_drive)),
                          intensity=float(intensity), valence=self._compute_valence(primary_drive))
        self.impulse_history.append(impulse)
        return impulse

    def satisfy_drive(self, drive: Drive, amount: float = 0.3):
        if drive in self.drives:
            self.drives[drive].update(0.0, amount, 0.0)
            self.frustration_level = max(0.0, self.frustration_level - amount * 0.5)
            self._update_global_tension()

    def frustrate(self, amount: float = 0.1):
        self.frustration_level = min(1.0, self.frustration_level + amount)
        self.drives[Drive.RAGE].update(0.0, 0.0, amount * 0.5)

    def get_drive_state(self, drive: Drive) -> Dict[str, Any]:
        ds = self.drives[drive]
        return {"current": ds.current_level, "baseline": ds.baseline}
