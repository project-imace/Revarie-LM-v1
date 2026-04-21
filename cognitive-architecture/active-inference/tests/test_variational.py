"""Unit tests for VariationalBeliefUpdater."""

import sys
import os
import importlib.util

import pytest

# Dynamically load the module from its actual filesystem path (handles hyphens)
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "variational_belief_updater.py")
)
spec = importlib.util.spec_from_file_location("variational_belief_updater", module_path)
vbu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vbu)

VariationalBeliefUpdater = vbu.VariationalBeliefUpdater
GenerativeModel = vbu.GenerativeModel


def build_simple_model():
    """Build a simple generative model for testing."""
    likelihood = {
        "light_on": {"bright": 0.9, "dim": 0.1},
        "light_off": {"bright": 0.1, "dim": 0.9},
    }
    prior = {"light_on": 0.5, "light_off": 0.5}
    return GenerativeModel(likelihood=likelihood, prior=prior)


def test_belief_initialization():
    model = build_simple_model()
    updater = VariationalBeliefUpdater(model)
    belief = updater.get_belief()
    assert abs(belief["light_on"] - 0.5) < 0.01
    assert abs(belief["light_off"] - 0.5) < 0.01


def test_exact_bayesian_update():
    model = build_simple_model()
    updater = VariationalBeliefUpdater(model)
    posterior = updater.exact_bayesian_update("bright")
    # P(light_on | bright) should be > P(light_off | bright)
    assert posterior["light_on"] > posterior["light_off"]
    # The internal belief should not have changed yet
    belief = updater.get_belief()
    assert abs(belief["light_on"] - 0.5) < 0.01


def test_free_energy_decreases_with_update():
    model = build_simple_model()
    updater = VariationalBeliefUpdater(model, learning_rate=0.1)
    obs = "bright"
    fe_before = updater.compute_free_energy(obs)
    updater.update_belief(obs, iterations=30)
    fe_after = updater.compute_free_energy(obs)
    assert fe_after < fe_before


def test_update_belief_changes_state():
    model = build_simple_model()
    updater = VariationalBeliefUpdater(model, learning_rate=0.1)
    updater.update_belief("bright", iterations=20)
    belief = updater.get_belief()
    # After seeing "bright", light_on probability should increase
    assert belief["light_on"] > belief["light_off"]


def test_set_belief():
    model = build_simple_model()
    updater = VariationalBeliefUpdater(model)
    updater.set_belief({"light_on": 0.8, "light_off": 0.2})
    belief = updater.get_belief()
    assert abs(belief["light_on"] - 0.8) < 0.01
    assert abs(belief["light_off"] - 0.2) < 0.01


def test_entropy():
    model = build_simple_model()
    updater = VariationalBeliefUpdater(model)
    entropy_uniform = updater.entropy()
    updater.set_belief({"light_on": 0.99, "light_off": 0.01})
    entropy_peaked = updater.entropy()
    # Entropy should be lower when distribution is peaked
    assert entropy_peaked < entropy_uniform


def test_initial_belief_custom():
    model = build_simple_model()
    updater = VariationalBeliefUpdater(
        model, initial_belief={"light_on": 0.7, "light_off": 0.3}
    )
    belief = updater.get_belief()
    assert abs(belief["light_on"] - 0.7) < 0.01
    assert abs(belief["light_off"] - 0.3) < 0.01
