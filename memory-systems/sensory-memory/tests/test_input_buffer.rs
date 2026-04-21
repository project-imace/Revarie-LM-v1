//! test_input_buffer.rs
//! Unit tests for Sensory Memory Input Buffer.

#[cfg(test)]
mod tests {
    use std::thread::sleep;
    use std::time::Duration;

    include!("../input_buffer.rs");

    #[test]
    fn test_buffer_initial_state() {
        let buffer: SensoryBuffer<String> = SensoryBuffer::new(10);
        assert!(buffer.is_empty());
        assert_eq!(buffer.len(), 0);
        assert!(buffer.active_items().is_empty());
    }

    #[test]
    fn test_insert_single_item() {
        let mut buffer = SensoryBuffer::new(10);
        buffer.insert("test".to_string(), Modality::Iconic);
        assert_eq!(buffer.len(), 1);
        let items = buffer.active_items();
        assert_eq!(items.len(), 1);
        assert_eq!(*items[0], "test");
    }

    #[test]
    fn test_capacity_eviction() {
        let mut buffer = SensoryBuffer::new(3);
        buffer.insert("A".to_string(), Modality::Iconic);
        buffer.insert("B".to_string(), Modality::Iconic);
        buffer.insert("C".to_string(), Modality::Iconic);
        buffer.insert("D".to_string(), Modality::Iconic);
        assert_eq!(buffer.len(), 3);
        let items = buffer.active_items();
        let contents: Vec<&str> = items.iter().map(|s| s.as_str()).collect();
        assert!(!contents.contains(&"A"));
        assert!(contents.contains(&"B"));
        assert!(contents.contains(&"C"));
        assert!(contents.contains(&"D"));
    }

    #[test]
    fn test_modality_filtering() {
        let mut buffer = SensoryBuffer::new(10);
        buffer.insert("visual".to_string(), Modality::Iconic);
        buffer.insert("audio".to_string(), Modality::Echoic);
        buffer.insert("touch".to_string(), Modality::Haptic);
        let iconic = buffer.items_by_modality(Modality::Iconic);
        assert_eq!(iconic.len(), 1);
        assert_eq!(*iconic[0], "visual");
        let echoic = buffer.items_by_modality(Modality::Echoic);
        assert_eq!(echoic.len(), 1);
        assert_eq!(*echoic[0], "audio");
        let haptic = buffer.items_by_modality(Modality::Haptic);
        assert_eq!(haptic.len(), 1);
        assert_eq!(*haptic[0], "touch");
    }

    #[test]
    fn test_cleanup_removes_expired_items() {
        let mut buffer = SensoryBuffer::new(10)
            .with_decay(Modality::Iconic, Duration::from_millis(10));
        buffer.insert("fast".to_string(), Modality::Iconic);
        buffer.insert("slow".to_string(), Modality::Echoic);  // 2000ms default
        sleep(Duration::from_millis(20));
        let remaining = buffer.cleanup();
        assert_eq!(remaining, 1);
        let items = buffer.active_items();
        assert_eq!(items.len(), 1);
        assert_eq!(*items[0], "slow");
    }

    #[test]
    fn test_clear_buffer() {
        let mut buffer = SensoryBuffer::new(10);
        buffer.insert("A".to_string(), Modality::Iconic);
        buffer.insert("B".to_string(), Modality::Echoic);
        assert!(!buffer.is_empty());
        buffer.clear();
        assert!(buffer.is_empty());
        assert_eq!(buffer.len(), 0);
    }

    #[test]
    fn test_custom_decay_duration() {
        let mut buffer = SensoryBuffer::new(10)
            .with_decay(Modality::Echoic, Duration::from_millis(5));
        buffer.insert("custom".to_string(), Modality::Echoic);
        sleep(Duration::from_millis(10));
        let items = buffer.active_items();
        assert!(items.is_empty());
    }

    #[test]
    fn test_active_items_auto_cleanup() {
        let mut buffer = SensoryBuffer::new(10)
            .with_decay(Modality::Iconic, Duration::from_millis(10));
        buffer.insert("decayed".to_string(), Modality::Iconic);
        buffer.insert("persistent".to_string(), Modality::Echoic);
        sleep(Duration::from_millis(20));
        let items = buffer.active_items();
        assert_eq!(items.len(), 1);
        assert_eq!(*items[0], "persistent");
    }
}
