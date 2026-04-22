"""conftest.py – Shared fixtures for integration tests."""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_d1_client():
    """Mock D1 client for testing."""
    client = AsyncMock()
    mock_participant = type('MockParticipant', (), {
        'participant_id': "P001",
        'name': "Test User",
        'study_group': "A",
        'ai_type': "Relational AI Samara",
        'day_progress': 3,
        'has_onboarded': True,
        'is_disqualified': False,
        'age': 25,
        'gender': 'Female',
        'country': 'USA',
        'status': 'active',
        'pre_study_mind_experience': None,
        'post_study_mind_experience': None
    })()
    client.get_participant.return_value = mock_participant
    client.get_participant_sessions.return_value = []
    return client

@pytest.fixture
def mock_vector_store():
    """Mock Vectorize client for testing."""
    client = AsyncMock()
    client.query_by_participant.return_value = []
    return client

@pytest.fixture
def mock_embedding_generator():
    """Mock embedding generator for testing."""
    gen = AsyncMock()
    gen.embed_single.return_value = [0.1] * 1536
    return gen

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
