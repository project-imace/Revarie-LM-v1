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
