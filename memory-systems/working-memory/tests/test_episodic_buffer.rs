//! test_episodic_buffer.rs
//! Unit tests for Episodic Buffer.

#[cfg(test)]
mod tests {
    use std::thread::sleep;
    use std::time::Duration;

    include!("../episodic_buffer.rs");

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

    #[test]
    fn test_clear() {
        let mut eb = EpisodicBuffer::new();
        eb.bind(EpisodicChunk::new("test"));
        assert!(!eb.is_empty());
        eb.clear();
        assert!(eb.is_empty());
    }
}
