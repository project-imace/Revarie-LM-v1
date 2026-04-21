"""
habit_strengthener.py
Procedural Memory – Habit Strengthener.
Implements habit formation and strengthening based on repetition and
reinforcement. Models the transition from goal-directed action to
automatic habit.

Theoretical foundations:
- Dickinson (1985): Actions and habits.
- Wood & Rünger (2016): Psychology of habit.
- Lally et al. (2010): How habits are formed.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import time
import math


@dataclass
class Habit:
    """A habit formed through repetition."""
    cue: str                    # Trigger for the habit
    response: str               # Automatic response
    strength: float = 0.1       # Habit strength (0.0 to 1.0)
    repetition_count: int = 0   # Number of times performed
    last_performed: float = field(default_factory=time.time)
    context_modifiers: Dict[str, float] = field(default_factory=dict)
    automated: bool = False     # Whether fully automatic


class HabitStrengthener:
    """
    Manages habit formation, strengthening, and decay.
    """

    def __init__(self, decay_rate: float = 0.01, automation_threshold: float = 0.7):
        self.habits: Dict[str, Habit] = {}
        self.decay_rate = decay_rate
        self.automation_threshold = automation_threshold
        self.history: List[Tuple[str, str, float]] = []  # (cue, response, timestamp)

    def _habit_key(self, cue: str, response: str) -> str:
        return f"{cue}->{response}"

    def get_or_create(self, cue: str, response: str) -> Habit:
        """Retrieve existing habit or create new one."""
        key = self._habit_key(cue, response)
        if key not in self.habits:
            self.habits[key] = Habit(cue=cue, response=response)
        return self.habits[key]

    def strengthen(self, cue: str, response: str, context: Optional[Dict[str, float]] = None):
        """
        Strengthen a habit based on successful execution.
        Strength increases follow a logarithmic learning curve.
        """
        habit = self.get_or_create(cue, response)
        habit.repetition_count += 1
        habit.last_performed = time.time()

        # Logarithmic increase in strength (diminishing returns)
        habit.strength = min(
            1.0,
            0.1 + 0.3 * math.log(habit.repetition_count + 1)
        )

        # Update context modifiers
        if context:
            for ctx_key, ctx_value in context.items():
                habit.context_modifiers[ctx_key] = (
                    habit.context_modifiers.get(ctx_key, 0.0) * 0.9 + ctx_value * 0.1
                )

        # Check for automation
        if habit.strength >= self.automation_threshold:
            habit.automated = True

        self.history.append((cue, response, time.time()))
        if len(self.history) > 1000:
            self.history = self.history[-500:]

    def get_strength(self, cue: str, response: str) -> float:
        """Get current strength of a habit."""
        habit = self.habits.get(self._habit_key(cue, response))
        if habit:
            return habit.strength
        return 0.0

    def is_automated(self, cue: str, response: str) -> bool:
        """Check if a habit has become automatic."""
        habit = self.habits.get(self._habit_key(cue, response))
        return habit.automated if habit else False

    def apply_decay(self):
        """Apply decay to all habits over time."""
        now = time.time()
        for habit in self.habits.values():
            elapsed_days = (now - habit.last_performed) / 86400.0
            if elapsed_days > 1.0:
                decay = math.exp(-self.decay_rate * elapsed_days)
                habit.strength = max(0.05, habit.strength * decay)

    def predict_response(self, cue: str, context: Optional[Dict[str, float]] = None) -> Optional[Tuple[str, float]]:
        """
        Predict the most likely habitual response to a cue.
        Returns (response, confidence).
        """
        best_response = None
        best_strength = 0.0

        for habit in self.habits.values():
            if habit.cue != cue:
                continue

            strength = habit.strength

            # Apply context modulation
            if context:
                for ctx_key, ctx_value in context.items():
                    if ctx_key in habit.context_modifiers:
                        strength *= (1.0 + 0.1 * habit.context_modifiers[ctx_key] * ctx_value)

            if strength > best_strength:
                best_strength = strength
                best_response = habit.response

        if best_response:
            return (best_response, best_strength)
        return None

    def get_automated_habits(self) -> List[Habit]:
        """Return all habits that have become automatic."""
        return [h for h in self.habits.values() if h.automated]

    def reset(self):
        """Clear all habits."""
        self.habits.clear()
        self.history.clear()

if __name__ == "__main__":
    hs = HabitStrengthener()
    hs.strengthen("greeting", "Hello!")
    print(f"Habit strength: {hs.get_strength('greeting', 'Hello!')}")
