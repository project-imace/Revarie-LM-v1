//! dopamine_analog.rs – Affective Modulator: Dopamine Analog
//!
//! Implements a computational analog of the dopaminergic system.
//! Dopamine mediates reward prediction, motivation, goal-directed behavior,
//! and reinforcement learning. Critical for the "wanting" component of reward.
//!
//! Theoretical Foundations:
//! - Schultz et al. (1997): Dopamine neurons encode reward prediction error.
//! - Berridge & Robinson (1998): Distinction between "liking" and "wanting".
//! - Montague et al. (1996): Temporal difference learning model of dopamine.
//! - Fellous (1999): Neuromodulatory basis of emotion.
//!
//! Mathematical Model:
//! - Reward prediction error: δ(t) = R(t) + γ·V(t+1) - V(t)
//! - Dopamine level: DA(t+1) = DA(t) + α·δ(t) - β·(DA(t) - baseline)
//! - Motivation = σ(DA(t) - threshold) where σ is sigmoid.

use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct DopamineAnalog {
    /// Current dopamine level (0.0 to 1.0)
    pub level: f64,
    /// Baseline homeostatic level
    pub baseline: f64,
    /// Learning rate for reward prediction error (α)
    pub learning_rate: f64,
    /// Decay rate back to baseline (β)
    pub decay_rate: f64,
    /// Temporal discount factor (γ)
    pub discount_factor: f64,
    /// Current value estimate V(t)
    pub value_estimate: f64,
    /// Reward prediction error history
    pub prediction_error_history: Vec<f64>,
    /// Activation threshold for motivated behavior
    pub motivation_threshold: f64,
    /// Maximum history size
    max_history: usize,
    /// Last update timestamp
    last_update: Instant,
}

impl Default for DopamineAnalog {
    fn default() -> Self {
        Self {
            level: 0.5,
            baseline: 0.5,
            learning_rate: 0.15,
            decay_rate: 0.05,
            discount_factor: 0.9,
            value_estimate: 0.5,
            prediction_error_history: Vec::with_capacity(100),
            motivation_threshold: 0.4,
            max_history: 100,
            last_update: Instant::now(),
        }
    }
}

impl DopamineAnalog {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_baseline(mut self, baseline: f64) -> Self {
        self.baseline = baseline.clamp(0.0, 1.0);
        self.level = self.baseline;
        self
    }

    pub fn with_learning_rate(mut self, lr: f64) -> Self {
        self.learning_rate = lr.clamp(0.01, 0.5);
        self
    }

    pub fn with_discount(mut self, gamma: f64) -> Self {
        self.discount_factor = gamma.clamp(0.5, 0.99);
        self
    }

    /// Process a reward signal and update dopamine level via reward prediction error.
    /// Returns the prediction error δ(t).
    pub fn process_reward(&mut self, reward: f64, next_value_estimate: Option<f64>) -> f64 {
        let clamped_reward = reward.clamp(0.0, 1.0);
        let next_v = next_value_estimate.unwrap_or(self.value_estimate);
        
        // Temporal difference reward prediction error
        let prediction_error = clamped_reward + self.discount_factor * next_v - self.value_estimate;
        
        // Update value estimate
        self.value_estimate = self.value_estimate + self.learning_rate * prediction_error;
        self.value_estimate = self.value_estimate.clamp(0.0, 1.0);
        
        // Update dopamine level via phasic response to prediction error
        let phasic_response = if prediction_error > 0.0 {
            prediction_error * 0.5  // Positive error → dopamine burst
        } else {
            prediction_error * 0.3  // Negative error → dopamine dip
        };
        
        self.level = (self.level + phasic_response).clamp(0.0, 1.0);
        
        // Apply tonic decay toward baseline
        self.apply_decay();
        
        // Record history
        self.prediction_error_history.push(prediction_error);
        if self.prediction_error_history.len() > self.max_history {
            self.prediction_error_history.remove(0);
        }
        
        self.last_update = Instant::now();
        prediction_error
    }

    /// Apply expectation-based dopamine release (anticipatory).
    pub fn anticipate(&mut self, expected_reward: f64) -> f64 {
        let expectation = expected_reward.clamp(0.0, 1.0);
        let anticipatory_boost = expectation * 0.2;
        self.level = (self.level + anticipatory_boost).min(1.0);
        self.apply_decay();
        self.level
    }

    /// Apply tonic decay back toward baseline.
    fn apply_decay(&mut self) {
        let decay = self.decay_rate * (self.level - self.baseline);
        self.level -= decay;
        self.level = self.level.clamp(0.0, 1.0);
    }

    /// Update based on elapsed time (tonic regulation).
    pub fn update_tonic(&mut self) {
        self.apply_decay();
        self.last_update = Instant::now();
    }

    /// Compute current motivation level (0.0 to 1.0).
    pub fn motivation(&self) -> f64 {
        let sigmoid_input = 8.0 * (self.level - self.motivation_threshold);
        let motivation = 1.0 / (1.0 + (-sigmoid_input).exp());
        motivation.clamp(0.0, 1.0)
    }

    /// Whether the agent is currently in a motivated state.
    pub fn is_motivated(&self) -> bool {
        self.level > self.motivation_threshold
    }

    /// Get the recent trend of prediction errors (positive = learning, negative = disappointment).
    pub fn error_trend(&self, window: usize) -> f64 {
        let n = self.prediction_error_history.len().min(window);
        if n == 0 { return 0.0; }
        let start = self.prediction_error_history.len() - n;
        self.prediction_error_history[start..].iter().sum::<f64>() / n as f64
    }

    /// Reset the dopamine system to baseline.
    pub fn reset(&mut self) {
        self.level = self.baseline;
        self.value_estimate = self.baseline;
        self.prediction_error_history.clear();
        self.last_update = Instant::now();
    }

    pub fn get_level(&self) -> f64 {
        self.level
    }
}
