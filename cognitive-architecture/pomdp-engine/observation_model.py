"""
observation_model.py
POMDP Engine – Observation Model.
Defines the observation likelihood P(o | s) in a Partially Observable
Markov Decision Process. Supports discrete observations with stochastic
sampling and Bayesian inversion.

Theoretical foundations:
- Kaelbling, Littman, & Cassandra (1998): POMDP planning.
- Rabiner (1989): Hidden Markov Models.
"""

import numpy as np
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ObservationMatrix:
    """
    Observation likelihood matrix P(o | s).
    Matrix of shape (n_states, n_observations) where each row sums to 1.
    """
    data: np.ndarray
    observation_names: Optional[List[str]] = None
    state_names: Optional[List[str]] = None

    def __post_init__(self):
        """Normalize rows and validate shape."""
        if self.data.ndim != 2:
            raise ValueError(f"Expected 2D matrix, got shape {self.data.shape}")
        # Ensure rows sum to 1
        row_sums = self.data.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1.0, row_sums)
        self.data = self.data / row_sums

        self.n_states, self.n_obs = self.data.shape

        if self.observation_names is None:
            self.observation_names = [f"o{i}" for i in range(self.n_obs)]
        if self.state_names is None:
            self.state_names = [f"s{i}" for i in range(self.n_states)]

    def probability(self, state: Union[int, str], observation: Union[int, str]) -> float:
        """Return P(observation | state)."""
        s_idx = self._state_index(state)
        o_idx = self._obs_index(observation)
        return float(self.data[s_idx, o_idx])

    def sample(self, state: Union[int, str], rng: Optional[np.random.Generator] = None) -> str:
        """Sample an observation given a state."""
        if rng is None:
            rng = np.random.default_rng()
        s_idx = self._state_index(state)
        probs = self.data[s_idx, :]
        o_idx = rng.choice(self.n_obs, p=probs)
        return self.observation_names[o_idx]

    def likelihood_vector(self, observation: Union[int, str]) -> np.ndarray:
        """Return column vector of P(observation | state) for all states."""
        o_idx = self._obs_index(observation)
        return self.data[:, o_idx].copy()

    def most_likely_state(self, observation: Union[int, str]) -> str:
        """Return the state that maximizes P(observation | state)."""
        o_idx = self._obs_index(observation)
        s_idx = np.argmax(self.data[:, o_idx])
        return self.state_names[s_idx]

    def _state_index(self, state: Union[int, str]) -> int:
        if isinstance(state, int):
            if 0 <= state < self.n_states:
                return state
            raise IndexError(f"State index {state} out of bounds [0, {self.n_states})")
        if state in self.state_names:
            return self.state_names.index(state)
        raise ValueError(f"Unknown state: {state}")

    def _obs_index(self, obs: Union[int, str]) -> int:
        if isinstance(obs, int):
            if 0 <= obs < self.n_obs:
                return obs
            raise IndexError(f"Observation index {obs} out of bounds [0, {self.n_obs})")
        if obs in self.observation_names:
            return self.observation_names.index(obs)
        raise ValueError(f"Unknown observation: {obs}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "data": self.data.tolist(),
            "observation_names": self.observation_names,
            "state_names": self.state_names,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ObservationMatrix":
        """Deserialize from dictionary."""
        return cls(
            data=np.array(d["data"]),
            observation_names=d.get("observation_names"),
            state_names=d.get("state_names"),
        )

    @classmethod
    def uniform(cls, n_states: int, n_observations: int,
                state_names: Optional[List[str]] = None,
                obs_names: Optional[List[str]] = None) -> "ObservationMatrix":
        """Create a uniform observation model."""
        data = np.ones((n_states, n_observations)) / n_observations
        return cls(data=data, state_names=state_names, observation_names=obs_names)

    @classmethod
    def identity(cls, n_states: int,
                 state_names: Optional[List[str]] = None) -> "ObservationMatrix":
        """Create a deterministic identity model (state == observation)."""
        data = np.eye(n_states)
        obs_names = state_names if state_names else [f"o{i}" for i in range(n_states)]
        return cls(data=data, state_names=state_names, observation_names=obs_names)


# =============================================================================
# Tests (pytest compatible)
# =============================================================================
def test_observation_matrix_creation():
    data = np.array([[0.9, 0.1], [0.2, 0.8]])
    om = ObservationMatrix(data)
    assert om.n_states == 2
    assert om.n_obs == 2
    assert om.state_names == ["s0", "s1"]
    assert om.observation_names == ["o0", "o1"]


def test_probability_access():
    data = np.array([[0.7, 0.3], [0.4, 0.6]])
    om = ObservationMatrix(data, state_names=["A", "B"], observation_names=["X", "Y"])
    assert abs(om.probability("A", "X") - 0.7) < 1e-9
    assert abs(om.probability(1, 0) - 0.4) < 1e-9


def test_sampling():
    data = np.array([[1.0, 0.0], [0.0, 1.0]])
    om = ObservationMatrix(data)
    rng = np.random.default_rng(42)
    assert om.sample(0, rng) == "o0"
    assert om.sample(1, rng) == "o1"


def test_likelihood_vector():
    data = np.array([[0.9, 0.1], [0.1, 0.9]])
    om = ObservationMatrix(data)
    vec = om.likelihood_vector(0)
    assert vec.shape == (2,)
    assert abs(vec[0] - 0.9) < 1e-9
    assert abs(vec[1] - 0.1) < 1e-9


def test_most_likely_state():
    data = np.array([[0.2, 0.8], [0.9, 0.1]])
    om = ObservationMatrix(data, state_names=["s0", "s1"])
    assert om.most_likely_state(0) == "s1"  # for o0, s1 has 0.9
    assert om.most_likely_state(1) == "s0"  # for o1, s0 has 0.8


def test_uniform_creation():
    om = ObservationMatrix.uniform(3, 4)
    assert om.n_states == 3
    assert om.n_obs == 4
    assert np.allclose(om.data.sum(axis=1), 1.0)


def test_identity_creation():
    om = ObservationMatrix.identity(3, state_names=["A", "B", "C"])
    assert om.n_states == 3
    assert om.n_obs == 3
    assert om.observation_names == ["A", "B", "C"]
    for i in range(3):
        assert om.probability(i, i) == 1.0


def test_serialization():
    data = np.array([[0.5, 0.5], [0.3, 0.7]])
    om = ObservationMatrix(data, state_names=["on", "off"], observation_names=["bright", "dim"])
    d = om.to_dict()
    om2 = ObservationMatrix.from_dict(d)
    assert np.allclose(om.data, om2.data)
    assert om.state_names == om2.state_names
    assert om.observation_names == om2.observation_names


def test_normalization_on_creation():
    data = np.array([[2.0, 2.0], [1.0, 3.0]])
    om = ObservationMatrix(data)
    assert np.allclose(om.data[0, :], [0.5, 0.5])
    assert np.allclose(om.data[1, :], [0.25, 0.75])
