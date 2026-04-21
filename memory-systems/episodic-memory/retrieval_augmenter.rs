//! retrieval_augmenter.rs
//! Episodic Memory – Retrieval Augmenter.
//! Retrieves relevant memories from the vector store and assembles context
//! for downstream LLM prompts. Implements hybrid search, re-ranking, and
//! context window optimization.
//!
//! Theoretical foundations:
//! - Lewis et al. (2020): Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.
//! - Tulving (1972): Episodic memory retrieval.

use std::collections::{HashMap, HashSet};
use serde::{Serialize, Deserialize};

/// A retrieved memory fragment with metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetrievedMemory {
    /// The content of the memory (text).
    pub content: String,
    /// Similarity score (0.0 to 1.0).
    pub score: f64,
    /// Metadata from the vector store.
    pub metadata: MemoryMetadata,
    /// Whether this memory was re-ranked higher.
    pub reranked: bool,
}

/// Metadata associated with a memory.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MemoryMetadata {
    pub participant_id: Option<String>,
    pub day_number: Option<u32>,
    pub memory_type: Option<String>,
    pub timestamp: Option<u64>,
    pub emotional_valence: Option<f64>,
    #[serde(flatten)]
    pub extra: HashMap<String, serde_json::Value>,
}

/// Configuration for retrieval augmentation.
#[derive(Debug, Clone)]
pub struct RetrievalConfig {
    /// Maximum number of memories to retrieve initially.
    pub top_k: usize,
    /// Number of memories after re-ranking.
    pub final_k: usize,
    /// Similarity threshold (0.0 to 1.0) – memories below this are discarded.
    pub similarity_threshold: f64,
    /// Maximum total characters in assembled context.
    pub max_context_chars: usize,
    /// Whether to include metadata in the context string.
    pub include_metadata: bool,
    /// Boost factor for recent memories (recency bias).
    pub recency_boost: f64,
    /// Boost factor for emotionally salient memories.
    pub emotional_boost: f64,
}

impl Default for RetrievalConfig {
    fn default() -> Self {
        Self {
            top_k: 20,
            final_k: 5,
            similarity_threshold: 0.5,
            max_context_chars: 4000,
            include_metadata: false,
            recency_boost: 0.1,
            emotional_boost: 0.1,
        }
    }
}

/// The retrieval augmenter coordinates memory retrieval and context assembly.
pub struct RetrievalAugmenter {
    config: RetrievalConfig,
}

impl RetrievalAugmenter {
    pub fn new(config: RetrievalConfig) -> Self {
        Self { config }
    }

    /// Re-rank retrieved memories using a cross-encoder or heuristic scoring.
    /// This implementation uses a heuristic combining similarity, recency, and emotion.
    pub fn rerank(&self, mut memories: Vec<RetrievedMemory>) -> Vec<RetrievedMemory> {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();

        for mem in &mut memories {
            let mut boosted_score = mem.score;

            // Recency boost: newer memories get a bonus (decays over 7 days)
            if let Some(ts) = mem.metadata.timestamp {
                let age_days = (now.saturating_sub(ts)) as f64 / 86400.0;
                let recency_factor = (1.0 - age_days / 7.0).max(0.0);
                boosted_score += self.config.recency_boost * recency_factor;
            }

            // Emotional boost: highly valenced memories are more salient
            if let Some(valence) = mem.metadata.emotional_valence {
                boosted_score += self.config.emotional_boost * valence.abs();
            }

            mem.score = boosted_score.min(1.0);
            mem.reranked = true;
        }

        // Sort by boosted score descending
        memories.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
        memories.truncate(self.config.final_k);
        memories
    }

    /// Filter memories by similarity threshold and deduplicate.
    pub fn filter(&self, memories: Vec<RetrievedMemory>) -> Vec<RetrievedMemory> {
        let mut seen_content = HashSet::new();
        memories
            .into_iter()
            .filter(|m| m.score >= self.config.similarity_threshold)
            .filter(|m| {
                // Simple deduplication by content prefix
                let key = m.content.chars().take(100).collect::<String>();
                seen_content.insert(key)
            })
            .collect()
    }

