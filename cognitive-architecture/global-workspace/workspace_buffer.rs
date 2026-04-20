//! workspace_buffer.rs
//! Global Workspace buffer – the central "theater" of consciousness.
//! Implements Baars' Global Workspace Theory: a limited‑capacity buffer
//! that broadcasts information to specialized processors.

use std::collections::VecDeque;
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime};

/// A single item in the workspace – represents conscious content.
#[derive(Debug, Clone, PartialEq)]
pub struct WorkspaceItem {
    /// Unique identifier for this item.
    pub id: String,
    /// The actual content (could be text, symbol, reference).
    pub content: String,
    /// Source module that produced this item.
    pub source: String,
    /// Priority (higher = more likely to be broadcast).
    pub priority: u8,
    /// Creation timestamp.
    pub created_at: SystemTime,
    /// How long this item can stay in the workspace.
    pub ttl: Duration,
}

impl WorkspaceItem {
    /// Creates a new workspace item with default TTL of 5 seconds.
    pub fn new(id: impl Into<String>, content: impl Into<String>, source: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            content: content.into(),
            source: source.into(),
            priority: 5,
            created_at: SystemTime::now(),
            ttl: Duration::from_secs(5),
        }
    }

    /// Sets the priority of this item.
    pub fn with_priority(mut self, priority: u8) -> Self {
        self.priority = priority.clamp(0, 10);
        self
    }

    /// Sets the time‑to‑live for this item.
    pub fn with_ttl(mut self, ttl: Duration) -> Self {
        self.ttl = ttl;
        self
    }

    /// Checks if the item has expired.
    pub fn is_expired(&self) -> bool {
        self.created_at.elapsed().map(|e| e >= self.ttl).unwrap_or(true)
    }
}

/// The Global Workspace – a limited‑capacity buffer that broadcasts
/// the most salient content to all subscribed modules.
pub struct GlobalWorkspace {
    /// The actual buffer (limited capacity).
    buffer: VecDeque<WorkspaceItem>,
    /// Maximum number of items that can coexist in the workspace.
    capacity: usize,
    /// Subscribers that receive broadcasts (would be channels in production).
    subscriber_count: Arc<Mutex<usize>>,
}

impl Default for GlobalWorkspace {
    fn default() -> Self {
        Self {
            buffer: VecDeque::new(),
            capacity: 7, // Miller's Law: 7 ± 2 items
            subscriber_count: Arc::new(Mutex::new(0)),
        }
    }
}

impl GlobalWorkspace {
    /// Creates a new workspace with default capacity (7 items).
    pub fn new() -> Self {
        Self::default()
    }

    /// Sets a custom capacity for the workspace.
    pub fn with_capacity(mut self, capacity: usize) -> Self {
        self.capacity = capacity;
        self
    }

    /// Inserts a new item into the workspace.
    /// If the buffer is full, the lowest‑priority item is evicted.
    pub fn insert(&mut self, item: WorkspaceItem) {
        // Remove expired items first.
        self.cleanup();

        // If still full, evict the lowest priority item.
        if self.buffer.len() >= self.capacity {
            if let Some(lowest_idx) = self.find_lowest_priority_index() {
                self.buffer.remove(lowest_idx);
            }
        }

        self.buffer.push_back(item);
        // Sort by priority (highest first) to facilitate attention selection.
        self.buffer.make_contiguous().sort_by(|a, b| b.priority.cmp(&a.priority));
    }

    /// Returns the current most salient (highest priority) item.
    pub fn current_focus(&self) -> Option<&WorkspaceItem> {
        self.buffer.front()
    }

    /// Broadcasts the current focus to all subscribers.
    /// In a real implementation, this would send through channels.
    pub fn broadcast(&self) -> Option<WorkspaceItem> {
        let item = self.current_focus()?;
        // Simulate broadcast by returning a clone.
        // In production: send to subscriber channels.
        Some(item.clone())
    }

    /// Removes expired items from the buffer.
    fn cleanup(&mut self) {
        self.buffer.retain(|item| !item.is_expired());
    }

    /// Finds the index of the lowest‑priority item in the buffer.
    fn find_lowest_priority_index(&self) -> Option<usize> {
        self.buffer
            .iter()
            .enumerate()
            .min_by_key(|(_, item)| item.priority)
            .map(|(idx, _)| idx)
    }

    /// Returns the current number of items in the workspace.
    pub fn len(&self) -> usize {
        self.buffer.len()
    }

    /// Returns true if the workspace is empty.
    pub fn is_empty(&self) -> bool {
        self.buffer.is_empty()
    }

    /// Clears all items from the workspace.
    pub fn clear(&mut self) {
        self.buffer.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread::sleep;

    #[test]
    fn test_insert_and_focus() {
        let mut ws = GlobalWorkspace::new();
        let item = WorkspaceItem::new("1", "Hello", "system1").with_priority(8);
        ws.insert(item);
        assert_eq!(ws.current_focus().unwrap().content, "Hello");
    }

    #[test]
    fn test_priority_ordering() {
        let mut ws = GlobalWorkspace::new().with_capacity(3);
        ws.insert(WorkspaceItem::new("low", "low", "test").with_priority(2));
        ws.insert(WorkspaceItem::new("high", "high", "test").with_priority(9));
        ws.insert(WorkspaceItem::new("mid", "mid", "test").with_priority(5));

        // Focus should be highest priority.
        assert_eq!(ws.current_focus().unwrap().content, "high");
    }

    #[test]
    fn test_expiration() {
        let mut ws = GlobalWorkspace::new();
        let item = WorkspaceItem::new("expire", "gone", "test")
            .with_ttl(Duration::from_millis(10));
        ws.insert(item);
        sleep(Duration::from_millis(20));
        ws.cleanup();
        assert!(ws.is_empty());
    }

    #[test]
    fn test_capacity_eviction() {
        let mut ws = GlobalWorkspace::new().with_capacity(2);
        ws.insert(WorkspaceItem::new("keep1", "keep1", "test").with_priority(8));
        ws.insert(WorkspaceItem::new("evict", "evict", "test").with_priority(1));
        ws.insert(WorkspaceItem::new("keep2", "keep2", "test").with_priority(6));

        assert_eq!(ws.len(), 2);
        let contents: Vec<String> = ws.buffer.iter().map(|i| i.content.clone()).collect();
        assert!(contents.contains(&"keep1".to_string()));
        assert!(contents.contains(&"keep2".to_string()));
        assert!(!contents.contains(&"evict".to_string()));
    }
}
