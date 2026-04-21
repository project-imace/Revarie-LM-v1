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
