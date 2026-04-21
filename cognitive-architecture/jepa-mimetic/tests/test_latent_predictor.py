"""
test_latent_predictor.py
Unit tests for JEPA-Mimetic Latent Predictor.
"""

import sys
import os
import importlib.util

import pytest
import numpy as np
import torch

# Dynamically load the module (handles hyphenated directory names)
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "latent_predictor.py")
)
spec = importlib.util.spec_from_file_location("latent_predictor", module_path)
lp_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lp_module)

JEPAMimeticAgent = lp_module.JEPAMimeticAgent
LatentEncoder = lp_module.LatentEncoder
LatentPredictor = lp_module.LatentPredictor
LatentState = lp_module.LatentState


def test_latent_encoder_output_shape():
    encoder = LatentEncoder(input_dim=10, latent_dim=4, hidden_dim=32)
    x = torch.randn(8, 10)
    z = encoder(x)
    assert z.shape == (8, 4)


def test_latent_predictor_output_shape():
    predictor = LatentPredictor(latent_dim=4, action_dim=2, hidden_dim=32)
    z = torch.randn(8, 4)
    a = torch.randn(8, 2)
    z_pred = predictor(z, a)
    assert z_pred.shape == (8, 4)


def test_jepa_agent_initialization():
    agent = JEPAMimeticAgent(obs_dim=10, action_dim=2, latent_dim=8)
    assert agent.obs_dim == 10
    assert agent.action_dim == 2
    assert agent.latent_dim == 8
    assert agent.batch_size == 64


def test_encode_observation():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4)
    agent.eval()
    obs = np.random.randn(5).astype(np.float32)
    state = agent.encode(obs)
    assert isinstance(state, LatentState)
    assert state.vector.shape == (4,)


def test_predict_next_shape():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4)
    agent.eval()
    z = np.random.randn(4).astype(np.float32)
    z_next = agent.predict_next(z, 0)
    assert z_next.shape == (4,)


def test_store_and_learn():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4, batch_size=4)
    for _ in range(10):
        obs = np.random.randn(5).astype(np.float32)
        next_obs = np.random.randn(5).astype(np.float32)
        agent.store_transition(obs, 0, next_obs)
    loss = agent.learn()
    assert loss is not None
    assert loss > 0


def test_target_encoder_update():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4, tau=1.0)
    # With tau=1.0, target encoder should exactly match encoder after update
    agent.update_target_encoder()
    for p1, p2 in zip(agent.encoder.parameters(), agent.target_encoder.parameters()):
        assert torch.allclose(p1, p2)


def test_train_eval_modes():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4)
    agent.eval()
    assert not agent.encoder.training
    assert not agent.predictor.training
    agent.train()
    assert agent.encoder.training
    assert agent.predictor.training


def test_memory_overflow():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4, memory_size=5)
    for i in range(10):
        obs = np.random.randn(5).astype(np.float32)
        next_obs = np.random.randn(5).astype(np.float32)
        agent.store_transition(obs, i % 2, next_obs)
    assert len(agent.memory) == 5


def test_get_latent_trajectory_empty():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4)
    trajectory = agent.get_latent_trajectory()
    assert trajectory == []


def test_get_latent_trajectory():
    agent = JEPAMimeticAgent(obs_dim=5, action_dim=2, latent_dim=4)
    agent.eval()
    for _ in range(5):
        obs = np.random.randn(5).astype(np.float32)
        agent.store_transition(obs, 0, obs)
    trajectory = agent.get_latent_trajectory(n_steps=3)
    assert len(trajectory) == 3
    assert all(isinstance(s, LatentState) for s in trajectory)
