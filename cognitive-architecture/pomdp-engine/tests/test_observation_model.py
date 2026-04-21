"""Unit tests for Observation Model."""

import sys
import os
import importlib.util

import pytest
import numpy as np

# Dynamically load the module (handles hyphenated directory names)
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "observation_model.py")
)
spec = importlib.util.spec_from_file_location("observation_model", module_path)
obs_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obs_module)

ObservationMatrix = obs_module.ObservationMatrix


def test_observation_matrix_creation():
    data = np.array([[0.9, 0.1], [0.2, 0.8]])
    om = ObservationMatrix(data)
    assert om.n_states == 2
    assert om.n_obs == 2
    assert om.state_names == ["s0", "s1"]
    assert om.observation_names == ["o0", "o1"]


def test_probability_access_by_index():
    data = np.array([[0.7, 0.3], [0.4, 0.6]])
    om = ObservationMatrix(data)
    assert abs(om.probability(0, 0) - 0.7) < 1e-9
    assert abs(om.probability(1, 0) - 0.4) < 1e-9


def test_probability_access_by_name():
    data = np.array([[0.7, 0.3], [0.4, 0.6]])
    om = ObservationMatrix(
        data, state_names=["A", "B"], observation_names=["X", "Y"]
    )
    assert abs(om.probability("A", "X") - 0.7) < 1e-9
    assert abs(om.probability("B", "Y") - 0.6) < 1e-9


def test_sampling_deterministic():
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
    om = ObservationMatrix(
        data, state_names=["on", "off"], observation_names=["bright", "dim"]
    )
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


def test_invalid_state_name():
    data = np.array([[0.5, 0.5], [0.5, 0.5]])
    om = ObservationMatrix(data, state_names=["A", "B"])
    with pytest.raises(ValueError, match="Unknown state: C"):
        om.probability("C", "o0")


def test_invalid_obs_name():
    data = np.array([[0.5, 0.5], [0.5, 0.5]])
    om = ObservationMatrix(data, observation_names=["X", "Y"])
    with pytest.raises(ValueError, match="Unknown observation: Z"):
        om.probability(0, "Z")
