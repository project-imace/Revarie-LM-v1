//! test_workspace_buffer.rs
//! Unit tests for the Global Workspace buffer implementation.

#[cfg(test)]
mod tests {
    use std::thread::sleep;
    use std::time::Duration;

    // Import the module from the parent directory.
    // In a real project, this would be `use revarie::gwt::workspace_buffer::*`
    // For now, we include the source directly.
    include!("../workspace_buffer.rs");

    #[test]
    fn test_buffer_initial_state() {
        let ws = GlobalWorkspace::new();
        assert!(ws.is_empty());
        assert_eq!(ws.len(), 0);
        assert!(ws.current_focus().is_none());
    }

    #[test]
    fn test_single_item_insertion() {
        let mut ws = GlobalWorkspace::new();
        let item = WorkspaceItem::new("test1", "content1", "moduleA").with_priority(5);
        ws.insert(item.clone());
        assert_eq!(ws.len(), 1);
        assert_eq!(ws.current_focus().unwrap().content, "content1");
    }

    #[test]
    fn test_priority_eviction() {
        let mut ws = GlobalWorkspace::new().with_capacity(2);
        
        // Fill buffer
        ws.insert(WorkspaceItem::new("low1", "low1", "test").with_priority(1));
        ws.insert(WorkspaceItem::new("high", "high", "test").with_priority(10));
        
        // This should evict "low1"
        ws.insert(WorkspaceItem::new("mid", "mid", "test").with_priority(5));
        
        assert_eq!(ws.len(), 2);
        let items: Vec<String> = ws.buffer.iter().map(|i| i.content.clone()).collect();
        assert!(items.contains(&"high".to_string()));
        assert!(items.contains(&"mid".to_string()));
        assert!(!items.contains(&"low1".to_string()));
    }

    #[test]
    fn test_expiration_cleanup() {
        let mut ws = GlobalWorkspace::new();
        let item = WorkspaceItem::new("exp", "expired", "test")
            .with_ttl(Duration::from_millis(10));
        ws.insert(item);
        sleep(Duration::from_millis(20));
        
        // Cleanup should remove expired item.
        ws.cleanup();
        assert!(ws.is_empty());
    }

    #[test]
    fn test_broadcast_returns_focus() {
        let mut ws = GlobalWorkspace::new();
        let item = WorkspaceItem::new("bcast", "broadcasted", "moduleX");
        ws.insert(item);
        
        let broadcasted = ws.broadcast();
        assert!(broadcasted.is_some());
        assert_eq!(broadcasted.unwrap().content, "broadcasted");
    }

    #[test]
    fn test_clear_removes_all() {
        let mut ws = GlobalWorkspace::new();
        ws.insert(WorkspaceItem::new("1", "one", "test"));
        ws.insert(WorkspaceItem::new("2", "two", "test"));
        ws.clear();
        assert!(ws.is_empty());
    }

    #[test]
    fn test_capacity_default_is_seven() {
        let ws = GlobalWorkspace::new();
        // Miller's Law: 7 ± 2
        assert_eq!(ws.capacity, 7);
    }

    #[test]
    fn test_workspace_item_builder_pattern() {
        let item = WorkspaceItem::new("id", "hello", "system1")
            .with_priority(8)
            .with_ttl(Duration::from_secs(30));
        
        assert_eq!(item.priority, 8);
        assert_eq!(item.ttl, Duration::from_secs(30));
        assert_eq!(item.content, "hello");
    }

    #[test]
    fn test_item_expiration_check() {
        let item = WorkspaceItem::new("test", "content", "src")
            .with_ttl(Duration::from_millis(50));
        assert!(!item.is_expired());
        sleep(Duration::from_millis(60));
        assert!(item.is_expired());
    }

    #[test]
    fn test_priority_clamping() {
        let item = WorkspaceItem::new("test", "content", "src").with_priority(15);
        assert_eq!(item.priority, 10); // Clamped to max 10
        
        let item2 = WorkspaceItem::new("test2", "content", "src").with_priority(0);
        assert_eq!(item2.priority, 0);
    }
}
