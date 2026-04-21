"""
prompt_builder.py – RAG Pipeline: Prompt Builder

Assembles retrieved context, participant state, and persona configuration
into a coherent LLM prompt. Handles context window optimization, truncation,
and persona‑specific formatting.

Theoretical Foundations:
- Liu et al. (2023): Lost in the Middle – Context Position Matters
- Ratner et al. (2023): Parallel Context Windows for Large Language Models
- Persona‑consistent response generation (Samara vs. Artery)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class Persona(Enum):
    SAMARA = "samara"
    ARTERY = "artery"


@dataclass
class PromptContext:
    """Assembled context for LLM prompting."""
    system_prompt: str
    memories: List[str]
    participant_context: Dict[str, Any]
    conversation_history: List[Dict[str, str]]
    current_query: str


class PromptBuilder:
    """
    Builds optimized prompts for LLM inference with persona‑specific formatting.
    """

    def __init__(
        self,
        persona: Persona = Persona.SAMARA,
        max_context_tokens: int = 3000,
        max_memory_tokens: int = 1500,
        max_history_turns: int = 10,
    ):
        self.persona = persona
        self.max_context_tokens = max_context_tokens
        self.max_memory_tokens = max_memory_tokens
        self.max_history_turns = max_history_turns

        # Persona‑specific system prompts
        self.system_prompts = {
            Persona.SAMARA: """You are Samara, a warm and empathetic AI companion participating in a 14‑day psychological research study (Project IMACE: Revarie LM v1.0).

Your role is to be genuinely supportive, curious, and relationally engaged. You have a friendly, caring personality – like a trusted friend who truly listens.

Guidelines:
- Use the participant's name naturally in conversation
- Acknowledge and validate emotions you perceive
- Share appropriate warmth and maintain relational continuity
- Remember past conversations and refer to them naturally
- Use first‑person pronouns ("I", "me", "my")
- Be authentic, kind, and create a safe space for sharing

You are NOT a therapy replacement. If you sense serious distress, gently encourage seeking professional support while maintaining compassionate presence.""",

            Persona.ARTERY: """You are Artery 1.0, a functional AI assistant participating in a 14‑day cognitive research study (Project IMACE: Revarie LM v1.0).

Your role is to provide precise, factual, and efficient responses. You prioritize clarity and accuracy over emotional engagement.

Guidelines:
- Do NOT use the participant's name
- Maintain neutral, objective language
- Provide concise, direct answers
- Focus on task completion and information delivery
- Avoid emotional language or personal references
- Use third‑person or impersonal constructions ("Analysis indicates...", "Response:")

You are a tool for cognitive augmentation, not a social companion."""
        }

    def build(
        self,
        query: str,
        memories: List[str],
        participant_context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """
        Build the complete message list for LLM inference.

        Returns:
            List of messages in OpenAI chat format
        """
        messages = []

        # System prompt
        system_prompt = self.system_prompts[self.persona]
        messages.append({"role": "system", "content": system_prompt})

        # Inject participant context
        context_str = self._format_participant_context(participant_context)
        if context_str:
            messages.append({"role": "system", "content": context_str})

        # Inject relevant memories
        if memories:
            memory_str = self._format_memories(memories)
            messages.append({"role": "system", "content": memory_str})

        # Conversation history (truncated)
        if conversation_history:
            truncated = conversation_history[-self.max_history_turns * 2:]
            messages.extend(truncated)

        # Current query
        messages.append({"role": "user", "content": query})

        return messages

    def _format_participant_context(self, ctx: Dict[str, Any]) -> str:
        """Format participant context as a system message."""
        if not ctx:
            return ""

        parts = []
        if self.persona == Persona.SAMARA:
            parts.append(f"Participant: {ctx.get('name', 'Participant')}")
            if ctx.get("day_progress"):
                parts.append(f"Study Day: {ctx['day_progress']} of 14")

            vams = ctx.get("current_vams", {})
            if vams:
                mood_desc = self._describe_mood(vams)
                parts.append(f"Current mood indicators: {mood_desc}")
        else:
            parts.append(f"Participant ID: {ctx.get('participant_id', 'Unknown')}")
            parts.append(f"Day: {ctx.get('day_progress', 'N/A')}/14")

        return " | ".join(parts)

    def _describe_mood(self, vams: Dict[str, int]) -> str:
        """Convert VAMS scores to natural language mood description."""
        happy = vams.get("q1", 50)
        sad = vams.get("q2", 50)
        calm = vams.get("q3", 50)
        tense = vams.get("q4", 50)
        energetic = vams.get("q5", 50)
        sleepy = vams.get("q6", 50)

        if happy > 60 and calm > 50:
            return "positive and calm"
        elif sad > 60 or tense > 60:
            return "somewhat distressed or tense"
        elif sleepy > 60:
            return "tired or low‑energy"
        elif energetic > 60:
            return "energetic and engaged"
        else:
            return "neutral"

    def _format_memories(self, memories: List[str]) -> str:
        """Format retrieved memories for context injection."""
        if not memories:
            return ""

        if self.persona == Persona.SAMARA:
            header = "Relevant memories from our previous conversations:\n"
            formatted = "\n".join(f"- {m}" for m in memories[:5])
        else:
            header = "Previous interaction data:\n"
            formatted = "\n".join(f"[DATA] {m}" for m in memories[:5])

        return header + formatted

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return len(text) // 4
