//! episodic_buffer.rs
//! Working Memory – Episodic Buffer.
//! Implements Baddeley's episodic buffer component of working memory.
//! Integrates information from phonological loop, visuospatial sketchpad,
//! and long-term memory into coherent episodic representations.
//! Based on Baddeley (2000) "The episodic buffer: a new component of working memory?"

use std::collections::VecDeque;
use std::time::{Duration, Instant};
use serde::{Serialize, Deserialize};

/// An episodic chunk – a multimodal binding of information.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EpisodicChunk {
    /// Unique identifier for this episode.
    pub id: String,
    /// Verbal/acoustic content (from phonological loop).
    pub verbal_content: Option<Vec<String>>,
    /// Visual/spatial content (from visuospatial sketchpad).
    pub visual_content: Option<VisualSnapshot>,
    /// Emotional valence (-1.0 to 1.0).
    pub emotional_valence: f64,
    /// Contextual tags (time, location, source).
    pub context: EpisodeContext,
    /// Timestamp of creation.
    #[serde(skip)]
    pub timestamp: Instant,
    /// Activation strength (affects accessibility).
    pub activation: f64,
}

/// Snapshot of visual/spatial information.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VisualSnapshot {
    pub objects: Vec<String>,      // Object identifiers
    pub locations: Vec<(f64, f64)>, // Spatial positions
    pub colors: Vec<String>,        // Dominant colors
}

/// Contextual information for an episode.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EpisodeContext {
    pub source: String,      // Where the information came from
    pub timestamp: u64,      // Unix timestamp
    pub location: Option<String>,
}

impl Default for EpisodeContext {
    fn default() -> Self {
        Self {
            source: "perception".to_string(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            location: None,
        }
    }
}

impl EpisodicChunk {
    pub fn new(id: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            verbal_content: None,
            visual_content: None,
            emotional_valence: 0.0,
            context: EpisodeContext::default(),
            timestamp: Instant::now(),
            activation: 1.0,
        }
    }

    pub fn with_verbal(mut self, content: Vec<String>) -> Self {
        self.verbal_content = Some(content);
        self
    }

    pub fn with_visual(mut self, snapshot: VisualSnapshot) -> Self {
        self.visual_content = Some(snapshot);
        self
    }

    pub fn with_emotion(mut self, valence: f64) -> Self {
        self.emotional_valence = valence.clamp(-1.0, 1.0);
        self
    }

    pub fn with_context(mut self, context: EpisodeContext) -> Self {
        self.context = context;
        self
    }
}

/// Episodic Buffer – binds information into coherent episodes.
pub struct EpisodicBuffer {
    /// Currently active episodic chunks (capacity ~4 chunks).
    chunks: VecDeque<EpisodicChunk>,
    /// Maximum number of chunks (Cowan, 2001: ~4 chunks).
    capacity: usize,
    /// Decay duration for unattended chunks (~2-3 seconds).
    decay_duration: Duration,
    /// Whether active rehearsal/maintenance is enabled.
    maintenance_active: bool,
    /// Link to long-term episodic memory (for consolidation).
    consolidation_threshold: f64,
}

impl Default for EpisodicBuffer {
    fn default() -> Self {
        Self {
            chunks: VecDeque::new(),
            capacity: 4,
            decay_duration: Duration::from_secs(2),
            maintenance_active: true,
            consolidation_threshold: 0.7,
        }
    }
}

impl EpisodicBuffer {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_capacity(mut self, capacity: usize) -> Self {
        self.capacity = capacity;
        self
    }

    pub fn with_decay(mut self, duration: Duration) -> Self {
        self.decay_duration = duration;
        self
    }

    /// Bind information into a new episodic chunk.
    pub fn bind(&mut self, chunk: EpisodicChunk) {
        self.cleanup();
        if self.chunks.len() >= self.capacity {
            // Evict least active chunk
            if let Some(pos) = self.least_active_index() {
                self.chunks.remove(pos);
            }
        }
        self.chunks.push_back(chunk);
    }

    /// Find index of least active chunk.
    fn least_active_index(&self) -> Option<usize> {
        self.chunks
            .iter()
            .enumerate()
            .min_by(|(_, a), (_, b)| a.activation.partial_cmp(&b.activation).unwrap())
            .map(|(i, _)| i)
    }

    /// Remove decayed chunks.
    pub fn cleanup(&mut self) -> usize {
        let now = Instant::now();
        let before = self.chunks.len();
        self.chunks.retain(|chunk| {
            now.duration_since(chunk.timestamp) < self.decay_duration
        });
        before - self.chunks.len()
    }

