//! test_free_energy.rs
//! Unit tests for the Free Energy Minimizer implementation.

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    // Include the source file directly for testing
    include!("../free_energy_minimizer.rs");

    fn build_simple_model() -> GenerativeModel {
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
        
        // Action: "look"
        let mut look_trans = HashMap::new();
        let mut look_on = HashMap::new();
        look_on.insert("light_on".to_string(), 1.0);
        let mut look_off = HashMap::new();
        look_off.insert("light_off".to_string(), 1.0);
        look_trans.insert("light_on".to_string(), look_on);
        look_trans.insert("light_off".to_string(), look_off);
        transitions.insert("look".to_string(), look_trans);

        // Action: "toggle"
        let mut toggle_trans = HashMap::new();
        let mut toggle_on = HashMap::new();
        toggle_on.insert("light_off".to_string(), 1.0);
        let mut toggle_off = HashMap::new();
        toggle_off.insert("light_on".to_string(), 1.0);
        toggle_trans.insert("light_on".to_string(), toggle_on);
        toggle_trans.insert("light_off".to_string(), toggle_off);
        transitions.insert("toggle".to_string(), toggle_trans);

        let mut prior = HashMap::new();
        prior.insert("light_on".to_string(), 0.5);
        prior.insert("light_off".to_string(), 0.5);

        GenerativeModel::new(likelihood, transitions, prior)
    }

    #[test]
    fn test_belief_uniform_initialization() {
        let states = vec!["light_on".to_string(), "light_off".to_string()];
        let belief = BeliefState::uniform(&states);
        assert!((belief.probability("light_on") - 0.5).abs() < 1e-6);
        assert!((belief.probability("light_off") - 0.5).abs() < 1e-6);
    }

    #[test]
    fn test_belief_entropy() {
        let states = vec!["A".to_string(), "B".to_string()];
        let belief = BeliefState::uniform(&states);
        let entropy = belief.entropy();
        // H = ln(2) for uniform 2-state
        assert!((entropy - (0.5_f64.ln() * -1.0)).abs() < 1e-6);
    }

    #[test]
    fn test_perception_updates_belief() {
        let model = build_simple_model();
        let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
        let mut agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string()]);

        agent.perceive("bright");
        let belief = agent.belief();
        // After seeing "bright", light_on probability should spike
        assert!(belief.probability("light_on") > belief.probability("light_off"));
    }

    #[test]
    fn test_free_energy_decreases_after_perception() {
        let model = build_simple_model();
        let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
        let mut agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string()]);

        let obs = "bright";
        let fe_before = agent.compute_free_energy(obs);
        agent.perceive(obs);
        let fe_after = agent.compute_free_energy(obs);
        assert!(fe_after < fe_before);
    }

    #[test]
    fn test_expected_free_energy_computation() {
        let model = build_simple_model();
        let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
        let mut agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string(), "toggle".to_string()]);

        agent.compute_expected_free_energy();
        assert_eq!(agent.expected_free_energy.len(), 2);
    }

    #[test]
    fn test_action_selection_returns_some() {
        let model = build_simple_model();
        let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
        let mut agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string(), "toggle".to_string()]);

        agent.compute_expected_free_energy();
        let action = agent.select_action();
        assert!(action.is_some());
    }

    #[test]
    fn test_full_cycle() {
        let model = build_simple_model();
        let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
        let mut agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string(), "toggle".to_string()]);

        let action = agent.cycle("bright");
        assert!(action.is_some());
    }

    #[test]
    fn test_precision_parameter() {
        let model = build_simple_model();
        let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
        let agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string()])
            .with_precision(2.0);
        assert_eq!(agent.precision, 2.0);
    }
}
