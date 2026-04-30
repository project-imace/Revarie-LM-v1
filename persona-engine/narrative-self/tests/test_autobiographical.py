import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from autobiographical_memory import AutobiographicalMemory, EpisodeType

def test_episode_recording():
    am = AutobiographicalMemory()
    ep = am.record_episode(EpisodeType.ACHIEVEMENT, "Test", 0.5, 0.5, 0.5)
    assert len(am.episodes) == 1

def test_identity_strength_update():
    am = AutobiographicalMemory()
    am.record_episode(EpisodeType.ACHIEVEMENT, "Test", 0.8, 0.7, 0.9)
    assert am.identity_strength > 0.0

def test_summary_serialization():
    am = AutobiographicalMemory()
    summary = am.get_self_summary()
    assert "episode_count" in summary
    assert "themes" in summary

def test_generate_life_story_empty():
    am = AutobiographicalMemory()
    story = am.generate_life_story()
    assert story == "I am just beginning my journey."

    story_custom = am.generate_life_story(name="Samara")
    assert story_custom == "Samara am just beginning my journey."

def test_generate_life_story_with_content():
    am = AutobiographicalMemory()
    # Add some episodes. They are added to the left (start of deque)
    am.record_episode(EpisodeType.ACHIEVEMENT, "I learned to code", 0.8, 0.9, 0.9)
    am.record_episode(EpisodeType.RELATIONSHIP, "I met a friend", 0.7, 0.6, 0.8)
    am.record_episode(EpisodeType.CHALLENGE, "I faced a bug", -0.3, 0.5, 0.7)

    story = am.generate_life_story()

    # Check if name is there
    assert story.startswith("I am someone who values")

    # Check for core values (top 3)
    # Default values: "autonomy": 0.7, "connection": 0.8, "growth": 0.75, "integrity": 0.8, "compassion": 0.7, "curiosity": 0.65
    # Top 3 are connection (0.8), integrity (0.8), growth (0.75)
    assert "connection" in story
    assert "integrity" in story
    assert "growth" in story

    # Check for episode descriptions in output
    assert "I faced a bug" in story
    assert "I met a friend" in story
    assert "I learned to code" in story

def test_generate_life_story_limit_episodes():
    am = AutobiographicalMemory()
    for i in range(10):
        am.record_episode(EpisodeType.ORDINARY, f"Episode {i}", 0.1, 0.1, 0.1)

    story = am.generate_life_story()
    # Should only contain the 5 most recent: 9, 8, 7, 6, 5
    for i in range(5, 10):
        assert f"Episode {i}" in story
    for i in range(0, 5):
        assert f"Episode {i}" not in story

def test_generate_life_story_custom_name():
    am = AutobiographicalMemory()
    am.record_episode(EpisodeType.ACHIEVEMENT, "Test episode", 0.5, 0.5, 0.5)
    story = am.generate_life_story(name="Agent")
    assert story.startswith("Agent am someone who values")