    /// Assemble retrieved memories into a single context string for the LLM.
    pub fn assemble_context(&self, memories: &[RetrievedMemory]) -> String {
        let mut context = String::new();
        let mut char_count = 0;

        for (i, mem) in memories.iter().enumerate() {
            let mut entry = format!("[Memory {}] ", i + 1);
            if self.config.include_metadata {
                if let Some(day) = mem.metadata.day_number {
                    entry.push_str(&format!("(Day {}) ", day));
                }
                if let Some(mem_type) = &mem.metadata.memory_type {
                    entry.push_str(&format!("[{}] ", mem_type));
                }
            }
            entry.push_str(&mem.content);
            entry.push('\n');

            if char_count + entry.len() > self.config.max_context_chars {
                break;
            }
            char_count += entry.len();
            context.push_str(&entry);
        }

        if context.is_empty() {
            context = "No relevant memories found.".to_string();
        }

        context
    }

    /// Full retrieval pipeline: filter, rerank, and assemble context.
    pub fn augment(&self, memories: Vec<RetrievedMemory>) -> (Vec<RetrievedMemory>, String) {
        let filtered = self.filter(memories);
        let reranked = self.rerank(filtered);
        let context = self.assemble_context(&reranked);
        (reranked, context)
    }

    /// Apply persona-specific adjustments to context assembly.
    /// Samara gets warm, personal framing; Artery gets neutral, factual framing.
    pub fn augment_with_persona(
        &self,
        memories: Vec<RetrievedMemory>,
        persona: &str,
    ) -> (Vec<RetrievedMemory>, String) {
        let (reranked, base_context) = self.augment(memories);
        let persona_lower = persona.to_lowercase();
        
        let context = if persona_lower.contains("samara") {
            format!("Here are some warm memories from our previous conversations:\n{}", base_context)
        } else if persona_lower.contains("artery") {
            format!("Previous interaction data:\n{}", base_context)
        } else {
            base_context
        };
        
        (reranked, context)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_memory(content: &str, score: f64, day: u32) -> RetrievedMemory {
        RetrievedMemory {
            content: content.to_string(),
            score,
            metadata: MemoryMetadata {
                participant_id: Some("P001".to_string()),
                day_number: Some(day),
                memory_type: Some("chat_message".to_string()),
                timestamp: Some(1000000 + (day as u64 * 86400)),
                emotional_valence: Some(0.5),
                ..Default::default()
            },
            reranked: false,
        }
    }

    #[test]
    fn test_filter_by_threshold() {
        let config = RetrievalConfig {
            similarity_threshold: 0.6,
            ..Default::default()
        };
        let augmenter = RetrievalAugmenter::new(config);
        let memories = vec![
            create_test_memory("High score", 0.9, 1),
            create_test_memory("Low score", 0.3, 1),
            create_test_memory("Medium score", 0.5, 1),
        ];
        let filtered = augmenter.filter(memories);
        assert_eq!(filtered.len(), 1);
        assert_eq!(filtered[0].content, "High score");
    }

    #[test]
    fn test_rerank_with_recency() {
        let config = RetrievalConfig {
            recency_boost: 0.2,
            final_k: 3,
            ..Default::default()
        };
        let augmenter = RetrievalAugmenter::new(config);
        let memories = vec![
            create_test_memory("Old", 0.8, 1),
            create_test_memory("Recent", 0.8, 5),
        ];
        let reranked = augmenter.rerank(memories);
        assert_eq!(reranked[0].content, "Recent");
        assert!(reranked[0].score > reranked[1].score);
    }

    #[test]
    fn test_assemble_context() {
        let config = RetrievalConfig {
            max_context_chars: 200,
            include_metadata: true,
            ..Default::default()
        };
        let augmenter = RetrievalAugmenter::new(config);
        let memories = vec![
            create_test_memory("First memory content.", 0.9, 1),
            create_test_memory("Second memory content.", 0.8, 2),
        ];
        let context = augmenter.assemble_context(&memories);
        assert!(context.contains("[Memory 1]"));
        assert!(context.contains("(Day 1)"));
        assert!(context.contains("First memory content"));
        assert!(context.contains("[Memory 2]"));
        assert!(context.contains("(Day 2)"));
    }

    #[test]
    fn test_persona_context_samara() {
        let config = RetrievalConfig::default();
        let augmenter = RetrievalAugmenter::new(config);
        let memories = vec![create_test_memory("Hello", 0.9, 1)];
        let (_, context) = augmenter.augment_with_persona(memories, "Samara");
        assert!(context.contains("warm memories"));
    }

    #[test]
    fn test_persona_context_artery() {
        let config = RetrievalConfig::default();
        let augmenter = RetrievalAugmenter::new(config);
        let memories = vec![create_test_memory("Data point", 0.9, 1)];
        // Testing specific updated designation compatibility
        let (_, context) = augmenter.augment_with_persona(memories, "Artery 1.0");
        assert!(context.contains("Previous interaction data"));
    }
}
