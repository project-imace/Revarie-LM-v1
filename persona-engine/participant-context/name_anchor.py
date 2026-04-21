"""
name_anchor.py – Participant Context: Name Anchor

Controls the use of participant names in AI responses. Samara uses names
frequently to build relational warmth; Artery bypasses name usage entirely
to maintain functional neutrality.

Theoretical Foundations:
- Epley, Waytz, & Cacioppo (2007): Anthropomorphism and name usage
- Nass & Brave (2005): "Wired for Speech" – voice and identity
- Bickmore & Picard (2005): Relational agents and personalization
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class NameUsagePolicy(Enum):
    """Policy for using participant names."""
    ALWAYS = "always"           # Use name frequently (Samara)
    NEVER = "never"             # Never use name (Artery)
    CONTEXTUAL = "contextual"   # Use based on rapport level


@dataclass
class NameAnchor:
    """
    Controls participant name usage based on persona policy.
    """

    policy: NameUsagePolicy
    participant_name: str
    rapport_level: float = 0.0
    name_usage_count: int = 0
    max_uses_per_session: int = 10

    @classmethod
    def for_samara(cls, participant_name: str, rapport_level: float = 0.0) -> "NameAnchor":
        """Create name anchor for Samara (high name usage)."""
        return cls(
            policy=NameUsagePolicy.ALWAYS,
            participant_name=participant_name,
            rapport_level=rapport_level,
            max_uses_per_session=20,
        )

    @classmethod
    def for_artery(cls, participant_name: str) -> "NameAnchor":
        """Create name anchor for Artery (no name usage)."""
        return cls(
            policy=NameUsagePolicy.NEVER,
            participant_name=participant_name,
            max_uses_per_session=0,
        )

    def should_use_name(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if name should be used in current context.

        Args:
            context: Optional context dict containing:
                - is_greeting: bool
                - is_farewell: bool
                - emotional_intensity: float
                - message_position: str ('start', 'middle', 'end')

        Returns:
            True if name should be used
        """
        if self.policy == NameUsagePolicy.NEVER:
            return False

        if self.policy == NameUsagePolicy.ALWAYS:
            # Even Samara has limits to avoid overuse
            if self.name_usage_count >= self.max_uses_per_session:
                return False

            # Contextual adjustments for Samara
            if context:
                # Always use in greetings and farewells
                if context.get("is_greeting") or context.get("is_farewell"):
                    return True

                # Use more with high emotional intensity
                if context.get("emotional_intensity", 0.0) > 0.6:
                    return True

                # Use at start, less in middle
                if context.get("message_position") == "start":
                    return True
                if context.get("message_position") == "middle":
                    return self.name_usage_count < 3

            # Default: use if not overused
            return self.name_usage_count < 5

        if self.policy == NameUsagePolicy.CONTEXTUAL:
            # Use name when rapport is established
            if self.rapport_level < 0.4:
                return False
            return self.name_usage_count < 3

        return False

    def personalize(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Personalize text by inserting participant name if appropriate.

        Args:
            text: Original response text
            context: Context for decision

        Returns:
            Personalized text
        """
        if not self.should_use_name(context):
            return text

        self.name_usage_count += 1

        # Insert name at appropriate position
        name = self.participant_name

        if context and context.get("is_greeting"):
            return f"{name}, {text[0].lower()}{text[1:]}" if text else f"Hello, {name}!"

        if context and context.get("is_farewell"):
            return f"{text} Take care, {name}."

        # Insert after first sentence or comma
        if ". " in text:
            parts = text.split(". ", 1)
            return f"{parts[0]}, {name}. {parts[1]}"

        if ", " in text:
            parts = text.split(", ", 1)
            return f"{parts[0]}, {name}, {parts[1]}"

        # Prepend if no good insertion point
        return f"{name}, {text}"

    def get_greeting(self) -> str:
        """Get persona-appropriate greeting."""
        if self.policy == NameUsagePolicy.NEVER:
            return "Greetings. Session initiated."

        if self.should_use_name({"is_greeting": True}):
            self.name_usage_count += 1
            if self.rapport_level > 0.6:
                return f"Welcome back, {self.participant_name}! It's so good to see you again."
            elif self.rapport_level > 0.3:
                return f"Hi {self.participant_name}! Great to have you here."
            else:
                return f"Hello, {self.participant_name}! I'm Samara. It's nice to meet you."

        return "Hello! I'm Samara. It's nice to meet you."

    def get_farewell(self) -> str:
        """Get persona-appropriate farewell."""
        if self.policy == NameUsagePolicy.NEVER:
            return "Session terminated."

        if self.should_use_name({"is_farewell": True}):
            self.name_usage_count += 1
            return f"Take care, {self.participant_name}. I'll be here when you return."

        return "Take care. I'll be here when you return."

    def reset_session(self):
        """Reset name usage counter for new session."""
        self.name_usage_count = 0

    def update_rapport(self, rapport_level: float):
        """Update rapport level for contextual policy."""
        self.rapport_level = rapport_level
