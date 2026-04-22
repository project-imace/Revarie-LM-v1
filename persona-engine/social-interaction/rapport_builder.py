"""
rapport_builder.py – Social Interaction: Rapport Builder

Implements computational rapport building through active listening,
self-disclosure reciprocity, common ground discovery, and trust calibration.
Based on social penetration theory and therapeutic alliance research.

Theoretical Foundations:
- Altman & Taylor (1973): Social penetration theory.
- Tickle-Degnen & Rosenthal (1990): Nature of rapport.
- Bickmore & Picard (2005): Relational agents and therapeutic alliance.
- Collins & Miller (1994): Self-disclosure and liking.
"""

import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum


class RapportStage(Enum):
    """Stages of rapport development."""
    INITIAL = "initial"
    EXPLORATORY = "exploratory"
    AFFECTIVE = "affective"
    STABLE = "stable"
    INTIMATE = "intimate"


@dataclass
class RapportState:
    """Current state of rapport with a participant."""
    participant_id: str
    level: float = 0.2                    # Overall rapport (0-1)
    trust: float = 0.1                    # Trust component
    attentiveness: float = 0.5            # Active listening quality
    positivity: float = 0.5               # Positive affect component
    coordination: float = 0.5             # Interactional synchrony
    self_disclosure_depth: float = 0.0    # How deep the sharing has gone
    common_ground_topics: set = field(default_factory=set)
    interaction_count: int = 0
    stage: RapportStage = RapportStage.INITIAL
    last_interaction: float = field(default_factory=time.time)
    history: deque = field(default_factory=lambda: deque(maxlen=100))


