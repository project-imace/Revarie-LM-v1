//! transition_model.rs
//! POMDP Engine – Transition Model.
//! Defines the state transition dynamics P(s' | s, a) in a Partially Observable
//! Markov Decision Process. Provides stochastic sampling, matrix representation,
//! and validation utilities for Markov chains.
//!
//! Theoretical foundations:
//! - Sutton & Barto (2018): Reinforcement Learning: An Introduction.
//! - Kaelbling, Littman, & Cassandra (1998): POMDP planning.

use std::fmt;
use std::collections::HashMap;
use rand::Rng;
use rand::distributions::{Distribution, WeightedIndex};

/// Transition matrix for a single action.
/// `matrix[s][s_prime]` = P(s' | s, a)
#[derive(Debug, Clone)]
pub struct TransitionMatrix {
    data: Vec<Vec<f64>>,
    n_states: usize,
}

impl TransitionMatrix {
    /// Create a new transition matrix from raw data.
    /// Automatically normalizes each row to sum to 1.0.
    pub fn new(mut data: Vec<Vec<f64>>) -> Result<Self, String> {
        if data.is_empty() {
            return Err("Transition matrix cannot be empty".to_string());
        }
        let n_states = data.len();
        for row in &data {
            if row.len() != n_states {
                return Err(format!(
                    "Matrix must be square: expected {} columns, got {}",
                    n_states, row.len()
                ));
            }
        }
        // Normalize each row
        for row in &mut data {
            let sum: f64 = row.iter().sum();
            if sum > 0.0 {
                for p in row.iter_mut() {
                    *p /= sum;
                }
            } else {
                // Uniform fallback for zero rows
                let uniform = 1.0 / n_states as f64;
                for p in row.iter_mut() {
                    *p = uniform;
                }
            }
        }
        Ok(Self { data, n_states })
    }

    /// Create an identity transition matrix (deterministic: s -> s).
    pub fn identity(n_states: usize) -> Self {
        let mut data = vec![vec![0.0; n_states]; n_states];
        for i in 0..n_states {
            data[i][i] = 1.0;
        }
        Self { data, n_states }
    }

    /// Create a uniform transition matrix (all transitions equally likely).
    pub fn uniform(n_states: usize) -> Self {
        let p = 1.0 / n_states as f64;
        Self {
            data: vec![vec![p; n_states]; n_states],
            n_states,
        }
    }

    /// Number of states.
    pub fn n_states(&self) -> usize {
        self.n_states
    }

    /// Get probability P(s' | s).
    pub fn probability(&self, from_state: usize, to_state: usize) -> f64 {
        self.data[from_state][to_state]
    }

    /// Sample a next state given current state.
    pub fn sample<R: Rng>(&self, rng: &mut R, from_state: usize) -> usize {
        let row = &self.data[from_state];
        let dist = WeightedIndex::new(row).unwrap();
        dist.sample(rng)
    }

    /// Get the entire transition matrix as a reference.
    pub fn matrix(&self) -> &[Vec<f64>] {
        &self.data
    }

    /// Check if the matrix is valid (all rows sum to 1.0 within epsilon).
    pub fn is_valid(&self, epsilon: f64) -> bool {
        for row in &self.data {
            let sum: f64 = row.iter().sum();
            if (sum - 1.0).abs() > epsilon {
                return false;
            }
        }
        true
    }

    /// Compute the stationary distribution (if ergodic).
    /// Uses power iteration method.
    pub fn stationary_distribution(&self, max_iter: usize, tol: f64) -> Vec<f64> {
        let mut dist = vec![1.0 / self.n_states as f64; self.n_states];
        for _ in 0..max_iter {
            let mut new_dist = vec![0.0; self.n_states];
            for s in 0..self.n_states {
                for s_prime in 0..self.n_states {
                    new_dist[s_prime] += dist[s] * self.data[s][s_prime];
                }
            }
            let diff: f64 = dist.iter()
                .zip(&new_dist)
                .map(|(a, b)| (a - b).abs())
                .sum();
            dist = new_dist;
            if diff < tol {
                break;
            }
        }
        dist
    }
}

/// Complete transition model for all actions.
#[derive(Debug, Clone)]
pub struct TransitionModel {
    matrices: HashMap<String, TransitionMatrix>,
    actions: Vec<String>,
    n_states: usize,
}

impl TransitionModel {
    /// Create a new transition model from action-matrix pairs.
    pub fn new(matrices: HashMap<String, TransitionMatrix>) -> Result<Self, String> {
        if matrices.is_empty() {
            return Err("Transition model must contain at least one action".to_string());
        }
        let n_states = matrices.values().next().unwrap().n_states();
        for (action, matrix) in &matrices {
            if matrix.n_states() != n_states {
                return Err(format!(
                    "Action '{}' has {} states, expected {}",
                    action, matrix.n_states(), n_states
                ));
            }
        }
        let actions: Vec<String> = matrices.keys().cloned().collect();
        Ok(Self { matrices, actions, n_states })
    }

