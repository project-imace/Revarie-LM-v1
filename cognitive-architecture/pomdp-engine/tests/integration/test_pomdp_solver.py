"""
test_pomdp_solver.py
Integration test for the full POMDP solver pipeline.
Simulates the classic Tiger problem: an agent must decide whether to
listen for the tiger or open a door, updating beliefs after each observation.

Theoretical foundation:
- Cassandra, Kaelbling, & Littman (1994): Acting optimally in partially observable stochastic domains.
- Hauskrecht (2000): Value-function approximations for partially observable Markov decision processes.
"""

import sys
import os
import importlib.util
import numpy as np
from typing import List, Dict, Tuple, Optional

# Dynamically load ObservationMatrix from parent module
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "observation_model.py")
)
spec = importlib.util.spec_from_file_location("observation_model", module_path)
obs_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obs_module)
ObservationMatrix = obs_module.ObservationMatrix


class TigerPOMDP:
    """
    Classic Tiger POMDP environment.
    States: tiger-left, tiger-right
    Actions: listen, open-left, open-right
    Observations: hear-left, hear-right
    """
    def __init__(self):
        self.states = ["tiger-left", "tiger-right"]
        self.actions = ["listen", "open-left", "open-right"]
        self.observations = ["hear-left", "hear-right"]

        # Observation model: P(o | s)
        obs_data = np.array([
            [0.85, 0.15],  # tiger-left:  hear-left=0.85, hear-right=0.15
            [0.15, 0.85]   # tiger-right: hear-left=0.15, hear-right=0.85
        ])
        self.observation_model = ObservationMatrix(
            obs_data,
            state_names=self.states,
            observation_names=self.observations
        )

        # Transition model: P(s' | s, a)
        # For 'listen', state remains unchanged.
        # For 'open-left' or 'open-right', the problem resets: tiger randomly placed.
        self.transitions = {
            "listen": np.eye(2),
            "open-left": np.full((2, 2), 0.5),
            "open-right": np.full((2, 2), 0.5),
        }

        # Rewards: R(s, a)
        self.rewards = {
            ("tiger-left", "listen"): -1,
            ("tiger-right", "listen"): -1,
            ("tiger-left", "open-left"): -100,
            ("tiger-right", "open-left"): 10,
            ("tiger-left", "open-right"): 10,
            ("tiger-right", "open-right"): -100,
        }

        self.discount = 0.95

    def transition_matrix(self, action: str) -> np.ndarray:
        return self.transitions[action]

    def reward_vector(self) -> np.ndarray:
        """Return vector of expected immediate rewards for each state."""
        r = np.zeros(len(self.states))
        for i, s in enumerate(self.states):
            r[i] = self.rewards.get((s, "listen"), 0)  # placeholder
        return r


class BeliefState:
    """Simple belief state (probability distribution over states)."""
    def __init__(self, probabilities: np.ndarray):
        self.probs = probabilities / probabilities.sum()

    def update(self, action: str, observation: str, pomdp: TigerPOMDP) -> "BeliefState":
        """Bayesian belief update."""
        obs_idx = pomdp.observations.index(observation)
        obs_likelihood = pomdp.observation_model.likelihood_vector(obs_idx)
        trans = pomdp.transition_matrix(action)
        new_probs = obs_likelihood * (trans.T @ self.probs)
        return BeliefState(new_probs)

    def sample_state(self) -> str:
        return np.random.choice(["tiger-left", "tiger-right"], p=self.probs)


def value_iteration(pomdp: TigerPOMDP, epsilon: float = 1e-3, max_iter: int = 100) -> Dict[str, np.ndarray]:
    """
    Solve POMDP using Fast Informed Bound (FIB) approximation.
    Returns a dictionary mapping action to a single alpha-vector.
    """
    n_states = len(pomdp.states)
    
    # Initialize alpha-vectors with optimistic values
    alpha_vectors = {a: np.full(n_states, 10.0) for a in pomdp.actions}
    
    for _ in range(max_iter):
        new_alphas = {}
        for action in pomdp.actions:
            trans = pomdp.transition_matrix(action)
            immediate = np.array([pomdp.rewards.get((s, action), 0) for s in pomdp.states])
            
            expected_future = np.zeros(n_states)
            for o_idx, obs in enumerate(pomdp.observations):
                obs_prob = pomdp.observation_model.likelihood_vector(o_idx)
                
                action_values = []
                for next_action in pomdp.actions:
                    next_alpha = alpha_vectors[next_action]
                    # Compute sum_{s'} T(s'|s,a) * O(o|s') * alpha_a'(s')
                    val_s = trans @ (obs_prob * next_alpha)
                    action_values.append(val_s)
                    
                # Maximize over next actions FOR EACH state independently
                best_for_o = np.max(action_values, axis=0)
                expected_future += best_for_o
                
            new_alphas[action] = immediate + pomdp.discount * expected_future

        # Check convergence
        max_diff = max(
            np.max(np.abs(new_alphas[a] - alpha_vectors[a])) for a in pomdp.actions
        )
        alpha_vectors = new_alphas
        if max_diff < epsilon:
            break

    return alpha_vectors


def test_tiger_pomdp_simulation():
    """Run a full simulation of the Tiger POMDP."""
    np.random.seed(42)
    pomdp = TigerPOMDP()

    # Solve using value iteration
    alpha_vectors = value_iteration(pomdp)

    # Initial belief: 50/50
    belief = BeliefState(np.array([0.5, 0.5]))

    # Simulate a few steps
    history = []
    for step in range(5):
        # Choose optimal action according to current belief
        best_action = None
        best_value = -np.inf
        for action in pomdp.actions:
            value = np.dot(alpha_vectors[action], belief.probs)
            if value > best_value:
                best_value = value
                best_action = action

        # Sample true state and observation
        true_state = belief.sample_state()
        obs = pomdp.observation_model.sample(true_state)
        reward = pomdp.rewards.get((true_state, best_action), 0)

        history.append({
            "step": step,
            "belief": belief.probs.tolist(),
            "action": best_action,
            "observation": obs,
            "reward": reward,
        })

        # Update belief
        belief = belief.update(best_action, obs, pomdp)

    # Assertions: initial steps should prefer "listen"
    assert history[0]["action"] == "listen", "First action should be listen to gather information"
    assert history[1]["action"] == "listen", "Second action should also be listen"

    # After two listens, belief should become more certain
    final_belief = np.array(history[-1]["belief"])
    assert max(final_belief) > 0.7, "Belief should become concentrated after observations"

    print("Tiger POMDP simulation passed.")
    for h in history:
        print(f"Step {h['step']}: belief={h['belief']}, action={h['action']}, obs={h['observation']}, reward={h['reward']}")


if __name__ == "__main__":
    test_tiger_pomdp_simulation()
