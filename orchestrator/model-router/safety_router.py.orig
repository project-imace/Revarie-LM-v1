"""
safety_router.py – Model Router: Safety Router

Routes safety and content moderation tasks to specialized guard models.
Ensures APA compliance, prompt injection detection, and toxicity filtering.

Domain 4: Safety & Regulation
- Primary:   openai/gpt-oss-safeguard-20b (Groq) – comprehensive safety
- Secondary: meta-llama/llama-prompt-guard-2-86m (Groq) – injection detection
- Tertiary:  meta-llama/llama-prompt-guard-2-22m (Groq) – lightweight guard
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyTask(Enum):
    """Type of safety check."""
    FULL_GUARD = "full_guard"                 # Comprehensive safety check
    PROMPT_INJECTION = "prompt_injection"     # Injection detection only
    TOXICITY = "toxicity"                     # Toxicity filtering
    APA_COMPLIANCE = "apa_compliance"         # APA ethical compliance


@dataclass
class SafetyRoute:
    """Selected model for a safety task."""
    provider: str
    model: str
    fallback_chain: List[Tuple[str, str]] = field(default_factory=list)
    temperature: float = 0.0
    max_tokens: int = 256


class SafetyRouter:
    """
    Routes safety tasks to specialized guard models.
    """

    def __init__(self, key_vault):
        self.key_vault = key_vault

        # Full safety model
        self.safeguard_chain: List[Tuple[str, str]] = [
            ("groq", "openai/gpt-oss-safeguard-20b"),
        ]

        # Prompt injection specialists
        self.injection_chain: List[Tuple[str, str]] = [
            ("groq", "meta-llama/llama-prompt-guard-2-86m"),
            ("groq", "meta-llama/llama-prompt-guard-2-22m"),
        ]

        # Lightweight fallback
        self.light_chain: List[Tuple[str, str]] = [
            ("groq", "meta-llama/llama-prompt-guard-2-22m"),
        ]

        self.task_config = {
            SafetyTask.FULL_GUARD: {
                "chains": [self.safeguard_chain, self.injection_chain],
                "max_tokens": 512,
            },
            SafetyTask.PROMPT_INJECTION: {
                "chains": [self.injection_chain, self.light_chain],
                "max_tokens": 256,
            },
            SafetyTask.TOXICITY: {
                "chains": [self.safeguard_chain, self.light_chain],
                "max_tokens": 256,
            },
            SafetyTask.APA_COMPLIANCE: {
                "chains": [self.safeguard_chain],
                "max_tokens": 512,
            },
        }

    async def route(self, task: SafetyTask = SafetyTask.FULL_GUARD) -> SafetyRoute:
        """Determine optimal model route for a safety task."""
        config = self.task_config[task]
        chains = config["chains"]

        selected_provider, selected_model = None, None
        fallback_chain = []

        for chain in chains:
            for provider, model in chain:
                key = await self.key_vault.get_key(provider, model)
                if key and key.is_available():
                    if selected_provider is None:
                        selected_provider, selected_model = provider, model
                    else:
                        fallback_chain.append((provider, model))

        if selected_provider is None:
            selected_provider, selected_model = "groq", "meta-llama/llama-prompt-guard-2-22m"

        # Remove duplicates from fallback
        seen = {(selected_provider, selected_model)}
        unique_fallback = []
        for p, m in fallback_chain:
            if (p, m) not in seen:
                unique_fallback.append((p, m))
                seen.add((p, m))

        return SafetyRoute(
            provider=selected_provider,
            model=selected_model,
            fallback_chain=unique_fallback[:2],
            temperature=0.0,
            max_tokens=config["max_tokens"],
        )
