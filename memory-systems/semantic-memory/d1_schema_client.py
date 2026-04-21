"""
d1_schema_client.py
Semantic Memory – D1 Schema Client.
Provides a typed interface to Cloudflare D1 for structured semantic memory.
Handles participant state, session data, VAMS scores, and survey responses.

Theoretical foundations:
- Collins & Quillian (1969): Semantic memory as a network of facts.
- Tulving (1972): Distinction between episodic and semantic memory.
"""

import os
import json
import asyncio
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp


@dataclass
class Participant:
    """Structured representation of a study participant."""
    participant_id: str
    name: str
    email: str
    whatsapp: Optional[str]
    age: int
    gender: str
    country: str
    status: str
    study_group: str
    ai_type: str
    day_progress: int = 1
    has_onboarded: bool = False
    is_disqualified: bool = False
    last_login_date: Optional[str] = None
    pre_study_mind_experience: Optional[Dict] = None
    post_study_mind_experience: Optional[Dict] = None
    godspeed_results: Optional[Dict] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Participant":
        """Create a Participant from a D1 row dictionary."""
        return cls(
            participant_id=row["participant_id"],
            name=row["name"],
            email=row["email"],
            whatsapp=row.get("whatsapp"),
            age=row["age"],
            gender=row["gender"],
            country=row["country"],
            status=row["status"],
            study_group=row["study_group"],
            ai_type=row["ai_type"],
            day_progress=row.get("day_progress", 1),
            has_onboarded=bool(row.get("has_onboarded", 0)),
            is_disqualified=bool(row.get("is_disqualified", 0)),
            last_login_date=row.get("last_login_date"),
            pre_study_mind_experience=json.loads(row["pre_study_mind_experience"])
                if row.get("pre_study_mind_experience") else None,
            post_study_mind_experience=json.loads(row["post_study_mind_experience"])
                if row.get("post_study_mind_experience") else None,
            godspeed_results=json.loads(row["godspeed_results_json"])
                if row.get("godspeed_results_json") else None,
        )


@dataclass
class DailySession:
    """Structured representation of a single day's session."""
    session_id: int
    participant_id: str
    day_number: int
    session_date_ist: str
    status: str
    pre_vams: Dict[str, int] = field(default_factory=dict)
    post_vams: Dict[str, int] = field(default_factory=dict)
    mandatory_time_seconds: int = 600
    extra_time_seconds: int = 0
    dismissed: bool = False
    dismissal_reason: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "DailySession":
        """Create a DailySession from a D1 row dictionary."""
        pre_vams = {
            f"q{i}": row.get(f"pre_vams_q{i}")
            for i in range(1, 7) if row.get(f"pre_vams_q{i}") is not None
        }
        post_vams = {
            f"q{i}": row.get(f"post_vams_q{i}")
            for i in range(1, 7) if row.get(f"post_vams_q{i}") is not None
        }
        return cls(
            session_id=row["session_id"],
            participant_id=row["participant_id"],
            day_number=row["day_number"],
            session_date_ist=row["session_date_ist"],
            status=row["status"],
            pre_vams=pre_vams,
            post_vams=post_vams,
            mandatory_time_seconds=row.get("mandatory_time_seconds", 600),
            extra_time_seconds=row.get("extra_time_seconds", 0),
            dismissed=bool(row.get("dismissed", 0)),
            dismissal_reason=row.get("dismissal_reason"),
        )