    /// Maintain active chunks (rehearsal/refreshing).
    pub fn maintain(&mut self) {
        if !self.maintenance_active {
            return;
        }
        let now = Instant::now();
        for chunk in self.chunks.iter_mut() {
            chunk.timestamp = now;
            // Activation decays slightly even with maintenance
            chunk.activation *= 0.99;
        }
    }

    /// Recall all currently active chunks.
    pub fn recall(&mut self) -> Vec<EpisodicChunk> {
        self.cleanup();
        self.chunks.iter().cloned().collect()
    }

    /// Recall with active maintenance.
    pub fn recall_with_maintenance(&mut self) -> Vec<EpisodicChunk> {
        self.maintain();
        self.recall()
    }

    /// Retrieve chunks that match a query (simple keyword match).
    pub fn query(&self, keywords: &[String]) -> Vec<EpisodicChunk> {
        self.chunks
            .iter()
            .filter(|chunk| {
                if let Some(verbal) = &chunk.verbal_content {
                    keywords.iter().any(|kw| verbal.iter().any(|v| v.contains(kw)))
                } else {
                    false
                }
            })
            .cloned()
            .collect()
    }

    /// Get chunks with high activation (ready for consolidation).
    pub fn consolidation_candidates(&self) -> Vec<EpisodicChunk> {
        self.chunks
            .iter()
            .filter(|chunk| chunk.activation >= self.consolidation_threshold)
            .cloned()
            .collect()
    }

    /// Boost activation of a specific chunk (attention).
    pub fn attend_to(&mut self, chunk_id: &str) -> bool {
        for chunk in self.chunks.iter_mut() {
            if chunk.id == chunk_id {
                chunk.activation = (chunk.activation + 0.3).min(2.0);
                chunk.timestamp = Instant::now();
                return true;
            }
        }
        false
    }

    pub fn len(&self) -> usize {
        self.chunks.len()
    }

    pub fn is_empty(&self) -> bool {
        self.chunks.is_empty()
    }

    pub fn clear(&mut self) {
        self.chunks.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread::sleep;

    #[test]
    fn test_bind_and_recall() {
        let mut eb = EpisodicBuffer::new();
        let chunk = EpisodicChunk::new("ep1")
            .with_verbal(vec!["hello".to_string(), "world".to_string()])
            .with_emotion(0.5);
        eb.bind(chunk);
        let recalled = eb.recall();
        assert_eq!(recalled.len(), 1);
        assert_eq!(recalled[0].id, "ep1");
        assert_eq!(recalled[0].emotional_valence, 0.5);
    }

    #[test]
    fn test_capacity_eviction() {
        let mut eb = EpisodicBuffer::new().with_capacity(2);
        eb.bind(EpisodicChunk::new("A"));
        eb.bind(EpisodicChunk::new("B"));
        eb.bind(EpisodicChunk::new("C"));
        let recalled = eb.recall();
        assert_eq!(recalled.len(), 2);
        assert!(!recalled.iter().any(|c| c.id == "A"));
    }

    #[test]
    fn test_query() {
        let mut eb = EpisodicBuffer::new();
        eb.bind(EpisodicChunk::new("ep1")
            .with_verbal(vec!["apple".to_string(), "banana".to_string()]));
        eb.bind(EpisodicChunk::new("ep2")
            .with_verbal(vec!["car".to_string(), "truck".to_string()]));
        let results = eb.query(&["apple".to_string()]);
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].id, "ep1");
    }

    #[test]
    fn test_attend_to_boosts_activation() {
        let mut eb = EpisodicBuffer::new();
        let chunk = EpisodicChunk::new("target");
        eb.bind(chunk);
        let before = eb.chunks[0].activation;
        eb.attend_to("target");
        let after = eb.chunks[0].activation;
        assert!(after > before);
    }

    #[test]
    fn test_consolidation_candidates() {
        let mut eb = EpisodicBuffer::new();
        let mut high_activation = EpisodicChunk::new("high");
        high_activation.activation = 0.9;
        let low_activation = EpisodicChunk::new("low");
        eb.bind(high_activation);
        eb.bind(low_activation);
        let candidates = eb.consolidation_candidates();
        assert_eq!(candidates.len(), 1);
        assert_eq!(candidates[0].id, "high");
    }

    #[test]
    fn test_maintain_refreshes_timestamps() {
        let mut eb = EpisodicBuffer::new()
            .with_decay(Duration::from_millis(50));
        eb.bind(EpisodicChunk::new("keep"));
        sleep(Duration::from_millis(30));
        eb.maintain();
        sleep(Duration::from_millis(30));
        let recalled = eb.recall();
        assert_eq!(recalled.len(), 1);
    }
}
