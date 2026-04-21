"""
test_d1_client.py
Unit tests for D1SchemaClient (using mocks).
"""

import sys
import os
import importlib.util
import asyncio
from unittest.mock import AsyncMock, patch
import pytest

module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "d1_schema_client.py"))
spec = importlib.util.spec_from_file_location("d1_schema_client", module_path)
d1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d1)

D1SchemaClient = d1.D1SchemaClient
Participant = d1.Participant
DailySession = d1.DailySession


def test_participant_from_row():
    row = {
        "participant_id": "P001",
        "name": "Test User",
        "email": "test@example.com",
        "whatsapp": "1234567890",
        "age": 25,
        "gender": "Female",
        "country": "India",
        "status": "University",
        "study_group": "A",
        "ai_type": "Relational AI Samara",
        "day_progress": 3,
        "has_onboarded": 1,
        "is_disqualified": 0,
        "last_login_date": "2026-04-20T06:00:00",
        "pre_study_mind_experience": '{"baseline": "data"}',
        "post_study_mind_experience": None,
        "godspeed_results_json": None,
    }
    p = Participant.from_row(row)
    assert p.participant_id == "P001"
    assert p.name == "Test User"
    assert p.study_group == "A"
    assert p.day_progress == 3
    assert p.has_onboarded is True
    assert p.pre_study_mind_experience == {"baseline": "data"}


def test_daily_session_from_row():
    row = {
        "session_id": 42,
        "participant_id": "P001",
        "day_number": 2,
        "session_date_ist": "2026-04-20",
        "status": "Completed",
        "pre_vams_q1": 65,
        "pre_vams_q2": 30,
        "post_vams_q1": 45,
        "post_vams_q2": 60,
        "mandatory_time_seconds": 600,
        "extra_time_seconds": 120,
        "dismissed": 0,
    }
    s = DailySession.from_row(row)
    assert s.session_id == 42
    assert s.day_number == 2
    assert s.pre_vams == {"q1": 65, "q2": 30}
    assert s.post_vams == {"q1": 45, "q2": 60}
    assert s.extra_time_seconds == 120


@pytest.mark.asyncio
async def test_verify_participant():
    client = D1SchemaClient(api_url="http://localhost", api_key="test-key")
    mock_data = {
        "participant_id": "P001",
        "name": "Test User",
        "email": "test@example.com",
        "age": 25,
        "gender": "Female",
        "country": "India",
        "status": "University",
        "study_group": "A",
        "ai_type": "Relational AI Samara",
    }
    with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_data
        p = await client.verify_participant("test@example.com")
        assert p is not None
        assert p.participant_id == "P001"


@pytest.mark.asyncio
async def test_start_session():
    client = D1SchemaClient(api_url="http://localhost", api_key="test-key")
    with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"session_id": 123}
        sid = await client.start_session("P001", 1, {"q1": 50, "q2": 50, "q3": 50, "q4": 50, "q5": 50, "q6": 50})
        assert sid == 123


@pytest.mark.asyncio
async def test_end_session():
    client = D1SchemaClient(api_url="http://localhost", api_key="test-key")
    with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"message": "Finished"}
        ok = await client.end_session(123, "P001", {"q1": 40, "q2": 50, "q3": 60, "q4": 50, "q5": 40, "q6": 30})
        assert ok is True


@pytest.mark.asyncio
async def test_save_mind_study():
    client = D1SchemaClient(api_url="http://localhost", api_key="test-key")
    with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"message": "Saved"}
        ok = await client.save_mind_study("P001", 1, {"q1": "answer"})
        assert ok is True
