import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from name_anchor import NameAnchor, NameUsagePolicy

def test_samara_uses_name_in_greeting():
    anchor = NameAnchor.for_samara("Arijit")
    assert anchor.should_use_name({"is_greeting": True})

def test_artery_never_uses_name():
    anchor = NameAnchor.for_artery("Arijit")
    assert not anchor.should_use_name({"is_greeting": True})

def test_samara_greeting_contains_name():
    anchor = NameAnchor.for_samara("Arijit", rapport_level=0.5)
    greeting = anchor.get_greeting()
    assert "Arijit" in greeting

def test_artery_greeting_no_name():
    anchor = NameAnchor.for_artery("Arijit")
    greeting = anchor.get_greeting()
    assert "Arijit" not in greeting
    assert "Session initiated" in greeting

def test_personalize_inserts_name():
    anchor = NameAnchor.for_samara("Arijit")
    text = "I understand how you feel."
    personalized = anchor.personalize(text)
    assert "Arijit" in personalized

def test_usage_limit_enforced():
    anchor = NameAnchor.for_samara("Arijit")
    anchor.name_usage_count = 20
    assert not anchor.should_use_name()

def test_reset_session():
    anchor = NameAnchor.for_samara("Arijit")
    anchor.name_usage_count = 15
    anchor.reset_session()
    assert anchor.name_usage_count == 0

def test_artery_farewell_no_name():
    anchor = NameAnchor.for_artery("Arijit")
    farewell = anchor.get_farewell()
    assert "Arijit" not in farewell
    assert "Session terminated" in farewell

def test_samara_farewell_contains_name():
    anchor = NameAnchor.for_samara("Arijit")
    farewell = anchor.get_farewell()
    assert "Arijit" in farewell
    assert "Take care" in farewell

def test_samara_farewell_usage_limit_enforced():
    anchor = NameAnchor.for_samara("Arijit")
    anchor.name_usage_count = anchor.max_uses_per_session
    farewell = anchor.get_farewell()
    assert "Arijit" not in farewell
    assert farewell == "Take care. I'll be here when you return."

def test_contextual_farewell_high_rapport():
    anchor = NameAnchor(policy=NameUsagePolicy.CONTEXTUAL, participant_name="Arijit", rapport_level=0.5)
    farewell = anchor.get_farewell()
    assert "Arijit" in farewell

def test_contextual_farewell_low_rapport():
    anchor = NameAnchor(policy=NameUsagePolicy.CONTEXTUAL, participant_name="Arijit", rapport_level=0.2)
    farewell = anchor.get_farewell()
    assert "Arijit" not in farewell

def test_contextual_farewell_usage_limit_enforced():
    anchor = NameAnchor(policy=NameUsagePolicy.CONTEXTUAL, participant_name="Arijit", rapport_level=0.5)
    anchor.name_usage_count = 3
    farewell = anchor.get_farewell()
    assert "Arijit" not in farewell

def test_farewell_increments_usage_count():
    anchor = NameAnchor.for_samara("Arijit")
    initial_count = anchor.name_usage_count
    anchor.get_farewell()
    assert anchor.name_usage_count == initial_count + 1

def test_farewell_no_increment_when_name_not_used():
    anchor = NameAnchor.for_artery("Arijit")
    initial_count = anchor.name_usage_count
    anchor.get_farewell()
    assert anchor.name_usage_count == initial_count
