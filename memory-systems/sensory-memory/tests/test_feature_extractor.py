"""
test_feature_extractor.py
Unit tests for Feature Extractor.
"""

import sys
import os
import importlib.util

import pytest

# Dynamically load the module (handles hyphenated directory names)
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "feature_extractor.py")
)
spec = importlib.util.spec_from_file_location("feature_extractor", module_path)
fe_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fe_module)

FeatureExtractor = fe_module.FeatureExtractor
ExtractedFeatures = fe_module.ExtractedFeatures
Modality = fe_module.Modality


def test_extract_text_modality():
    extractor = FeatureExtractor()
    features = extractor.extract("I am feeling very happy today!", Modality.ECHOIC)
    assert features.modality == Modality.ECHOIC
    assert "happy" in features.tokens
    assert "feeling" in features.tokens
    assert features.sentiment > 0.0
    assert 0.0 <= features.salience_score <= 1.0
    assert features.content_hash is not None
    assert len(features.content_hash) == 32


def test_extract_iconic_modality():
    extractor = FeatureExtractor()
    features = extractor.extract("visual_data", Modality.ICONIC)
    assert features.modality == Modality.ICONIC
    assert features.tokens == []
    assert features.entities == []
    assert features.sentiment is None
    assert features.salience_score == 0.5
    assert features.metadata == {"type": "visual"}


def test_extract_haptic_modality():
    extractor = FeatureExtractor()
    features = extractor.extract("tactile_input", Modality.HAPTIC)
    assert features.modality == Modality.HAPTIC
    assert features.salience_score == 0.7
    assert features.metadata == {"type": "tactile"}


def test_novelty_tracking():
    extractor = FeatureExtractor(novelty_window=3)
    f1 = extractor.extract("Hello world")
    assert f1.novelty_score == 1.0
    f2 = extractor.extract("Hello world")
    assert f2.novelty_score == 0.0
    f3 = extractor.extract("New content")
    assert f3.novelty_score == 1.0


def test_novelty_window_eviction():
    extractor = FeatureExtractor(novelty_window=2)
    extractor.extract("A")
    extractor.extract("B")
    extractor.extract("C")
    features = extractor.extract("A")
    assert features.novelty_score == 1.0


def test_entity_extraction():
    extractor = FeatureExtractor()
    features = extractor.extract("John went to Paris with Mary.")
    entities = features.entities
    assert any(e in entities for e in ["John", "Paris", "Mary"])


def test_sentiment_positive():
    extractor = FeatureExtractor()
    features = extractor.extract("I love this wonderful day!")
    assert features.sentiment > 0.3


def test_sentiment_negative():
    extractor = FeatureExtractor()
    features = extractor.extract("This is terrible and awful.")
    assert features.sentiment < -0.3


def test_sentiment_neutral():
    extractor = FeatureExtractor()
    features = extractor.extract("The sky is blue.")
    assert abs(features.sentiment) < 0.1


def test_salience_increases_with_tokens():
    extractor = FeatureExtractor()
    f1 = extractor.extract("Hi")
    f2 = extractor.extract("This is a much longer sentence with many words in it.")
    assert f2.salience_score > f1.salience_score


def test_salience_increases_with_entities():
    extractor = FeatureExtractor()
    f1 = extractor.extract("I saw a cat.")
    f2 = extractor.extract("John and Mary went to London and Paris.")
    assert f2.salience_score > f1.salience_score


def test_metadata_populated():
    extractor = FeatureExtractor()
    features = extractor.extract("Hello world!")
    assert "token_count" in features.metadata
    assert "entity_count" in features.metadata
    assert "avg_token_length" in features.metadata
    assert features.metadata["token_count"] > 0


def test_content_hash_stable():
    extractor = FeatureExtractor()
    f1 = extractor.extract("same content")
    f2 = extractor.extract("same content")
    assert f1.content_hash == f2.content_hash
    f3 = extractor.extract("different content")
    assert f1.content_hash != f3.content_hash
