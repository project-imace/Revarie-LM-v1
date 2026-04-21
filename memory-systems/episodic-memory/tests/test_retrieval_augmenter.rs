//! test_retrieval_augmenter.rs
//! Unit tests for Retrieval Augmenter.

#[cfg(test)]
mod tests {
    use std::collections::HashMap;
    include!("../retrieval_augmenter.rs");

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
    fn test_deduplication() {
        let config = RetrievalConfig {
            similarity_threshold: 0.0,
            ..Default::default()
        };
        let augmenter = RetrievalAugmenter::new(config);
        let memories = vec![
            create_test_memory("Duplicate content here", 0.9, 1),
            create_test_memory("Duplicate content here", 0.8, 2),
        ];
        let filtered = augmenter.filter(memories);
        assert_eq!(filtered.len(), 1);
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
    fn test_rerank_with_emotion() {
        let config = RetrievalConfig {
            emotional_boost: 0.2,
            final_k: 3,
            ..Default::default()
        };
        let augmenter = RetrievalAugmenter::new(config);
        let mut neutral = create_test_memory("Neutral", 0.8, 1);
        neutral.metadata.emotional_valence = Some(0.0);
        let mut emotional = create_test_memory("Emotional", 0.8, 1);
        emotional.metadata.emotional_valence = Some(0.9);
        let reranked = augmenter.rerank(vec![neutral, emotional]);
        assert_eq!(reranked[0].content, "Emotional");
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
    fn test_context_truncation() {
        let config = RetrievalConfig {
            max_context_chars: 30,
            include_metadata: false,
            ..Default::default()
        };
        let augmenter = RetrievalAugmenter::new(config);
        let memories = vec![
            create_test_memory("Very long memory content that exceeds the limit.", 0.9, 1),
            create_test_memory("Second memory.", 0.8, 2),
        ];
        let context = augmenter.assemble_context(&memories);
        assert!(context.len() <= config.max_context_chars + 20);
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
        let (_, context) = augmenter.augment_with_persona(memories, "Artery 1.0");
        assert!(context.contains("Previous interaction data"));
    }

    #[test]
    fn test_full_augment_pipeline() {
        let config = RetrievalConfig::default();
        let augmenter = RetrievalAugmenter::new(config);
        let memories = vec![
            create_test_memory("Relevant content", 0.9, 1),
            create_test_memory("Noise", 0.2, 1),
        ];
        let (reranked, context) = augmenter.augment(memories);
        assert_eq!(reranked.len(), 1);
        assert_eq!(reranked[0].content, "Relevant content");
        assert!(context.contains("Relevant content"));
    }
}
