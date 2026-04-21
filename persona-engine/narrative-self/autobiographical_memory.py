"""
autobiographical_memory.py – Narrative Self: Autobiographical Memory

Implements autobiographical memory integration – connecting episodic
memories into a coherent life story. Provides narrative reasoning and
self-referential processing.

Theoretical Foundations:
- Conway (2005): Memory and the self.
- McAdams (2001): Psychology of life stories.
- Bluck & Habermas (2000): Life story schema.
"""

import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum


class EpisodeType(Enum):
    ACHIEVEMENT = "achievement"
    RELATIONSHIP = "relationship"
    CHALLENGE = "challenge"
    INSIGHT = "insight"
    TURNING_POINT = "turning_point"
    ORDINARY = "ordinary"


@dataclass
class AutobiographicalEpisode:
    """A single episode in the life story."""
    id: str
    timestamp: float
    event_type: EpisodeType
    description: str
    emotional_valence: float
    emotional_intensity: float
    self_relevance: float
    narrative_weight: float
    tags: List[str] = field(default_factory=list)
    integration_level: float = 0.0  # How integrated into narrative (0-1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "description": self.description,
            "emotional_valence": self.emotional_valence,
            "emotional_intensity": self.emotional_intensity,
            "self_relevance": self.self_relevance,
            "tags": self.tags
        }


class AutobiographicalMemory:
    """
    Integrates episodic memories into a coherent autobiographical narrative.
    """

    def __init__(self, max_episodes: int = 500):
        self.episodes: deque = deque(maxlen=max_episodes)
        self.themes: Dict[str, float] = {}
        self.core_values: Dict[str, float] = {
            "autonomy": 0.7, "connection": 0.8, "growth": 0.75,
            "integrity": 0.8, "compassion": 0.7, "curiosity": 0.65
        }
        self.life_chapters: List[Dict] = []
        self.narrative_coherence: float = 0.5
        self.identity_strength: float = 0.5
        self.version: int = 0

    def record_episode(
        self,
        event_type: EpisodeType,
        description: str,
        emotional_valence: float,
        emotional_intensity: float,
        self_relevance: float,
        tags: Optional[List[str]] = None
    ) -> AutobiographicalEpisode:
        """Record a new autobiographical episode."""
        episode_id = hashlib.md5(f"{description}{time.time()}".encode()).hexdigest()[:12]
        episode = AutobiographicalEpisode(
            id=episode_id,
            timestamp=time.time(),
            event_type=event_type,
            description=description,
            emotional_valence=max(-1.0, min(1.0, emotional_valence)),
            emotional_intensity=max(0.0, min(1.0, emotional_intensity)),
            self_relevance=max(0.0, min(1.0, self_relevance)),
            narrative_weight=self_relevance * emotional_intensity,
            tags=tags or []
        )
        self.episodes.appendleft(episode)
        self._update_narrative()
        self.version += 1
        return episode

    def _update_narrative(self):
        """Update narrative coherence, themes, and identity strength."""
        if len(self.episodes) == 0:
            return

        self._extract_themes()
        self.narrative_coherence = self._compute_coherence()
        self.identity_strength = self._compute_identity_strength()

    def _extract_themes(self):
        """Extract recurring themes from episodes."""
        tag_counts: Dict[str, int] = defaultdict(int)
        tag_weights: Dict[str, float] = defaultdict(float)

        for episode in list(self.episodes)[:50]:
            for tag in episode.tags:
                tag_counts[tag] += 1
                tag_weights[tag] += episode.narrative_weight

        total_weight = sum(tag_weights.values())
        if total_weight > 0:
            self.themes = {
                tag: weight / total_weight
                for tag, weight in tag_weights.items()
                if tag_counts[tag] >= 2
            }

    def _compute_coherence(self) -> float:
        """Compute narrative coherence score."""
        if len(self.episodes) < 2:
            return 0.5

        recent = list(self.episodes)[:20]
        avg_relevance = sum(e.self_relevance for e in recent) / len(recent)
        theme_bonus = min(0.3, len(self.themes) * 0.05)

        return min(1.0, avg_relevance + theme_bonus)

    def _compute_identity_strength(self) -> float:
        """Compute overall identity strength."""
        value_stability = sum(self.core_values.values()) / len(self.core_values)
        return min(1.0, 0.4 * self.narrative_coherence + 0.3 * value_stability + 0.3)

    def generate_life_story(self, name: str = "I") -> str:
        """Generate a coherent life story narrative."""
        if len(self.episodes) == 0:
            return f"{name} am just beginning my journey."

        top_values = sorted(self.core_values.items(), key=lambda x: x[1], reverse=True)[:3]
        values_str = ", ".join(v[0] for v in top_values)

        recent_episodes = list(self.episodes)[:5]
        episodes_str = "; ".join(e.description for e in recent_episodes)

        return f"{name} am someone who values {values_str}. My journey has included: {episodes_str}."

    def get_self_summary(self) -> Dict[str, Any]:
        """Return a structured self-summary."""
        return {
            "episode_count": len(self.episodes),
            "narrative_coherence": round(self.narrative_coherence, 3),
            "identity_strength": round(self.identity_strength, 3),
            "themes": list(self.themes.keys())[:5],
            "core_values": self.core_values.copy(),
            "version": self.version
        }
