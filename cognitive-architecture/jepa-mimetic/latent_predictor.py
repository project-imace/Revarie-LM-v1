"""
latent_predictor.py
JEPA-Mimetic – Latent Predictor.
Implements a self-supervised predictive world model in latent space.
Inspired by Joint Embedding Predictive Architectures (JEPA) and
the Free Energy Principle. Learns to predict future latent states
from current observations and actions.

Theoretical foundations:
- LeCun (2022): A Path Towards Autonomous Machine Intelligence (JEPA).
- Friston (2010): The free-energy principle.
- Oord, Li, & Vinyals (2018): Representation Learning with Contrastive Predictive Coding.
"""

import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass, field
from collections import deque
import random
import torch
import torch.nn as nn
import torch.optim as optim


@dataclass
class LatentState:
    """A point in the agent's learned latent space."""
    vector: np.ndarray
    timestamp: float = field(default_factory=lambda: np.datetime64('now').astype(float))
    surprisal: float = 0.0


class LatentEncoder(nn.Module):
    """Encodes observations into a compact latent representation."""
    def __init__(self, input_dim: int, latent_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim),
            nn.LayerNorm(latent_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class LatentPredictor(nn.Module):
    """Predicts future latent state from current latent and action."""
    def __init__(self, latent_dim: int, action_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )

    def forward(self, z: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([z, a], dim=-1))


class JEPAMimeticAgent:
    """
    A self-supervised agent that learns a predictive world model in latent space.
    Uses a Joint Embedding Predictive Architecture (JEPA) style objective:
    minimize prediction error in latent space while preventing collapse.
    """
    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        latent_dim: int = 32,
        hidden_dim: int = 128,
        learning_rate: float = 1e-3,
        memory_size: int = 10000,
        batch_size: int = 64,
        tau: float = 0.005  # Target network soft-update rate
    ):
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.latent_dim = latent_dim
        self.batch_size = batch_size
        self.tau = tau

        # Networks
        self.encoder = LatentEncoder(obs_dim, latent_dim, hidden_dim)
        self.target_encoder = LatentEncoder(obs_dim, latent_dim, hidden_dim)
        self.predictor = LatentPredictor(latent_dim, action_dim, hidden_dim)

        # Initialize target encoder with same weights
        self.target_encoder.load_state_dict(self.encoder.state_dict())
        for param in self.target_encoder.parameters():
            param.requires_grad = False

        self.optimizer = optim.Adam(
            list(self.encoder.parameters()) + list(self.predictor.parameters()),
            lr=learning_rate
        )

        # Replay buffer
        self.memory = deque(maxlen=memory_size)
        self.step_counter = 0

        # Training mode
        self.train()

    def train(self):
        self.encoder.train()
        self.predictor.train()

    def eval(self):
        self.encoder.eval()
        self.predictor.eval()

    def encode(self, obs: np.ndarray) -> LatentState:
        """Encode an observation into latent state."""
        with torch.no_grad():
            obs_t = torch.FloatTensor(obs).unsqueeze(0)
            z = self.encoder(obs_t).squeeze(0).numpy()
        return LatentState(vector=z)

    def predict_next(self, z: np.ndarray, action: int) -> np.ndarray:
        """Predict next latent state from current latent and action."""
        with torch.no_grad():
            z_t = torch.FloatTensor(z).unsqueeze(0)
            a_t = torch.zeros(1, self.action_dim)
            a_t[0, action] = 1.0
            z_next_pred = self.predictor(z_t, a_t).squeeze(0).numpy()
        return z_next_pred

    def store_transition(
        self, obs: np.ndarray, action: int, next_obs: np.ndarray, reward: float = 0.0
    ):
        """Store a transition in the replay buffer."""
        self.memory.append((obs, action, next_obs, reward))

    def update_target_encoder(self):
        """Soft update of target encoder."""
        for target_param, param in zip(
            self.target_encoder.parameters(), self.encoder.parameters()
        ):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def compute_loss(self, batch: List[Tuple]) -> torch.Tensor:
        """Compute JEPA-style predictive loss."""
        obs_batch = torch.FloatTensor(np.array([b[0] for b in batch]))
        actions = torch.LongTensor([b[1] for b in batch])
        next_obs_batch = torch.FloatTensor(np.array([b[2] for b in batch]))

        # One-hot encode actions
        action_onehot = torch.zeros(len(batch), self.action_dim)
        action_onehot[range(len(batch)), actions] = 1.0

        # Encode current observations
        z = self.encoder(obs_batch)

        # Encode next observations with target encoder (no gradient)
        with torch.no_grad():
            z_next_target = self.target_encoder(next_obs_batch)

        # Predict next latent from current latent and action
        z_next_pred = self.predictor(z, action_onehot)

        # L2 loss in latent space
        loss = nn.functional.mse_loss(z_next_pred, z_next_target)

        # FIXED: Use hinge loss for variance regularization to prevent weight explosion
        z_std = torch.sqrt(z.var(dim=0) + 1e-4) 
        std_loss = torch.mean(torch.relu(1.0 - z_std))
        loss = loss + 0.1 * std_loss

        return loss

    def learn(self) -> Optional[float]:
        """Perform one learning step."""
        if len(self.memory) < self.batch_size:
            return None

        # FIXED: Use random.sample for O(1) buffer retrieval
        batch_data = random.sample(self.memory, self.batch_size)

        self.optimizer.zero_grad()
        loss = self.compute_loss(batch_data)
        loss.backward()
        self.optimizer.step()

        self.update_target_encoder()
        self.step_counter += 1

        return loss.item()

    def get_latent_trajectory(self, n_steps: int = 10) -> List[LatentState]:
        """Return recent latent states (for visualization)."""
        if len(self.memory) == 0:
            return []
        recent = list(self.memory)[-min(n_steps, len(self.memory)):]
        states = []
        for obs, _, _, _ in recent:
            states.append(self.encode(obs))
        return states


# =============================================================================
# Tests (pytest compatible)
# =============================================================================
def test_latent_encoder_shape():
    encoder = LatentEncoder(input_dim=10, latent_dim=4)
    x = torch.randn(3, 10)
    z = encoder(x)
    assert z.shape == (3, 4)


def test_latent_predictor_shape():
    predictor = LatentPredictor(latent_dim=4, action_dim=2)
    z = torch.randn(3, 4)
    a = torch.randn(3, 2)
    z_pred = predictor(z, a)
    assert z_pred.shape == (3, 4)


def test_jepa_agent_initialization():
    agent = JEPAMimeticAgent(obs_dim=10, action_dim=2, latent_dim=8)
    assert agent.obs_dim == 10
    assert agent.action_dim == 2
    assert agent.latent_dim == 8


def test_encode_observation():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4)
    agent.eval()
    obs = np.random.randn(5)
    state = agent.encode(obs)
    assert state.vector.shape == (4,)


def test_store_and_learn():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4, batch_size=4)
    # Populate memory
    for _ in range(10):
        obs = np.random.randn(5)
        next_obs = np.random.randn(5)
        agent.store_transition(obs, 0, next_obs)
    loss = agent.learn()
    assert loss is not None


def test_predict_next():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4)
    agent.eval()
    z = np.random.randn(4)
    z_next = agent.predict_next(z, 0)
    assert z_next.shape == (4,)
