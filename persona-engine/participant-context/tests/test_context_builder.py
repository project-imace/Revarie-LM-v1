import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from context_builder import ContextBuilder, ParticipantContext

@pytest.mark.asyncio
async def test_build_basic_context():
    mock_d1 = AsyncMock()
    mock_p = type('MockParticipant', (), {
        'participant_id': "P001",
        'name': "Test User",
        'study_group': "A",
        'ai_type': "Relational AI Samara",
        'day_progress': 3,
        'has_onboarded': True,
        'is_disqualified': False,
        'age': 25,
        'gender': 'Female',
        'country': 'India',
        'status': 'University',
        'pre_study_mind_experience': None,
        'post_study_mind_experience': None
    })()
    mock_d1.get_participant.return_value = mock_p
    mock_d1.get_participant_sessions.return_value = []

    mock_vs = AsyncMock()
    mock_emb = AsyncMock()

    builder = ContextBuilder(mock_d1, mock_vs, mock_emb, cache_ttl=0)
    ctx = await builder.build("P001")

    assert ctx.participant_id == "P001"
    assert ctx.name == "Test User"
    assert ctx.study_group == "A"

@pytest.mark.asyncio
async def test_cache_works():
    mock_d1 = AsyncMock()
    mock_p = type('MockParticipant', (), {
        'participant_id': "P001",
        'name': "Test",
        'study_group': "A",
        'ai_type': "Relational",
        'day_progress': 1,
        'has_onboarded': True,
        'is_disqualified': False,
        'age': 25,
        'gender': 'Female',
        'country': 'India',
        'status': 'University',
        'pre_study_mind_experience': None,
        'post_study_mind_experience': None
    })()
    mock_d1.get_participant.return_value = mock_p
    mock_d1.get_participant_sessions.return_value = []

    mock_vs = AsyncMock()
    mock_emb = AsyncMock()

    builder = ContextBuilder(mock_d1, mock_vs, mock_emb, cache_ttl=3600)
    ctx1 = await builder.build("P001")
    ctx2 = await builder.build("P001")

    assert mock_d1.get_participant.call_count == 1
    assert ctx1 is ctx2
