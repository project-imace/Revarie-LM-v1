#[cfg(test)]
mod tests {
    include!("../identity_persistence.rs");
    use super::*;

    #[test]
    fn test_identity_initialization() {
        let ip = IdentityPersistence::new();
        assert_eq!(ip.identity_strength, 0.5);
        assert!(ip.core_values.contains_key("autonomy"));
    }

    #[test]
    fn test_episode_updates_identity() {
        let mut ip = IdentityPersistence::new();
        ip.record_episode(
            EpisodeType::Achievement,
            "Test".to_string(),
            0.8, 0.7, 0.9,
            vec!["test".to_string()],
        );
        assert!(ip.version > 0);
    }

    #[test]
    fn test_summary_generation() {
        let ip = IdentityPersistence::new();
        let summary = ip.generate_self_summary(Some("Samara"));
        assert!(summary.contains("Samara"));
    }
}
