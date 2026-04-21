#[cfg(test)]
mod tests {
    include!("../feeling_function.rs");
    use super::*;

    #[test]
    fn test_evaluate_positive() {
        let mut ff = FeelingFunction::new("Test");
        let eval = ff.evaluate("wonderful great", None);
        assert!(eval.valence > 0.0);
    }

    #[test]
    fn test_evaluate_negative() {
        let mut ff = FeelingFunction::new("Test");
        let eval = ff.evaluate("terrible sad", None);
        assert!(eval.valence < 0.0);
    }

    #[test]
    fn test_mood_contagion() {
        let mut ff = FeelingFunction::new("Test").with_mood(0.0);
        ff.evaluate("wonderful excellent amazing", None);
        assert!(ff.mood > 0.0);
    }
}
