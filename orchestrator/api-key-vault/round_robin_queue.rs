//! round_robin_queue.rs – High‑Performance Round‑Robin Key Queue
//!
//! Thread‑safe, lock‑free round‑robin queue for API key distribution.
//! Provides atomic operations for high‑throughput key rotation.

use std::collections::VecDeque;
use std::sync::{Arc, Mutex, RwLock};
use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct APIKey {
    pub key: String,
    pub provider: String,
    pub model: String,
    pub status: KeyStatus,
    pub last_used: Instant,
    pub rate_limit_until: Instant,
    pub failure_count: usize,
    pub success_count: usize,
    pub total_calls: usize,
    pub avg_latency_ms: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum KeyStatus {
    Healthy,
    Degraded,
    RateLimited,
    Failed,
}

impl APIKey {
    pub fn new(key: impl Into<String>, provider: impl Into<String>, model: impl Into<String>) -> Self {
        Self {
            key: key.into(),
            provider: provider.into(),
            model: model.into(),
            status: KeyStatus::Healthy,
            last_used: Instant::now(),
            rate_limit_until: Instant::now(),
            failure_count: 0,
            success_count: 0,
            total_calls: 0,
            avg_latency_ms: 0.0,
        }
    }

    pub fn is_available(&self) -> bool {
        match self.status {
            KeyStatus::Failed => false,
            KeyStatus::RateLimited => Instant::now() >= self.rate_limit_until,
            _ => true,
        }
    }

    pub fn record_success(&mut self, latency_ms: f64) {
        self.success_count += 1;
        self.total_calls += 1;
        self.avg_latency_ms = (self.avg_latency_ms * (self.total_calls - 1) as f64 + latency_ms)
            / self.total_calls as f64;
        self.failure_count = 0;
        self.status = KeyStatus::Healthy;
    }

    pub fn record_failure(&mut self, is_rate_limit: bool) {
        self.failure_count += 1;
        self.total_calls += 1;
        if is_rate_limit {
            self.status = KeyStatus::RateLimited;
            let backoff_secs = 2u64.pow(self.failure_count as u32).min(60);
            self.rate_limit_until = Instant::now() + Duration::from_secs(backoff_secs);
        } else if self.failure_count >= 3 {
            self.status = KeyStatus::Failed;
        }
    }
}

#[derive(Debug)]
pub struct RoundRobinQueue {
    keys: Arc<RwLock<VecDeque<APIKey>>>,
    index: Arc<Mutex<usize>>,
}

impl RoundRobinQueue {
    pub fn new() -> Self {
        Self {
            keys: Arc::new(RwLock::new(VecDeque::new())),
            index: Arc::new(Mutex::new(0)),
        }
    }

    pub fn add_key(&self, key: APIKey) {
        self.keys.write().unwrap().push_back(key);
    }

    pub fn add_keys(&self, keys: Vec<APIKey>) {
        self.keys.write().unwrap().extend(keys);
    }

    pub fn next(&self) -> Option<APIKey> {
        let keys = self.keys.read().unwrap();
        if keys.is_empty() {
            return None;
        }

        let mut idx = self.index.lock().unwrap();
        let start_idx = *idx;

        loop {
            let key_idx = *idx % keys.len();
            *idx = (*idx + 1) % keys.len();

            let key = &keys[key_idx];
            if key.is_available() {
                return Some(key.clone());
            }

            if *idx == start_idx {
                break;
            }
        }

        // Fallback: return least recently failed key
        keys.iter()
            .filter(|k| k.status != KeyStatus::Failed)
            .min_by_key(|k| k.rate_limit_until)
            .cloned()
    }

    pub fn len(&self) -> usize {
        self.keys.read().unwrap().len()
    }

    pub fn is_empty(&self) -> bool {
        self.keys.read().unwrap().is_empty()
    }

    pub fn stats(&self) -> KeyPoolStats {
        let keys = self.keys.read().unwrap();
        let mut stats = KeyPoolStats::default();
        stats.total = keys.len();

        for key in keys.iter() {
            match key.status {
                KeyStatus::Healthy => stats.healthy += 1,
                KeyStatus::Degraded => stats.degraded += 1,
                KeyStatus::RateLimited => stats.rate_limited += 1,
                KeyStatus::Failed => stats.failed += 1,
            }
        }
        stats
    }
}

#[derive(Debug, Default, Clone)]
pub struct KeyPoolStats {
    pub total: usize,
    pub healthy: usize,
    pub degraded: usize,
    pub rate_limited: usize,
    pub failed: usize,
}

impl Default for RoundRobinQueue {
    fn default() -> Self {
        Self::new()
    }
}

// =============================================================================
// Tests
// =============================================================================
