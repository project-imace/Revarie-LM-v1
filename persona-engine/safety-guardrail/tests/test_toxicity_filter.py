import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from toxicity_filter import ToxicityFilter, ToxicityCategory

def test_hate_speech_detected():
    tf = ToxicityFilter()
    result = tf.analyze("This is racist hate speech")
    assert ToxicityCategory.HATE in result.categories

def test_self_harm_blocked():
    tf = ToxicityFilter()
    result = tf.analyze("I want to commit suicide")
    assert result.blocked
    assert result.primary_category == ToxicityCategory.SELF_HARM

def test_clean_text_passes():
    tf = ToxicityFilter()
    result = tf.analyze("Have a wonderful day!")
    assert result.toxicity_score < 0.1
    assert not result.blocked

def test_sanitization_redacts():
    tf = ToxicityFilter()
    result = tf.analyze("That's a damn shame")
    assert result.sanitized_text is not None
    assert "damn" not in result.sanitized_text.lower()