class D1SchemaClient:
    """
    Client for Cloudflare D1 via Worker API.
    Handles semantic memory storage and retrieval.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        self.api_url = api_url or os.environ.get("VAULT_API_URL", "")
        self.api_key = api_key or os.environ.get("VAULT_API_KEY", "")
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries

        if not self.api_url:
            raise ValueError("VAULT_API_URL environment variable is required")
        if not self.api_key:
            raise ValueError("VAULT_API_KEY environment variable is required")

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        retries: int = 0,
    ) -> Dict[str, Any]:
        """Make authenticated request to Vault API."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    if method == "GET":
                        async with session.get(url, headers=headers) as resp:
                            return await self._handle_response(resp)
                    elif method == "POST":
                        async with session.post(url, headers=headers, json=data) as resp:
                            return await self._handle_response(resp)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("Max retries exceeded")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """Parse and validate API response."""
        text = await response.text()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON response: {text[:200]}")

        if response.status == 401:
            raise PermissionError("Invalid API key")
        if response.status == 404:
            return {"error": "Not found"}
        if response.status >= 400:
            error_msg = data.get("error", "Unknown error")
            raise RuntimeError(f"API error {response.status}: {error_msg}")

        return data

    async def verify_participant(self, identifier: str) -> Optional[Participant]:
        """
        Verify a participant by email, WhatsApp, or participant ID.
        Returns Participant if found, None otherwise.
        """
        try:
            data = await self._request(
                "GET",
                f"/auth/verify?id={identifier}"
            )
            if "error" in data:
                return None
            return Participant.from_row(data)
        except Exception:
            return None

    async def get_participant(self, participant_id: str) -> Optional[Participant]:
        """Retrieve a participant by their ID."""
        return await self.verify_participant(participant_id)

    async def start_session(
        self,
        participant_id: str,
        day_number: int,
        pre_vams: Dict[str, int],
    ) -> Optional[int]:
        """
        Start a new daily session.
        Returns the generated session_id.
        """
        payload = {
            "participant_id": participant_id,
            "day_number": day_number,
            "q1": pre_vams.get("q1", 50),
            "q2": pre_vams.get("q2", 50),
            "q3": pre_vams.get("q3", 50),
            "q4": pre_vams.get("q4", 50),
            "q5": pre_vams.get("q5", 50),
            "q6": pre_vams.get("q6", 50),
        }
        data = await self._request("POST", "/session/start", payload)
        return data.get("session_id")

    async def end_session(
        self,
        session_id: int,
        participant_id: str,
        post_vams: Dict[str, int],
        extra_time_seconds: int = 0,
        dismissed: bool = False,
        dismissal_reason: Optional[str] = None,
    ) -> bool:
        """
        End a daily session and record post-VAMS scores.
        """
        payload = {
            "session_id": session_id,
            "participant_id": participant_id,
            "q1": post_vams.get("q1", 50),
            "q2": post_vams.get("q2", 50),
            "q3": post_vams.get("q3", 50),
            "q4": post_vams.get("q4", 50),
            "q5": post_vams.get("q5", 50),
            "q6": post_vams.get("q6", 50),
            "extra_time_seconds": extra_time_seconds,
            "dismissed": dismissed,
            "dismissal_reason": dismissal_reason,
        }
        data = await self._request("POST", "/session/end", payload)
        return "error" not in data

    async def save_mind_study(
        self,
        participant_id: str,
        day: int,
        payload: Dict[str, Any],
        godspeed: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Save pre-study (day 1) or post-study (day 14) mind & experience survey.
        """
        req_payload = {
            "participant_id": participant_id,
            "day": day,
            "payload": payload,
        }
        if godspeed:
            req_payload["godspeed"] = godspeed
        data = await self._request("POST", "/survey/mind-study", req_payload)
        return "error" not in data

    async def get_participant_sessions(
        self,
        participant_id: str,
        limit: int = 14,
    ) -> List[DailySession]:
        """
        Retrieve recent sessions for a participant.
        Note: Requires a custom Worker endpoint; returns empty if not implemented.
        """
        try:
            data = await self._request(
                "GET",
                f"/participant/{participant_id}/sessions?limit={limit}"
            )
            if "error" in data or "sessions" not in data:
                return []
            return [DailySession.from_row(s) for s in data["sessions"]]
        except Exception:
            return []


# =============================================================================
# Tests (pytest with asyncio)
# =============================================================================
async def test_participant_from_row():
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


async def test_daily_session_from_row():
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


if __name__ == "__main__":
    async def main():
        client = D1SchemaClient(
            api_url="http://localhost:8787",
            api_key="test-key"
        )
        print(f"Client initialized with URL: {client.api_url}")

    asyncio.run(main())
