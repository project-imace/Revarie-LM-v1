//! test_free_energy_convergence.rs
//! Property-based tests for free energy minimization.
//! Verifies that Active Inference agents converge to low free energy states.

#[cfg(test)]
mod tests {
    use proptest::prelude::*;
    use std::collections::HashMap;

    // Include the source file directly
    include!("../../free_energy_minimizer.rs");

    /// Strategy to generate a valid observation string.
    fn observation_strategy() -> impl Strategy<Value = String> {
        prop_oneof!["bright".to_string(), "dim".to_string()]
    }

    /// Build a simple generative model for the light-switch world.
    fn build_light_switch_model() -> GenerativeModel {
        let mut likelihood = HashMap::new();
        let mut light_dist = HashMap::new();
        light_dist.insert("bright".to_string(), 0.9);
        light_dist.insert("dim".to_string(), 0.1);
        likelihood.insert("light_on".to_string(), light_dist);
        let mut dark_dist = HashMap::new();
        dark_dist.insert("bright".to_string(), 0.1);
        dark_dist.insert("dim".to_string(), 0.9);
        likelihood.insert("light_off".to_string(), dark_dist);

        let mut transitions = HashMap::new();
        let mut look_trans = HashMap::new();
        let mut look_on = HashMap::new();
        look_on.insert("light_on".to_string(), 1.0);
        let mut look_off = HashMap::new();
        look_off.insert("light_off".to_string(), 1.0);
        look_trans.insert("light_on".to_string(), look_on);
        look_trans.insert("light_off".to_string(), look_off);
        transitions.insert("look".to_string(), look_trans);

        let mut prior = HashMap::new();
        prior.insert("light_on".to_string(), 0.5);
        prior.insert("light_off".to_string(), 0.5);

        GenerativeModel::new(likelihood, transitions, prior)
    }

    proptest! {
        /// Property: For any sequence of observations, free energy does not increase
        /// after perceptual inference and action selection.
        #[test]
        fn free_energy_is_monotonic(
            obs_seq in prop::collection::vec(observation_strategy(), 1..10)
        ) {
            let model = build_light_switch_model();
            let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
            let mut agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string()]);

            let mut prev_fe = f64::MAX;
            for obs in obs_seq {
                // Compute free energy before perception
                let fe_before = agent.compute_free_energy(&obs);
                // Perform perception (updates belief)
                agent.perceive(&obs);
                // Compute expected free energy for planning (optional, but doesn't hurt)
                agent.compute_expected_free_energy();
                // Free energy after perception should be <= before
                let fe_after = agent.compute_free_energy(&obs);
                // Due to numerical precision, allow tiny increases (1e-9)
                prop_assert!(fe_after <= fe_before + 1e-9,
                    "Free energy increased from {} to {} after perceiving '{}'",
                    fe_before, fe_after, obs);
                prev_fe = fe_after;
            }
        }

        /// Property: After many cycles, free energy converges to a low value.
        #[test]
        fn free_energy_converges_to_low_value(
            obs_seq in prop::collection::vec(observation_strategy(), 20..50)
        ) {
            let model = build_light_switch_model();
            let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
            let mut agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string()]);

            for obs in obs_seq {
                agent.perceive(&obs);
            }
            let final_fe = agent.compute_free_energy("bright");
            // Free energy should be below a reasonable threshold (e.g., 2.0)
            prop_assert!(final_fe < 2.0,
                "Free energy did not converge; final value = {}", final_fe);
        }
    }
}
