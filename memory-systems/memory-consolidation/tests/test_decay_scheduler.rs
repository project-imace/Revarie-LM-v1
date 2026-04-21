#[cfg(test)]
mod tests {
    include!("../decay_scheduler.rs");

    #[test]
    fn test_register_and_compute() {
        let mut scheduler = DecayScheduler::new(MemoryDecayConfig::default());
        scheduler.register_memory("mem1", 0.8);
        assert_eq!(scheduler.decay_events.len(), 1);
    }
}