class RapportBuilder:
    """
    Builds and maintains rapport with individual participants.
    Implements active listening, self-disclosure reciprocity, and trust calibration.
    """

    def __init__(self, persona: str = "samara"):
        """
        Initialize with persona-specific rapport-building style.
        
        Args:
            persona: "samara" (warm, high disclosure) or "artery" (reserved, low disclosure)
        """
        self.persona = persona.lower()
        self.states: Dict[str, RapportState] = {}
        
        # Persona-specific parameters
        if self.persona == "samara":
            self.disclosure_reciprocity = 0.9    # High reciprocity
            self.warmth_baseline = 0.85
            self.trust_building_rate = 0.15
            self.disclosure_cap = 0.8
        else:  # artery
            self.disclosure_reciprocity = 0.2    # Low reciprocity
            self.warmth_baseline = 0.15
            self.trust_building_rate = 0.05
            self.disclosure_cap = 0.1
        
        # Rapport decay parameters
        self.decay_rate = 0.01                  # Per day without interaction
        self.min_retention = 0.3                # Minimum retained rapport

    def get_or_create_state(self, participant_id: str) -> RapportState:
        """Retrieve or initialize rapport state for a participant."""
        if participant_id not in self.states:
            self.states[participant_id] = RapportState(participant_id=participant_id)
        return self.states[participant_id]

    def process_interaction(
        self,
        participant_id: str,
        user_message: str,
        user_emotional_tone: Optional[str] = None,
        user_self_disclosure: float = 0.0,
        turn_taking_smoothness: float = 0.7,
        shared_interests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a single interaction turn and update rapport.
        
        Returns:
            Dictionary with rapport update details and any recommended actions.
        """
        state = self.get_or_create_state(participant_id)
        state.interaction_count += 1
        state.last_interaction = time.time()
        
        # 1. Update attentiveness (active listening)
        listening_quality = self._assess_listening(user_message)
        state.attentiveness = 0.7 * state.attentiveness + 0.3 * listening_quality
        
        # 2. Update positivity (affective component)
        sentiment = self._analyze_sentiment(user_message)
        state.positivity = 0.6 * state.positivity + 0.4 * sentiment
        
        # 3. Update coordination (interactional synchrony)
        state.coordination = 0.5 * state.coordination + 0.5 * turn_taking_smoothness
        
        # 4. Process self-disclosure reciprocity
        if user_self_disclosure > 0.0:
            appropriate_response_depth = min(
                user_self_disclosure * self.disclosure_reciprocity,
                self.disclosure_cap
            )
            state.self_disclosure_depth = 0.7 * state.self_disclosure_depth + 0.3 * appropriate_response_depth
        
        # 5. Update common ground
        if shared_interests:
            for interest in shared_interests:
                state.common_ground_topics.add(interest)
        
        # 6. Update trust (accumulates slowly)
        trust_increment = (
            0.1 * state.attentiveness +
            0.1 * state.positivity +
            0.05 * state.coordination +
            0.05 * min(len(state.common_ground_topics), 5) / 5.0
        ) * self.trust_building_rate
        state.trust = min(1.0, state.trust + trust_increment)
        
        # 7. Compute overall rapport level
        state.level = self._compute_rapport_level(state)
        
        # 8. Update stage
        state.stage = self._determine_stage(state)
        
        # 9. Record history
        state.history.append({
            "timestamp": time.time(),
            "level": state.level,
            "trust": state.trust,
            "stage": state.stage.value
        })
        
        return {
            "participant_id": participant_id,
            "rapport_level": state.level,
            "trust": state.trust,
            "stage": state.stage.value,
            "appropriate_disclosure_depth": min(
                user_self_disclosure * self.disclosure_reciprocity,
                self.disclosure_cap
            ),
            "common_ground_count": len(state.common_ground_topics),
            "recommendation": self._generate_recommendation(state)
        }

    def _assess_listening(self, message: str) -> float:
        """Assess active listening cues in user message."""
        cues = ["?", "what do you think", "how about you", "your turn", "you know"]
        lower = message.lower()
        matches = sum(1 for cue in cues if cue in lower)
        return min(1.0, 0.5 + matches * 0.15)

    def _analyze_sentiment(self, message: str) -> float:
        """Simple rule-based sentiment analysis."""
        positive = ["good", "great", "happy", "like", "love", "wonderful", "excellent", "yes", "thanks"]
        negative = ["bad", "sad", "angry", "hate", "terrible", "awful", "no", "dislike"]
        lower = message.lower()
        pos_count = sum(1 for w in positive if w in lower)
        neg_count = sum(1 for w in negative if w in lower)
        if pos_count + neg_count == 0:
            return 0.5
        return pos_count / (pos_count + neg_count)

    def _compute_rapport_level(self, state: RapportState) -> float:
        """Compute overall rapport as weighted combination."""
        weights = {
            "trust": 0.35,
            "attentiveness": 0.20,
            "positivity": 0.20,
            "coordination": 0.15,
            "self_disclosure_depth": 0.10
        }
        level = (
            weights["trust"] * state.trust +
            weights["attentiveness"] * state.attentiveness +
            weights["positivity"] * state.positivity +
            weights["coordination"] * state.coordination +
            weights["self_disclosure_depth"] * state.self_disclosure_depth
        )
        # Common ground bonus
        common_bonus = min(0.1, len(state.common_ground_topics) * 0.02)
        return min(1.0, level + common_bonus)

    def _determine_stage(self, state: RapportState) -> RapportStage:
        """Determine current rapport stage."""
        if state.level < 0.2:
            return RapportStage.INITIAL
        elif state.level < 0.4:
            return RapportStage.EXPLORATORY
        elif state.level < 0.6:
            return RapportStage.AFFECTIVE
        elif state.level < 0.8:
            return RapportStage.STABLE
        else:
            return RapportStage.INTIMATE

    def _generate_recommendation(self, state: RapportState) -> str:
        """Generate rapport-building recommendation."""
        if state.stage == RapportStage.INITIAL:
            return "Establish basic trust through attentive listening."
        elif state.stage == RapportStage.EXPLORATORY:
            return "Discover common ground and shared interests."
        elif state.stage == RapportStage.AFFECTIVE:
            return "Share appropriate personal experiences to deepen connection."
        elif state.stage == RapportStage.STABLE:
            return "Maintain consistency and show genuine care."
        else:
            return "Continue nurturing the deep connection with authenticity."

    def apply_decay(self, participant_id: Optional[str] = None):
        """Apply time-based decay to rapport for inactive participants."""
        now = time.time()
        participants = [participant_id] if participant_id else list(self.states.keys())
        
        for pid in participants:
            if pid not in self.states:
                continue
            state = self.states[pid]
            days_inactive = (now - state.last_interaction) / 86400.0
            
            if days_inactive > 1.0:
                decay = math.exp(-self.decay_rate * days_inactive)
                state.level = max(self.min_retention, state.level * decay)
                state.trust = max(self.min_retention * 0.5, state.trust * decay)
                state.attentiveness = 0.5 * state.attentiveness + 0.5 * 0.5
                
                if state.level < 0.3:
                    state.stage = RapportStage.EXPLORATORY

    def get_rapport_summary(self, participant_id: str) -> Dict[str, Any]:
        """Return a summary of rapport state for a participant."""
        state = self.get_or_create_state(participant_id)
        return {
            "participant_id": participant_id,
            "level": round(state.level, 3),
            "stage": state.stage.value,
            "trust": round(state.trust, 3),
            "interaction_count": state.interaction_count,
            "common_ground": list(state.common_ground_topics)[:5],
            "disclosure_depth": round(state.self_disclosure_depth, 3)
        }

    def get_greeting(self, participant_id: str) -> str:
        """Generate persona-appropriate greeting based on rapport."""
        state = self.get_or_create_state(participant_id)
        
        if self.persona == "samara":
            if state.level < 0.3:
                return "Hi there! I'm Samara. It's nice to meet you."
            elif state.level < 0.6:
                return f"Welcome back! It's so good to see you again."
            else:
                return f"I'm so happy you're here. I've been looking forward to our conversation."
        else:  # artery
            if state.level < 0.3:
                return "Greetings. Artery 1.0 ready."
            elif state.level < 0.6:
                return "Session initiated. Continuing interaction."
            else:
                return "Session initiated. Previous data indicates established rapport."

    def reset(self, participant_id: Optional[str] = None):
        """Reset rapport state for one or all participants."""
        if participant_id:
            if participant_id in self.states:
                del self.states[participant_id]
        else:
            self.states.clear()


# =============================================================================
# Tests
# =============================================================================
def test_rapport_initialization():
    rb = RapportBuilder("samara")
    state = rb.get_or_create_state("P001")
    assert state.level == 0.2
    assert state.stage == RapportStage.INITIAL

def test_interaction_increases_rapport():
    rb = RapportBuilder("samara")
    result = rb.process_interaction(
        "P001",
        "I'm feeling good today, what do you think about that?",
        user_emotional_tone="positive",
        user_self_disclosure=0.3
    )
    assert result["rapport_level"] > 0.2

def test_samara_vs_artery_disclosure():
    samara = RapportBuilder("samara")
    artery = RapportBuilder("artery")
    
    samara_result = samara.process_interaction("P001", "test", user_self_disclosure=0.7)
    artery_result = artery.process_interaction("P002", "test", user_self_disclosure=0.7)
    
    assert samara_result["appropriate_disclosure_depth"] > artery_result["appropriate_disclosure_depth"]

def test_common_ground_accumulation():
    rb = RapportBuilder("samara")
    rb.process_interaction("P001", "I love hiking", shared_interests=["hiking", "nature"])
    rb.process_interaction("P001", "The mountains are beautiful", shared_interests=["mountains"])
    
    state = rb.get_or_create_state("P001")
    assert len(state.common_ground_topics) >= 2

def test_decay_over_time():
    rb = RapportBuilder("samara")
    rb.process_interaction("P001", "Hello", user_self_disclosure=0.5)
    initial = rb.get_or_create_state("P001").level
    
    # Simulate time passing
    state = rb.get_or_create_state("P001")
    state.last_interaction = time.time() - 10 * 86400  # 10 days ago
    rb.apply_decay("P001")
    
    assert rb.get_or_create_state("P001").level < initial


if __name__ == "__main__":
    rb = RapportBuilder("samara")
    result = rb.process_interaction(
        "P001",
        "I'm really excited about this project! What do you think?",
        user_emotional_tone="positive",
        user_self_disclosure=0.5,
        shared_interests=["AI", "psychology"]
    )
    print(f"Rapport: {result['rapport_level']:.2f}, Stage: {result['stage']}")
