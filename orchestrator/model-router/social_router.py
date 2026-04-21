"""
social_router.py – Model Router: Social Router

Routes social/interactive tasks to models optimized for conversational
fluency, empathy, and rapport building. Differentiates between Samara
(high anthropomorphism) and Artery (low anthropomorphism) contexts.

Domain 2: Social Interactive Models
- Primary:   llama-3.3-70b-versatile (Groq) – best social intelligence
- Secondary: meta-llama/llama-4-scout-17b-16e-instruct (Groq) – efficient
- Tertiary:  llama3.1-8b (Cerebras) – lightweight fallback
- Premium:   gemini-2.5-flash / flash-lite (Gemini) – sparingly
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SocialContext(Enum):
    """Context of social interaction."""
    GREETING = "greeting"
    RAPPORT_BUILDING = "rapport_building"
    EMOTIONAL_SUPPORT = "emotional_support"
    CASUAL_CHAT = "casual_chat"
    TASK_ORIENTED = "task_oriented"
    FAREWELL = "farewell"


@dataclass
class SocialRoute:
    """Selected model for a social task."""
    provider: str
    model: str
    persona: str  # "samara" or "artery"
    fallback_chain: List[Tuple[str, str]] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 1024
    use_gemini_fallback: bool = False


class SocialRouter:
    """
    Routes social/interactive tasks to appropriate models.
    """

    def __init__(self, key_vault, persona: str = "samara"):
        self.key_vault = key_vault
        self.persona = persona.lower()

        # Primary chain (Groq first, then Cerebras)
        self.primary_chain: List[Tuple[str, str]] = [
            ("groq", "llama-3.3-70b-versatile"),
            ("groq", "meta-llama/llama-4-scout-17b-16e-instruct"),
            ("cerebras", "llama3.1-8b"),
        ]

        # Premium fallback (Gemini – use sparingly)
        self.premium_chain: List[Tuple[str, str]] = [
            ("gemini", "gemini-2.5-flash"),
            ("gemini", "gemini-2.5-flash-lite"),
        ]

        # Context-specific temperature adjustments
        self.context_temperature = {
            SocialContext.GREETING: 0.8,
            SocialContext.RAPPORT_BUILDING: 0.7,
            SocialContext.EMOTIONAL_SUPPORT: 0.6,
            SocialContext.CASUAL_CHAT: 0.8,
            SocialContext.TASK_ORIENTED: 0.4,
            SocialContext.FAREWELL: 0.7,
        }

        # Samara uses warmer language (higher temp, more variety)
        # Artery uses precise language (lower temp)
        self.persona_temperature_boost = {
            "samara": 0.1,
            "artery": -0.1,
        }

    def classify_context(self, prompt: str, conversation_history: Optional[List] = None) -> SocialContext:
        """Classify the social context of the interaction."""
        lower = prompt.lower()

        if any(w in lower for w in ["hello", "hi", "hey", "greetings"]):
            return SocialContext.GREETING
        if any(w in lower for w in ["bye", "goodbye", "farewell", "see you"]):
            return SocialContext.FAREWELL
        if any(w in lower for w in ["sad", "upset", "worried", "anxious", "happy", "excited"]):
            return SocialContext.EMOTIONAL_SUPPORT
        if any(w in lower for w in ["how are you", "what do you think", "tell me about"]):
            return SocialContext.RAPPORT_BUILDING
        if "?" in lower or any(w in lower for w in ["what", "how", "when", "where"]):
            return SocialContext.TASK_ORIENTED

        return SocialContext.CASUAL_CHAT

    async def route(
        self,
        prompt: str,
        conversation_history: Optional[List] = None,
        force_provider: Optional[str] = None,
    ) -> SocialRoute:
        """Determine optimal model route for a social task."""
        context = self.classify_context(prompt, conversation_history)

        # Build available chain
        available_chain = []
        for provider, model in self.primary_chain:
            if force_provider and provider != force_provider:
                continue
            key = await self.key_vault.get_key(provider, model)
            if key and key.is_available():
                available_chain.append((provider, model))

        # If primary chain exhausted, consider Gemini (sparingly)
        use_gemini = False
        if not available_chain and context in [SocialContext.EMOTIONAL_SUPPORT, SocialContext.RAPPORT_BUILDING]:
            for provider, model in self.premium_chain:
                key = await self.key_vault.get_key(provider, model)
                if key and key.is_available():
                    available_chain.append((provider, model))
                    use_gemini = True
                    break

        # Fallback to any available
        if not available_chain:
            for provider, model in self.primary_chain + self.premium_chain:
                key = await self.key_vault.get_key(provider, model)
                if key:
                    available_chain.append((provider, model))
                    break

        if not available_chain:
            available_chain = [("groq", "llama-3.3-70b-versatile")]

        selected = available_chain[0]
        fallback = available_chain[1:4] if len(available_chain) > 1 else []

        # Compute temperature
        base_temp = self.context_temperature.get(context, 0.7)
        temp_boost = self.persona_temperature_boost.get(self.persona, 0.0)
        temperature = max(0.1, min(1.0, base_temp + temp_boost))

        return SocialRoute(
            provider=selected[0],
            model=selected[1],
            persona=self.persona,
            fallback_chain=fallback,
            temperature=temperature,
            max_tokens=1024 if context != SocialContext.EMOTIONAL_SUPPORT else 1536,
            use_gemini_fallback=use_gemini,
        )
