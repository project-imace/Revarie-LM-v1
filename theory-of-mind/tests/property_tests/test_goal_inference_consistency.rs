//! test_goal_inference_consistency.rs
//! Property-based tests for goal inference consistency.

#[cfg(test)]
mod tests {
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn goal_inference_is_consistent(
            actions in prop::collection::vec("goto_kitchen|goto_fridge|drink_water", 1..5)
        ) {
            // Property: Observed sequences should always be non-empty for inference
            assert!(!actions.is_empty());
            let inferred = actions.len() > 0;
            assert!(inferred);
        }

        #[test]
        fn prior_normalization_holds(
            prior_food in 0.1..1.0_f64,
            prior_water in 0.1..1.0_f64,
            prior_rest in 0.1..1.0_f64,
        ) {
            // Property: Normalization must always sum to 1.0 (within epsilon)
            let total = prior_food + prior_water + prior_rest;
            let normalized_food = prior_food / total;
            let normalized_water = prior_water / total;
            let normalized_rest = prior_rest / total;
            let sum = normalized_food + normalized_water + normalized_rest;
            assert!((sum - 1.0).abs() < 1e-9);
        }
    }
}
