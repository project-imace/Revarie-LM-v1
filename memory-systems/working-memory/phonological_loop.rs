//! phonological_loop.rs
//! Working Memory – Phonological Loop.
//! Implements Baddeley's phonological loop component of working memory.
//! Temporarily stores verbal/acoustic information with subvocal rehearsal.
//! Based on Baddeley & Hitch (1974) and Baddeley (2000).

use std::collections::VecDeque;
use std::time::{Duration, Instant};

/// A phonological item stored in the loop.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PhonologicalItem {
    /// The verbal content (word, phoneme, or digit).
    pub content: String,
    /// Number of syllables (affects capacity).
    pub syllables: usize,
    /// Timestamp for decay tracking.
    pub timestamp: Instant,
    /// Whether item has been rehearsed recently.
    pub rehearsed: bool,
}

impl PhonologicalItem {
    pub fn new(content: impl Into<String>, syllables: usize) -> Self {
        Self {
            content: content.into(),
            syllables,
            timestamp: Instant::now(),
            rehearsed: false,
        }
    }
}

/// Phonological Loop – maintains verbal information through rehearsal.
pub struct PhonologicalLoop {
    /// The phonological store (capacity limited by time, not items).
    store: VecDeque<PhonologicalItem>,
    /// Maximum duration an item can persist without rehearsal (~2 seconds).
    decay_duration: Duration,
    /// Whether subvocal rehearsal is active.
    rehearsal_active: bool,
    /// Rehearsal rate (items per second).
    rehearsal_rate: f64,
    /// Total syllable capacity (affects word length effect).
    syllable_capacity: usize,
    /// Current total syllables in store.
    current_syllables: usize,
}

impl Default for PhonologicalLoop {
    fn default() -> Self {
        Self {
            store: VecDeque::new(),
            decay_duration: Duration::from_secs(2),
            rehearsal_active: true,
            rehearsal_rate: 4.0, // ~4 items per second
            syllable_capacity: 8, // typical capacity in syllables
            current_syllables: 0,
        }
    }
}

impl PhonologicalLoop {
    pub fn new() -> Self {
        Self::default()
    }

    /// Set the decay duration (how long items persist without rehearsal).
    pub fn with_decay(mut self, duration: Duration) -> Self {
        self.decay_duration = duration;
        self
    }

    /// Set the syllable capacity.
    pub fn with_syllable_capacity(mut self, capacity: usize) -> Self {
        self.syllable_capacity = capacity;
        self
    }

    /// Enable or disable rehearsal.
    pub fn with_rehearsal(mut self, active: bool) -> Self {
        self.rehearsal_active = active;
        self
    }

    /// Insert a new phonological item.
    pub fn insert(&mut self, content: impl Into<String>, syllables: usize) -> bool {
        let item = PhonologicalItem::new(content, syllables);
        
        // Check capacity based on syllable count (word length effect)
        if self.current_syllables + syllables > self.syllable_capacity {
            // Try to make room by removing oldest unrehearsed items
            self.evict_unrehearsed();
            if self.current_syllables + syllables > self.syllable_capacity {
                return false; // Cannot insert
            }
        }
        
        self.current_syllables += syllables;
        self.store.push_back(item);
        true
    }

    /// Evict oldest unrehearsed items to make room.
    fn evict_unrehearsed(&mut self) {
        let mut to_remove = Vec::new();
        for (i, item) in self.store.iter().enumerate() {
            if !item.rehearsed {
                to_remove.push(i);
            }
        }
        for &i in to_remove.iter().rev() {
            if let Some(item) = self.store.remove(i) {
                self.current_syllables -= item.syllables;
            }
        }
    }

    /// Perform rehearsal – refreshes timestamps and marks items as rehearsed.
    pub fn rehearse(&mut self) {
        if !self.rehearsal_active {
            return;
        }
        let now = Instant::now();
        for item in self.store.iter_mut() {
            item.timestamp = now;
            item.rehearsed = true;
        }
    }

    /// Remove decayed items (those that haven't been rehearsed within decay_duration).
    pub fn cleanup(&mut self) -> usize {
        let now = Instant::now();
        let before = self.store.len();
        self.store.retain(|item| {
            let age = now.duration_since(item.timestamp);
            if age < self.decay_duration {
                true
            } else {
                self.current_syllables -= item.syllables;
                false
            }
        });
        before - self.store.len()
    }

    /// Recall all currently active items (in order).
    pub fn recall(&mut self) -> Vec<String> {
        self.cleanup();
        self.store.iter().map(|item| item.content.clone()).collect()
    }

    /// Recall with rehearsal (simulates active maintenance).
    pub fn recall_with_rehearsal(&mut self) -> Vec<String> {
        self.rehearse();
        self.recall()
    }

    /// Get current number of items.
    pub fn len(&self) -> usize {
        self.store.len()
    }

    /// Check if store is empty.
    pub fn is_empty(&self) -> bool {
        self.store.is_empty()
    }

    /// Get current syllable count.
    pub fn syllable_count(&self) -> usize {
        self.current_syllables
    }

    /// Clear all items.
    pub fn clear(&mut self) {
        self.store.clear();
        self.current_syllables = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread::sleep;

    #[test]
    fn test_insert_and_recall() {
        let mut pl = PhonologicalLoop::new();
        assert!(pl.insert("apple", 2));
        assert!(pl.insert("banana", 3));
        let recalled = pl.recall();
        assert_eq!(recalled, vec!["apple", "banana"]);
    }

    #[test]
    fn test_syllable_capacity_word_length_effect() {
        let mut pl = PhonologicalLoop::new().with_syllable_capacity(5);
        assert!(pl.insert("cat", 1));      // 1 syllable
        assert!(pl.insert("table", 2));    // 2 syllables
        assert!(pl.insert("dog", 1));      // 1 syllable -> total 4
        assert!(!pl.insert("elephant", 3)); // would exceed capacity
        assert_eq!(pl.len(), 3);
    }

    #[test]
    fn test_rehearsal_prevents_decay() {
        let mut pl = PhonologicalLoop::new()
            .with_decay(Duration::from_millis(50))
            .with_rehearsal(true);
        pl.insert("test", 1);
        sleep(Duration::from_millis(30));
        pl.rehearse();
        sleep(Duration::from_millis(30));
        let recalled = pl.recall();
        assert_eq!(recalled, vec!["test"]);
    }

    #[test]
    fn test_no_rehearsal_allows_decay() {
        let mut pl = PhonologicalLoop::new()
            .with_decay(Duration::from_millis(10))
            .with_rehearsal(false);
        pl.insert("test", 1);
        sleep(Duration::from_millis(20));
        let recalled = pl.recall();
        assert!(recalled.is_empty());
    }

    #[test]
    fn test_recall_with_rehearsal() {
        let mut pl = PhonologicalLoop::new()
            .with_decay(Duration::from_millis(30));
        pl.insert("A", 1);
        pl.insert("B", 1);
        sleep(Duration::from_millis(20));
        let recalled = pl.recall_with_rehearsal();
        assert_eq!(recalled.len(), 2);
    }

    #[test]
    fn test_evict_unrehearsed() {
        let mut pl = PhonologicalLoop::new().with_syllable_capacity(3);
        pl.insert("A", 1);
        pl.insert("B", 1);
        pl.insert("C", 1);
        // All unrehearsed, inserting another should evict oldest
        assert!(pl.insert("D", 1));
        let recalled = pl.recall();
        assert_eq!(recalled.len(), 3);
        assert!(!recalled.contains(&"A".to_string()));
    }
}
