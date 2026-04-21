"""
feature_extractor.py
Sensory Memory – Feature Extractor.
Extracts salient features from raw sensory input to prepare information
for attention selection and working memory encoding.
Based on Treisman's Feature Integration Theory and Broadbent's filter model.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter


class Modality(Enum):
    ICONIC = "iconic"
    ECHOIC = "echoic"
    HAPTIC = "haptic"


@dataclass
class ExtractedFeatures:
    """Container for features extracted from sensory input."""
    modality: Modality
    raw_content: str
    tokens: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    sentiment: Optional[float] = None
    salience_score: float = 0.0
    novelty_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""


class FeatureExtractor:
    """
    Extracts features from raw sensory input.
    Implements basic NLP feature extraction for textual input and
    provides hooks for other modalities.
    """

    def __init__(self, novelty_window: int = 100):
        self.novelty_window = novelty_window
        self.seen_hashes: Set[str] = set()
        self.recent_items: List[str] = []

    def extract(self, content: str, modality: Modality = Modality.ECHOIC) -> ExtractedFeatures:
        """Extract features from raw content."""
        features = ExtractedFeatures(
            modality=modality,
            raw_content=content,
            content_hash=self._compute_hash(content),
        )

        if modality == Modality.ECHOIC:
            features.tokens = self._tokenize(content)
            features.entities = self._extract_entities(content)
            features.sentiment = self._analyze_sentiment(content)
            features.salience_score = self._compute_salience(features)
            features.novelty_score = self._compute_novelty(features.content_hash)
            features.metadata = {
                "token_count": len(features.tokens),
                "entity_count": len(features.entities),
                "avg_token_length": sum(len(t) for t in features.tokens) / max(len(features.tokens), 1),
            }

        elif modality == Modality.ICONIC:
            features.salience_score = 0.5
            features.metadata = {"type": "visual"}

        elif modality == Modality.HAPTIC:
            features.salience_score = 0.7
            features.metadata = {"type": "tactile"}

        self._update_novelty_tracking(features.content_hash)
        return features

    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace and punctuation tokenization."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()

    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential named entities (capitalized words)."""
        words = text.split()
        entities = []
        for word in words:
            clean = re.sub(r'[^\w]', '', word)
            if clean and clean[0].isupper() and len(clean) > 1:
                entities.append(clean)
        return entities

    def _analyze_sentiment(self, text: str) -> float:
        """Simple rule-based sentiment analysis."""
        positive_words = {"good", "great", "happy", "excellent", "wonderful", "love", "like"}
        negative_words = {"bad", "terrible", "sad", "awful", "hate", "dislike", "poor"}
        tokens = self._tokenize(text)
        pos_count = sum(1 for t in tokens if t in positive_words)
        neg_count = sum(1 for t in tokens if t in negative_words)
        if pos_count + neg_count == 0:
            return 0.0
        return (pos_count - neg_count) / (pos_count + neg_count)

    def _compute_salience(self, features: ExtractedFeatures) -> float:
        """Compute salience score based on token count and entities."""
        score = 0.3
        if features.tokens:
            score += min(len(features.tokens) / 50, 0.3)
        if features.entities:
            score += min(len(features.entities) * 0.1, 0.4)
        return min(score, 1.0)

    def _compute_novelty(self, content_hash: str) -> float:
        """Compute novelty score (1.0 = completely new, 0.0 = recently seen)."""
        if content_hash in self.seen_hashes:
            return 0.0
        return 1.0

    def _compute_hash(self, content: str) -> str:
        """Compute stable hash of content."""
        return hashlib.md5(content.encode()).hexdigest()

    def _update_novelty_tracking(self, content_hash: str):
        """Update novelty tracking state."""
        self.seen_hashes.add(content_hash)
        self.recent_items.append(content_hash)
        if len(self.recent_items) > self.novelty_window:
            old_hash = self.recent_items.pop(0)
            self.seen_hashes.discard(old_hash)


# =============================================================================
# Tests (pytest compatible)
# =============================================================================
def test_feature_extraction_text():
    extractor = FeatureExtractor()
    features = extractor.extract("I am feeling very happy today!", Modality.ECHOIC)
    assert features.modality == Modality.ECHOIC
    assert "happy" in features.tokens
    assert features.sentiment > 0.0
    assert 0.0 <= features.salience_score <= 1.0


def test_novelty_tracking():
    extractor = FeatureExtractor()
    features1 = extractor.extract("Hello world")
    assert features1.novelty_score == 1.0
    features2 = extractor.extract("Hello world")
    assert features2.novelty_score == 0.0


def test_entity_extraction():
    extractor = FeatureExtractor()
    features = extractor.extract("John went to Paris with Mary.")
    assert "John" in features.entities or "Paris" in features.entities


def test_iconic_modality():
    extractor = FeatureExtractor()
    features = extractor.extract("some visual data", Modality.ICONIC)
    assert features.modality == Modality.ICONIC
    assert features.tokens == []
