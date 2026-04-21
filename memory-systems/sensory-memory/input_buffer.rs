//! input_buffer.rs
//! Sensory Memory – Input Buffer.
//! Implements the iconic/echoic buffer that briefly holds raw sensory input
//! before attention selects relevant features for further processing.
//! Based on Atkinson & Shiffrin (1968) multi-store model and Sperling (1960).

use std::collections::VecDeque;
use std::time::{Duration, Instant};

/// A single item in the sensory buffer with timestamp for decay.
#[derive(Debug, Clone)]
pub struct SensoryItem<T> {
    pub content: T,
    pub timestamp: Instant,
    pub modality: Modality,
}

/// Sensory modality (iconic, echoic, haptic).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Modality {
    Iconic,   // Visual
    Echoic,   // Auditory
    Haptic,   // Touch
}

impl Default for Modality {
    fn default() -> Self {
        Self::Iconic
    }
}

/// Sensory memory buffer with modality-specific decay rates.
pub struct SensoryBuffer<T> {
    buffer: VecDeque<SensoryItem<T>>,
    capacity: usize,
    /// Decay duration per modality (iconic ~250ms, echoic ~2-4s)
    decay_durations: Vec<(Modality, Duration)>,
}

impl<T> SensoryBuffer<T> {
    /// Create a new sensory buffer with default decay rates.
    pub fn new(capacity: usize) -> Self {
        Self {
            buffer: VecDeque::with_capacity(capacity),
            capacity,
            decay_durations: vec![
                (Modality::Iconic, Duration::from_millis(250)),
                (Modality::Echoic, Duration::from_millis(2000)),
                (Modality::Haptic, Duration::from_millis(1000)),
            ],
        }
    }

    /// Set custom decay duration for a modality.
    pub fn with_decay(mut self, modality: Modality, duration: Duration) -> Self {
        if let Some(pos) = self.decay_durations.iter().position(|(m, _)| *m == modality) {
            self.decay_durations[pos] = (modality, duration);
        } else {
            self.decay_durations.push((modality, duration));
        }
        self
    }

    /// Insert a new sensory item.
    pub fn insert(&mut self, content: T, modality: Modality) {
        let item = SensoryItem {
            content,
            timestamp: Instant::now(),
            modality,
        };
        self.buffer.push_back(item);
        if self.buffer.len() > self.capacity {
            self.buffer.pop_front();
        }
    }

    /// Remove decayed items and return the cleaned buffer length.
    pub fn cleanup(&mut self) -> usize {
        let now = Instant::now();
        self.buffer.retain(|item| {
            let max_age = self.decay_durations
                .iter()
                .find(|(m, _)| *m == item.modality)
                .map(|(_, d)| *d)
                .unwrap_or(Duration::from_millis(500));
            now.duration_since(item.timestamp) < max_age
        });
        self.buffer.len()
    }

    /// Retrieve all currently active items (after cleanup).
    pub fn active_items(&mut self) -> Vec<&T> {
        self.cleanup();
        self.buffer.iter().map(|item| &item.content).collect()
    }

    /// Retrieve items of a specific modality.
    pub fn items_by_modality(&mut self, modality: Modality) -> Vec<&T> {
        self.cleanup();
        self.buffer
            .iter()
            .filter(|item| item.modality == modality)
            .map(|item| &item.content)
            .collect()
    }

    /// Clear all items.
    pub fn clear(&mut self) {
        self.buffer.clear();
    }

    /// Number of items currently in buffer.
    pub fn len(&self) -> usize {
        self.buffer.len()
    }

    /// Check if buffer is empty.
    pub fn is_empty(&self) -> bool {
        self.buffer.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread::sleep;

    #[test]
    fn test_insert_and_retrieve() {
        let mut buffer = SensoryBuffer::new(5);
        buffer.insert("A", Modality::Iconic);
        buffer.insert("B", Modality::Echoic);
        
        let items = buffer.active_items();
        assert_eq!(items.len(), 2);
        assert!(items.contains(&&"A"));
        assert!(items.contains(&&"B"));
    }

    #[test]
    fn test_capacity_limit() {
        let mut buffer = SensoryBuffer::new(2);
        buffer.insert("A", Modality::Iconic);
        buffer.insert("B", Modality::Iconic);
        buffer.insert("C", Modality::Iconic);
        
        assert_eq!(buffer.len(), 2);
        let items = buffer.active_items();
        assert!(!items.contains(&&"A"));
    }

    #[test]
    fn test_modality_filter() {
        let mut buffer = SensoryBuffer::new(5);
        buffer.insert("visual", Modality::Iconic);
        buffer.insert("auditory", Modality::Echoic);
        
        let iconic = buffer.items_by_modality(Modality::Iconic);
        assert_eq!(iconic.len(), 1);
        assert!(iconic.contains(&&"visual"));
    }

    #[test]
    fn test_decay() {
        let mut buffer = SensoryBuffer::new(5)
            .with_decay(Modality::Iconic, Duration::from_millis(10));
        buffer.insert("fast_decay", Modality::Iconic);
        
        sleep(Duration::from_millis(20));
        let items = buffer.active_items();
        assert!(items.is_empty());
    }
}
