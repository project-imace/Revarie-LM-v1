//! test_phonological_loop.rs
//! Unit tests for Phonological Loop.

#[cfg(test)]
mod tests {
    use std::thread::sleep;
    use std::time::Duration;

    include!("../phonological_loop.rs");

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
        assert!(pl.insert("cat", 1));
        assert!(pl.insert("table", 2));
        assert!(pl.insert("dog", 1));
        assert!(!pl.insert("elephant", 3));
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
        assert!(pl.insert("D", 1));
        let recalled = pl.recall();
        assert_eq!(recalled.len(), 3);
        assert!(!recalled.contains(&"A".to_string()));
    }

    #[test]
    fn test_clear() {
        let mut pl = PhonologicalLoop::new();
        pl.insert("test", 1);
        assert!(!pl.is_empty());
        pl.clear();
        assert!(pl.is_empty());
        assert_eq!(pl.syllable_count(), 0);
    }
}
