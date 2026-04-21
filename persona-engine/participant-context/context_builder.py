"""
context_builder.py – Participant Context: Context Builder

Assembles comprehensive contextual state for each participant by integrating
D1 structured data, Vectorize episodic memory, and current session information.
Provides a unified context object for downstream LLM prompting and persona modulation.

Theoretical Foundations:
- Tulving (1972): Episodic vs. semantic memory distinction
- Baddeley (2000): Working memory as integrated episodic buffer
- Endel Tulving (1985): Memory and consciousness
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class MemoryType(Enum):
    """Types of memory integrated into participant context."""
    SEMANTIC = "semantic"       # D1 structured data
    EPISODIC = "episodic"       # Vectorize conversation embeddings
    WORKING = "working"         # Current session state
    PROCEDURAL = "procedural"   # Interaction patterns/habits


@dataclass
class ParticipantContext:
    """Complete contextual state for a participant."""
    participant_id: str
    name: str
    study_group: str
    ai_type: str
    day_progress: int
    has_onboarded: bool
    is_disqualified: bool

    # Semantic memory (D1)
    age: Optional[int] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None
    pre_study_mind_experience: Optional[Dict] = None
    post_study_mind_experience: Optional[Dict] = None

    # Current session state
    current_vams: Dict[str, int] = field(default_factory=dict)
    previous_vams: Optional[Dict[str, int]] = None
    vams_trend: Optional[Dict[str, float]] = None

    # Episodic memory
    recent_memories: List[Dict] = field(default_factory=list)
    daily_summaries: List[str] = field(default_factory=list)

    # Derived state
    emotional_baseline: Dict[str, float] = field(default_factory=dict)
    interaction_style: Dict[str, float] = field(default_factory=dict)
    rapport_level: float = 0.0
    trust_level: float = 0.0

    # Metadata
    last_updated: float = field(default_factory=time.time)
    context_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "participant_id": self.participant_id,
            "name": self.name,
            "study_group": self.study_group,
            "ai_type": self.ai_type,
            "day_progress": self.day_progress,
            "has_onboarded": self.has_onboarded,
            "is_disqualified": self.is_disqualified,
            "age": self.age,
            "gender": self.gender,
            "country": self.country,
            "status": self.status,
            "current_vams": self.current_vams,
            "previous_vams": self.previous_vams,
            "vams_trend": self.vams_trend,
            "emotional_baseline": self.emotional_baseline,
            "interaction_style": self.interaction_style,
            "rapport_level": self.rapport_level,
            "trust_level": self.trust_level,
            "last_updated": self.last_updated,
        }


class ContextBuilder:
    """
    Builds comprehensive participant context by integrating multiple memory systems.
    """

    def __init__(
        self,
        d1_client,
        vector_store_client,
        embedding_generator,
        cache_ttl: int = 300,
    ):
        """
        Initialize context builder.

        Args:
            d1_client: D1SchemaClient for structured data
            vector_store_client: VectorStoreClient for episodic memory
            embedding_generator: EmbeddingGenerator for semantic search
            cache_ttl: Cache time-to-live in seconds
        """
        self.d1 = d1_client
        self.vector_store = vector_store_client
        self.embedder = embedding_generator
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, Tuple[ParticipantContext, float]] = {}

    async def build(
        self,
        participant_id: str,
        current_query: Optional[str] = None,
        force_refresh: bool = False,
    ) -> ParticipantContext:
        """
        Build complete participant context.

        Args:
            participant_id: Participant identifier
            current_query: Current user message for memory retrieval
            force_refresh: Skip cache and rebuild

        Returns:
            Complete ParticipantContext
        """
        # Check cache
        if not force_refresh and participant_id in self.cache:
            ctx, timestamp = self.cache[participant_id]
            if time.time() - timestamp < self.cache_ttl:
                return ctx

        # Fetch semantic memory from D1
        participant = await self.d1.get_participant(participant_id)
        if not participant:
            raise ValueError(f"Participant {participant_id} not found")

        # Initialize context with semantic data
        ctx = ParticipantContext(
            participant_id=participant_id,
            name=participant.name,
            study_group=participant.study_group,
            ai_type=participant.ai_type,
            day_progress=participant.day_progress,
            has_onboarded=participant.has_onboarded,
            is_disqualified=participant.is_disqualified,
            age=participant.age,
            gender=participant.gender,
            country=participant.country,
            status=participant.status,
            pre_study_mind_experience=participant.pre_study_mind_experience,
            post_study_mind_experience=participant.post_study_mind_experience,
        )

        # Fetch current VAMS
        sessions = await self.d1.get_participant_sessions(participant_id, limit=2)
        if sessions:
            current = sessions[0]
            ctx.current_vams = current.pre_vams
            if len(sessions) > 1:
                ctx.previous_vams = sessions[1].pre_vams
                ctx.vams_trend = self._compute_vams_trend(ctx.current_vams, ctx.previous_vams)

        # Compute emotional baseline from pre-study data
        if ctx.pre_study_mind_experience:
            ctx.emotional_baseline = self._extract_emotional_baseline(ctx.pre_study_mind_experience)

        # Fetch episodic memories if query provided
        if current_query and self.vector_store:
            query_embedding = await self.embedder.embed_single(current_query)
            memories = await self.vector_store.query_by_participant(
                participant_id, query_embedding, top_k=5
            )
            ctx.recent_memories = [m.metadata for m in memories]

            # Extract daily summaries
            summary_memories = await self.vector_store.query_by_participant(
                participant_id,
                query_embedding,
                top_k=3,
                memory_type="daily_summary",
            )
            ctx.daily_summaries = [
                m.metadata.get("summary_text", "") for m in summary_memories
            ]

        # Derive interaction style from history
        ctx.interaction_style = self._derive_interaction_style(ctx)

        # Cache and return
        self.cache[participant_id] = (ctx, time.time())
        return ctx

    def _compute_vams_trend(
        self, current: Dict[str, int], previous: Dict[str, int]
    ) -> Dict[str, float]:
        """Compute trend between current and previous VAMS."""
        trend = {}
        for i in range(1, 7):
            key = f"q{i}"
            if key in current and key in previous:
                trend[key] = current[key] - previous[key]
        return trend

    def _extract_emotional_baseline(self, pre_study: Dict) -> Dict[str, float]:
        """Extract emotional baseline from pre-study mind experience data."""
        baseline = {
            "positive_affect": 0.5,
            "negative_affect": 0.5,
            "wellbeing": 0.5,
            "trust_in_ai": 0.5,
        }

        # Extract PANAS if present
        if "panas" in pre_study:
            panas = pre_study["panas"]
            pos_items = ["interested", "excited", "strong", "enthusiastic", "proud", "alert", "inspired", "determined", "attentive", "active"]
            neg_items = ["distressed", "upset", "guilty", "hostile", "irritable", "ashamed", "nervous", "jittery", "afraid"]

            pos_sum = sum(panas.get(item, 3) for item in pos_items)
            neg_sum = sum(panas.get(item, 3) for item in neg_items)

            baseline["positive_affect"] = min(1.0, pos_sum / (len(pos_items) * 5))
            baseline["negative_affect"] = min(1.0, neg_sum / (len(neg_items) * 5))

        # Extract WHO-5 if present
        if "who5" in pre_study:
            who5 = pre_study["who5"]
            items = ["cheerful", "calm", "active", "rested", "interested"]
            total = sum(who5.get(item, 3) for item in items)
            baseline["wellbeing"] = min(1.0, total / (len(items) * 5))

        # Extract TIAS if present
        if "tias" in pre_study:
            tias = pre_study["tias"]
            trust_items = ["confident", "security", "integrity", "dependable", "reliable", "trust"]
            trust_sum = sum(tias.get(item, 4) for item in trust_items)
            baseline["trust_in_ai"] = min(1.0, trust_sum / (len(trust_items) * 7))

        return baseline

    def _derive_interaction_style(self, ctx: ParticipantContext) -> Dict[str, float]:
        """Derive preferred interaction style from context."""
        style = {
            "prefers_detail": 0.5,
            "prefers_brevity": 0.5,
            "emotional_expressiveness": 0.5,
            "question_frequency": 0.5,
        }

        # Adjust based on VAMS
        if ctx.current_vams:
            # High energy = prefers brevity?
            energy = ctx.current_vams.get("q5", 50) / 100.0
            style["prefers_brevity"] = 0.3 + 0.4 * energy

            # High tense = prefers detail?
            tense = ctx.current_vams.get("q4", 50) / 100.0
            style["prefers_detail"] = 0.3 + 0.4 * (1.0 - tense)

        # Adjust based on emotional baseline
        if ctx.emotional_baseline:
            style["emotional_expressiveness"] = ctx.emotional_baseline.get("positive_affect", 0.5)

        return style

    def clear_cache(self, participant_id: Optional[str] = None):
        """Clear context cache."""
        if participant_id:
            self.cache.pop(participant_id, None)
        else:
            self.cache.clear()

    def get_cached_context(self, participant_id: str) -> Optional[ParticipantContext]:
        """Get cached context if available and fresh."""
        if participant_id in self.cache:
            ctx, timestamp = self.cache[participant_id]
            if time.time() - timestamp < self.cache_ttl:
                return ctx
        return None
