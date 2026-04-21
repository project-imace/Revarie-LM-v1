//! decay_scheduler.rs
//! Memory Consolidation – Decay Scheduler.
//! Applies exponential decay to older memories based on recency and importance.
//! Implements the forgetting curve from Ebbinghaus and ACT-R decay theory.

use std::collections::HashMap;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
pub struct MemoryDecayConfig {
    pub base_decay_rate: f64,
    pub min_retention: f64,
    pub importance_weight: f64,
    pub recency_weight: f64,
}

impl Default for MemoryDecayConfig {
    fn default() -> Self {
        Self {
            base_decay_rate: 0.1,
            min_retention: 0.1,
            importance_weight: 0.3,
            recency_weight: 0.7,
        }
    }
}

pub struct DecayScheduler {
    config: MemoryDecayConfig,
    decay_events: Vec<DecayEvent>,
}

#[derive(Debug, Clone)]
pub struct DecayEvent {
    pub memory_id: String,
    pub timestamp: u64,
    pub initial_strength: f64,
    pub importance: f64,
}

impl DecayScheduler {
    pub fn new(config: MemoryDecayConfig) -> Self {
        Self { config, decay_events: Vec::new() }
    }

    pub fn register_memory(&mut self, id: &str, importance: f64) {
        self.decay_events.push(DecayEvent {
            memory_id: id.to_string(),
            timestamp: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            initial_strength: 1.0,
            importance,
        });
    }

    pub fn compute_current_strength(&self, event: &DecayEvent, current_time: u64) -> f64 {
        let age_seconds = (current_time - event.timestamp) as f64;
        let age_days = age_seconds / 86400.0;
        let decay = (-self.config.base_decay_rate * age_days).exp();
        let retention = decay.max(self.config.min_retention);
        retention * (1.0 + self.config.importance_weight * event.importance)
    }

    pub fn get_active_memories(&self) -> Vec<String> {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        self.decay_events.iter()
            .filter(|e| self.compute_current_strength(e, now) > self.config.min_retention)
            .map(|e| e.memory_id.clone())
            .collect()
    }
}
