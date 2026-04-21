"""locustfile.py – Load testing for Revarie LM v1.0."""

from locust import HttpUser, task, between
import random
import json

class RevarieUser(HttpUser):
    """Simulates a participant interacting with the chat system."""
    wait_time = between(3, 8)

    def on_start(self):
        """Initialize participant session."""
        self.participant_id = f"P{random.randint(1, 80):03d}"
        self.persona = random.choice(["samara", "artery"])
        self.session_id = None

    @task(3)
    def send_chat_message(self):
        """Send a chat message."""
        messages = [
            "Hello, how are you today?",
            "I'm feeling a bit stressed about work.",
            "Can you tell me more about this study?",
            "That's interesting, thank you.",
            "I need to take a break now.",
        ]
        payload = {
            "participant_id": self.participant_id,
            "message": random.choice(messages),
            "persona": self.persona,
        }
        with self.client.post(
            "/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def check_health(self):
        """Check health endpoint."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
