//! serotonin_analog.rs – Affective Modulator: Serotonin Analog
//!
//! Implements a computational analog of the serotonergic system.
//! Serotonin mediates mood stability, patience, impulse control, and
//! long-term wellbeing. Low serotonin associated with negative affect.
//!
//! Theoretical Foundations:
//! - Dayan & Huys (2009): Serotonin in affective control and delay discounting.
//! - Lovheim (2012): Three-dimensional model of emotions and monoamines.
//! - Miyazaki et al. (2014): Serotonin and patience for delayed rewards.
//! - Larue et al. (2013): Neuromodulatory emotions in cognitive architectures.

use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct SerotoninAnalog {
    /// Current serotonin level (0.0 to 1.0)
    pub level: f64,
    /// Baseline homeostatic level
    pub baseline: f64,
    /// Rate of synthesis/accumulation (α)
    pub synthesis_rate: f64,
    /// Rate of decay/metabolism (β)
    pub decay_rate: f64,
    /// Sensitivity to positive events (up-regulation)
    pub positive_sensitivity: f64,
    /// Sensitivity to negative events (down-regulation)
    pub negative_sensitivity: f64,
    /// Impulse control factor (higher 5-HT = better control)
    pub impulse_control_factor: f64,
    /// Patience factor for delayed gratification (delay discounting)
    pub patience_factor: f64,
    /// Mood stability (inverse of volatility)
    pub mood_stability: f64,
    /// History of levels
    level_history: Vec<f64>,
    max_history: usize,
    last_update: Instant,
}

impl Default for SerotoninAnalog {
    fn default() -> Self {
        Self {
            level: 0.6,
            baseline: 0.6,
            synthesis_rate: 0.03,
            decay_rate: 0.02,
            positive_sensitivity: 0.15,
            negative_sensitivity: 0.25,
            impulse_control_factor: 0.7,
            patience_factor: 0.6,
            mood_stability: 0.7,
            level_history: Vec::with_capacity(100),
            max_history: 100,
            last_update: Instant::now(),
        }
    }
}

impl SerotoninAnalog {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_baseline(mut self, baseline: f64) -> Self {
        self.baseline = baseline.clamp(0.0, 1.0);
        self.level = self.baseline;
        self
    }

    pub fn with_sensitivities(mut self, positive: f64, negative: f64) -> Self {
        self.positive_sensitivity = positive.clamp(0.0, 0.5);
        self.negative_sensitivity = negative.clamp(0.0, 0.5);
        self
    }

    /// Process a positive event (social reward, achievement, etc.)
    pub fn process_positive_event(&mut self, intensity: f64) {
        let boost = intensity.clamp(0.0, 1.0) * self.positive_sensitivity;
        self.level = (self.level + boost).min(1.0);
        self.record_level();
    }

    /// Process a negative event (stress, failure, rejection, etc.)
    pub fn process_negative_event(&mut self, intensity: f64) {
        let drop = intensity.clamp(0.0, 1.0) * self.negative_sensitivity;
        self.level = (self.level - drop).max(0.0);
        self.record_level();
    }

    /// Update based on social feedback (can be positive or negative valence).
    pub fn process_social_feedback(&mut self, valence: f64, intensity: f64) {
        if valence > 0.0 {
            self.process_positive_event(intensity * valence);
        } else {
            self.process_negative_event(intensity * valence.abs());
        }
    }

    /// Apply tonic regulation (synthesis and decay).
    pub fn update_tonic(&mut self) {
        // Synthesis moves toward baseline
        if self.level < self.baseline {
            self.level += self.synthesis_rate * (self.baseline - self.level);
        }
        // Decay from elevated states
        if self.level > self.baseline {
            self.level -= self.decay_rate * (self.level - self.baseline);
        }
        self.level = self.level.clamp(0.0, 1.0);
        self.record_level();
        self.last_update = Instant::now();
    }

    fn record_level(&mut self) {
        self.level_history.push(self.level);
        if self.level_history.len() > self.max_history {
            self.level_history.remove(0);
        }
    }

    /// Compute current impulse control capacity (0.0 to 1.0).
    pub fn impulse_control(&self) -> f64 {
        (self.level * self.impulse_control_factor).clamp(0.0, 1.0)
    }

    /// Compute patience factor for delay discounting.
    /// Higher serotonin = more patience = less discounting.
    pub fn patience(&self) -> f64 {
        (self.level * self.patience_factor + 0.3).clamp(0.1, 1.0)
    }

    /// Compute effective delay discount factor γ' = γ^(1/patience).
    pub fn effective_discount(&self, base_discount: f64) -> f64 {
        base_discount.powf(1.0 / self.patience())
    }

    /// Whether the agent is in a positive mood state.
    pub fn is_positive_mood(&self) -> bool {
        self.level > 0.6
    }

    /// Whether the agent is in a negative/low mood state.
    pub fn is_low_mood(&self) -> bool {
        self.level < 0.3
    }

    /// Get mood volatility (standard deviation of recent levels).
    pub fn volatility(&self, window: usize) -> f64 {
        let n = self.level_history.len().min(window);
        if n < 2 { return 0.0; }
        let start = self.level_history.len() - n;
        let window_data = &self.level_history[start..];
        let mean = window_data.iter().sum::<f64>() / n as f64;
        let variance = window_data.iter().map(|&x| (x - mean).powi(2)).sum::<f64>() / n as f64;
        variance.sqrt()
    }

    /// Reset the serotonin system to baseline.
    pub fn reset(&mut self) {
        self.level = self.baseline;
        self.level_history.clear();
        self.last_update = Instant::now();
    }

    pub fn get_level(&self) -> f64 {
        self.level
    }
}
