#[cfg(test)]
mod tests {
    include!("../serotonin_analog.rs");
    use super::*;

    #[test]
    fn test_mood_state() {
        let mut ht = SerotoninAnalog::new();
        ht.level = 0.7;
        assert!(ht.is_positive_mood());
        ht.level = 0.2;
        assert!(ht.is_low_mood());
    }

    #[test]
    fn test_volatility_calculation() {
        let mut ht = SerotoninAnalog::new();
        ht.level = 0.5; ht.record_level();
        ht.level = 0.7; ht.record_level();
        ht.level = 0.3; ht.record_level();
        let vol = ht.volatility(3);
        assert!(vol > 0.1);
    }
}