    /// Number of states.
    pub fn n_states(&self) -> usize {
        self.n_states
    }

    /// List of available actions.
    pub fn actions(&self) -> &[String] {
        &self.actions
    }

    /// Get transition matrix for a specific action.
    pub fn matrix(&self, action: &str) -> Option<&TransitionMatrix> {
        self.matrices.get(action)
    }

    /// Probability P(s' | s, a).
    pub fn probability(&self, action: &str, from_state: usize, to_state: usize) -> Option<f64> {
        self.matrices.get(action).map(|m| m.probability(from_state, to_state))
    }

    /// Sample next state given action and current state.
    pub fn sample<R: Rng>(&self, rng: &mut R, action: &str, from_state: usize) -> Option<usize> {
        self.matrices.get(action).map(|m| m.sample(rng, from_state))
    }

    /// Insert a new action or replace existing.
    pub fn insert(&mut self, action: String, matrix: TransitionMatrix) -> Result<(), String> {
        if matrix.n_states() != self.n_states {
            return Err(format!("Matrix has {} states, expected {}", matrix.n_states(), self.n_states));
        }
        if !self.matrices.contains_key(&action) {
            self.actions.push(action.clone());
        }
        self.matrices.insert(action, matrix);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::thread_rng;

    #[test]
    fn test_transition_matrix_creation() {
        let data = vec![
            vec![0.8, 0.2],
            vec![0.3, 0.7],
        ];
        let tm = TransitionMatrix::new(data).unwrap();
        assert_eq!(tm.n_states(), 2);
        assert!((tm.probability(0, 0) - 0.8).abs() < 1e-9);
        assert!((tm.probability(0, 1) - 0.2).abs() < 1e-9);
        assert!((tm.probability(1, 0) - 0.3).abs() < 1e-9);
        assert!((tm.probability(1, 1) - 0.7).abs() < 1e-9);
    }

    #[test]
    fn test_transition_matrix_normalization() {
        let data = vec![
            vec![4.0, 1.0],  // sum = 5
            vec![1.0, 1.0],  // sum = 2
        ];
        let tm = TransitionMatrix::new(data).unwrap();
        assert!((tm.probability(0, 0) - 0.8).abs() < 1e-9);
        assert!((tm.probability(0, 1) - 0.2).abs() < 1e-9);
        assert!((tm.probability(1, 0) - 0.5).abs() < 1e-9);
        assert!((tm.probability(1, 1) - 0.5).abs() < 1e-9);
    }

    #[test]
    fn test_identity_matrix() {
        let tm = TransitionMatrix::identity(3);
        assert_eq!(tm.probability(0, 0), 1.0);
        assert_eq!(tm.probability(0, 1), 0.0);
        assert_eq!(tm.probability(1, 1), 1.0);
    }

    #[test]
    fn test_uniform_matrix() {
        let tm = TransitionMatrix::uniform(4);
        for i in 0..4 {
            for j in 0..4 {
                assert!((tm.probability(i, j) - 0.25).abs() < 1e-9);
            }
        }
    }

    #[test]
    fn test_sampling() {
        let mut rng = thread_rng();
        let tm = TransitionMatrix::new(vec![
            vec![1.0, 0.0],
            vec![0.0, 1.0],
        ]).unwrap();
        assert_eq!(tm.sample(&mut rng, 0), 0);
        assert_eq!(tm.sample(&mut rng, 1), 1);
    }

    #[test]
    fn test_stationary_distribution() {
        let tm = TransitionMatrix::new(vec![
            vec![0.5, 0.5],
            vec![0.5, 0.5],
        ]).unwrap();
        let dist = tm.stationary_distribution(100, 1e-6);
        assert!((dist[0] - 0.5).abs() < 1e-6);
        assert!((dist[1] - 0.5).abs() < 1e-6);
    }

    #[test]
    fn test_transition_model() {
        let mut matrices = HashMap::new();
        matrices.insert("move".to_string(), TransitionMatrix::new(vec![
            vec![0.9, 0.1],
            vec![0.2, 0.8],
        ]).unwrap());
        matrices.insert("stay".to_string(), TransitionMatrix::identity(2));
        let model = TransitionModel::new(matrices).unwrap();
        assert_eq!(model.n_states(), 2);
        assert_eq!(model.actions().len(), 2);
        assert!(model.probability("move", 0, 0).unwrap() > 0.8);
        assert!(model.probability("stay", 0, 0).unwrap() == 1.0);
    }

    #[test]
    fn test_invalid_matrix_squareness() {
        let data = vec![
            vec![0.8, 0.2],
            vec![0.3],  // too short
        ];
        assert!(TransitionMatrix::new(data).is_err());
    }

    #[test]
    fn test_validity_check() {
        let tm = TransitionMatrix::new(vec![
            vec![0.8, 0.2],
            vec![0.3, 0.7],
        ]).unwrap();
        assert!(tm.is_valid(1e-9));
    }
}
