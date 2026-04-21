#[cfg(test)]
mod tests {
    include!("../round_robin_queue.rs");
    use super::*;

    #[test]
    fn test_basic_rotation() {
        let queue = RoundRobinQueue::new();
        queue.add_key(APIKey::new("a", "g", "m"));
        queue.add_key(APIKey::new("b", "g", "m"));
        assert_eq!(queue.next().unwrap().key, "a");
        assert_eq!(queue.next().unwrap().key, "b");
    }
}
