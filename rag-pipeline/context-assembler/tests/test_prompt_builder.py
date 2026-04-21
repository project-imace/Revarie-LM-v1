import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from prompt_builder import PromptBuilder, Persona

def test_samara_system_prompt():
    builder = PromptBuilder(persona=Persona.SAMARA)
    messages = builder.build("Hi", [], {})
    assert "Samara" in messages[0]["content"]

def test_artery_system_prompt():
    builder = PromptBuilder(persona=Persona.ARTERY)
    messages = builder.build("Hi", [], {})
    assert "Artery" in messages[0]["content"]
