"""
variational_belief_updater.py
Active Inference – Variational Belief Updating.
Implements gradient-based variational inference to minimize free energy
with respect to the approximate posterior Q(s).
Based on Friston's Free Energy Principle.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class GenerativeModel:
    """
    Generative model P(o,s) = P(o|s) P(s).
    """
    likelihood: Dict[str, Dict[str, float]]   # P(o|s)
    prior: Dict[str, float]                    # P(s)
    
    def get_likelihood(self, state: str, obs: str) -> float:
        """Return P(obs | state) with a small epsilon to avoid zeros."""
        return self.likelihood.get(state, {}).get(obs, 1e-12)


class VariationalBeliefUpdater:
    """
    Maintains and updates a variational posterior Q(s) over hidden states.
    Uses gradient descent on variational free energy.
    """
    
    def __init__(
        self,
        model: GenerativeModel,
        initial_belief: Optional[Dict[str, float]] = None,
        learning_rate: float = 0.1,
    ):
        self.model = model
        self.states = list(model.prior.keys())
        
        if initial_belief is None:
            # Uniform initial belief
            n = len(self.states)
            self.q = {s: 1.0 / n for s in self.states}
        else:
            # Normalize provided initial belief
            total = sum(initial_belief.values())
            self.q = {s: initial_belief.get(s, 0.0) / total for s in self.states}
        
        self.learning_rate = learning_rate
    
    def compute_free_energy(self, observation: str) -> float:
        """
        Variational free energy for current Q(s):
        F = E_Q[ln Q(s) - ln P(o|s) - ln P(s)]
        """
        fe = 0.0
        for s, q_s in self.q.items():
            if q_s < 1e-12:
                continue
            log_q = np.log(q_s)
            log_prior = np.log(self.model.prior.get(s, 1e-12))
            log_lik = np.log(self.model.get_likelihood(s, observation))
            fe += q_s * (log_q - log_lik - log_prior)
        return fe
    
    def update_belief(self, observation: str, iterations: int = 10) -> None:
        """
        Perform gradient descent on the variational free energy
        to update Q(s) given a new observation.
        """
        for _ in range(iterations):
            grads = {}
            for s in self.states:
                q_s = self.q[s]
                if q_s < 1e-12:
                    grads[s] = 0.0
                    continue
                # Gradient of free energy w.r.t. q_s
                log_q = np.log(q_s)
                log_prior = np.log(self.model.prior.get(s, 1e-12))
                log_lik = np.log(self.model.get_likelihood(s, observation))
                grad = log_q + 1.0 - log_lik - log_prior
                grads[s] = grad
            
            # Apply gradient updates (in log-space for positivity)
            for s in self.states:
                self.q[s] = self.q[s] * np.exp(-self.learning_rate * grads[s])
            
            # Renormalize
            total = sum(self.q.values())
            if total > 0:
                for s in self.states:
                    self.q[s] /= total
    
    def exact_bayesian_update(self, observation: str) -> Dict[str, float]:
        """
        Perform exact Bayesian update: Q(s) ∝ P(o|s) P(s).
        Returns the updated posterior (without modifying internal state).
        """
        posterior = {}
        total = 0.0
        for s in self.states:
            prior = self.model.prior.get(s, 1e-12)
            likelihood = self.model.get_likelihood(s, observation)
            # BUG FIX: Removed `self.q[s] *` to prevent double-counting the prior.
            posterior[s] = prior * likelihood
            total += posterior[s]
        if total > 0:
            for s in posterior:
                posterior[s] /= total
        return posterior
    
    def set_belief(self, q: Dict[str, float]) -> None:
        """Directly set the belief state (automatically normalizes)."""
        total = sum(q.values())
        if total > 0:
            self.q = {s: q.get(s, 0.0) / total for s in self.states}
    
    def get_belief(self) -> Dict[str, float]:
        """Return a copy of the current belief state."""
        return self.q.copy()
    
    def entropy(self) -> float:
        """Compute the entropy of the current belief."""
        return -sum(q * np.log(q) for q in self.q.values() if q > 1e-12)


# =============================================================================
# Tests (pytest compatible)
# =============================================================================
def test_belief_initialization():
    model = GenerativeModel(
        likelihood={
            "light_on": {"bright": 0.9, "dim": 0.1},
            "light_off": {"bright": 0.1, "dim": 0.9},
        },
        prior={"light_on": 0.5, "light_off": 0.5},
    )
    updater = VariationalBeliefUpdater(model)
    assert abs(updater.get_belief()["light_on"] - 0.5) < 0.01


def test_exact_bayesian_update():
    model = GenerativeModel(
        likelihood={
            "light_on": {"bright": 0.9, "dim": 0.1},
            "light_off": {"bright": 0.1, "dim": 0.9},
        },
        prior={"light_on": 0.5, "light_off": 0.5},
    )
    updater = VariationalBeliefUpdater(model)
    posterior = updater.exact_bayesian_update("bright")
    assert posterior["light_on"] > posterior["light_off"]


def test_free_energy_decreases():
    model = GenerativeModel(
        likelihood={
            "light_on": {"bright": 0.9, "dim": 0.1},
            "light_off": {"bright": 0.1, "dim": 0.9},
        },
        prior={"light_on": 0.5, "light_off": 0.5},
    )
    updater = VariationalBeliefUpdater(model)
    obs = "bright"
    fe_before = updater.compute_free_energy(obs)
    updater.update_belief(obs, iterations=20)
    fe_after = updater.compute_free_energy(obs)
    assert fe_after < fe_before
