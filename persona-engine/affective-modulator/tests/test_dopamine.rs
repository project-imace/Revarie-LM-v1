#[cfg(test)]
mod tests {
    include!("../dopamine_analog.rs");
    use super::*;

    #[test]
    fn test_prediction_error_updates_value() {
        let mut da = DopamineAnalog::new();
        da.process_reward(0.9, None);
        assert!(da.value_estimate > 0.5);
    }

    #[test]
    fn test_motivation_threshold() {
        let mut da = DopamineAnalog::new();
        da.level = 0.3;
        assert!(!da.is_motivated());
        da.level = 0.7;
        assert!(da.is_motivated());
    }
}
