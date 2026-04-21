//! free_energy_minimizer.rs
//! Active Inference – Free Energy Minimization.
//! Implements Friston's Free Energy Principle: an agent that minimizes
//! variational free energy through perception, action, and learning.
//! Based on Friston (2010) "The free-energy principle: a unified brain theory?"

use std::collections::HashMap;

/// A probability distribution over hidden states.
#[derive(Debug, Clone)]
pub struct BeliefState {
    /// Probability mass for each possible hidden state.
    pub probabilities: HashMap<String, f64>,
}

impl BeliefState {
    /// Create a new uniform belief over the given states.
    pub fn uniform(states: &[String]) -> Self {
        let n = states.len() as f64;
        let prob = 1.0 / n;
        let mut probabilities = HashMap::new();
        for state in states {
            probabilities.insert(state.clone(), prob);
        }
        Self { probabilities }
    }

    /// Create a belief state from explicit probabilities.
    pub fn new(probabilities: HashMap<String, f64>) -> Self {
        let total: f64 = probabilities.values().sum();
        let normalized: HashMap<String, f64> = probabilities
            .into_iter()
            .map(|(k, v)| (k, v / total))
            .collect();
        Self { probabilities: normalized }
    }

    /// Get the probability of a specific state.
    pub fn probability(&self, state: &str) -> f64 {
        *self.probabilities.get(state).unwrap_or(&0.0)
    }

    /// Compute the entropy of the belief state.
    pub fn entropy(&self) -> f64 {
        -self.probabilities
            .values()
            .filter(|&&p| p > 0.0)
            .map(|&p| p * p.ln())
            .sum::<f64>()
    }
}

/// A generative model: P(obs | state) and P(state' | state, action).
#[derive(Debug, Clone)]
pub struct GenerativeModel {
    /// Likelihood mapping: state -> observation -> probability.
    pub likelihood: HashMap<String, HashMap<String, f64>>,
    /// Transition mapping: action -> from_state -> to_state -> probability.
    pub transitions: HashMap<String, HashMap<String, HashMap<String, f64>>>,
    /// Prior over initial states.
    pub prior: HashMap<String, f64>,
}

impl GenerativeModel {
    /// Create a new generative model.
    pub fn new(
        likelihood: HashMap<String, HashMap<String, f64>>,
        transitions: HashMap<String, HashMap<String, HashMap<String, f64>>>,
        prior: HashMap<String, f64>,
    ) -> Self {
        Self {
            likelihood,
            transitions,
            prior,
        }
    }

    /// Sample an observation given a state (stochastic).
    pub fn sample_observation(&self, state: &str) -> Option<String> {
        let dist = self.likelihood.get(state)?;
        // Simple weighted sampling.
        let total: f64 = dist.values().sum();
        let mut r = rand::random::<f64>() * total;
        for (obs, &prob) in dist {
            r -= prob;
            if r <= 0.0 {
                return Some(obs.clone());
            }
        }
        dist.keys().next().cloned()
    }
}

/// Free Energy Minimizer – the core Active Inference agent.
pub struct FreeEnergyMinimizer {
    /// Current belief about hidden states.
    belief: BeliefState,
    /// The agent's generative model of the world.
    model: GenerativeModel,
    /// Possible actions.
    actions: Vec<String>,
    /// Expected free energy for each action (G).
    expected_free_energy: HashMap<String, f64>,
    /// Precision (inverse temperature) parameter.
    precision: f64,
}

impl FreeEnergyMinimizer {
    /// Create a new minimizer with initial belief and model.
    pub fn new(initial_belief: BeliefState, model: GenerativeModel, actions: Vec<String>) -> Self {
        Self {
            belief: initial_belief,
            model,
            actions,
            expected_free_energy: HashMap::new(),
            precision: 1.0,
        }
    }

    /// Set the precision (gamma) parameter.
    pub fn with_precision(mut self, precision: f64) -> Self {
        self.precision = precision;
        self
    }

    /// Compute variational free energy for current belief given an observation.
    /// F = -E_Q[ln P(obs, state)] - H[Q]
    pub fn compute_free_energy(&self, observation: &str) -> f64 {
        let mut energy = 0.0;
        for (state, &q) in &self.belief.probabilities {
            if q == 0.0 {
                continue;
            }
            // Prior term: -ln P(state), using epsilon to avoid ln(0)
            let prior = *self.model.prior.get(state).unwrap_or(&1e-12);
            // Likelihood term: -ln P(obs | state)
            let likelihood = self
                .model
                .likelihood
                .get(state)
                .and_then(|dist| dist.get(observation))
                .copied()
                .unwrap_or(1e-12);
            energy += q * ( - (prior * likelihood).ln() );
        }
        energy - self.belief.entropy()
    }

    /// Perform perceptual inference: update belief given observation.
    /// Minimizes free energy with respect to Q(state).
    pub fn perceive(&mut self, observation: &str) {
        let mut new_belief = HashMap::new();
        let mut total = 0.0;

        for (state, &q) in &self.belief.probabilities {
            let prior = *self.model.prior.get(state).unwrap_or(&1e-12);
            let likelihood = self
                .model
                .likelihood
                .get(state)
                .and_then(|dist| dist.get(observation))
                .copied()
                .unwrap_or(1e-12);
            // Bayesian update: Q(state) ∝ prior * likelihood * previous Q
            let posterior = q * prior * likelihood;
            new_belief.insert(state.clone(), posterior);
            total += posterior;
        }

        // Normalize
        if total > 0.0 {
            for prob in new_belief.values_mut() {
                *prob /= total;
            }
        }
        self.belief = BeliefState::new(new_belief);
    }

    /// Compute expected free energy for each action.
    /// G(π) = E_Q(o,s|π)[ln Q(s|π) - ln P(o,s|π)]
    pub fn compute_expected_free_energy(&mut self) {
        self.expected_free_energy.clear();

        for action in &self.actions {
            let mut g = 0.0;
            // For each possible outcome, compute epistemic value.
            for (state, &q_state) in &self.belief.probabilities {
                // BUG FIX: Transition probability now depends on the specific ACTION
                if let Some(state_transitions) = self.model.transitions.get(action) {
                    if let Some(next_state_dist) = state_transitions.get(state) {
                        for (next_state, &t_prob) in next_state_dist {
                            // Expected observations from next_state
                            let q_next = q_state * t_prob;
                            if let Some(obs_dist) = self.model.likelihood.get(next_state) {
                                for (_obs, &o_prob) in obs_dist {
                                    // BUG FIX: Using epsilon (1e-12) to prevent taking ln(0)
                                    let info_gain = -o_prob * (o_prob + 1e-12).ln();
                                    g += q_next * o_prob * info_gain;
                                }
                            }
                        }
                    }
                }
            }
            self.expected_free_energy.insert(action.clone(), g);
        }
    }

    /// Select the action that minimizes expected free energy.
    pub fn select_action(&self) -> Option<String> {
        self.expected_free_energy
            .iter()
            // BUG FIX: using unwrap_or to prevent panic on NaN
            .min_by(|(_, g1), (_, g2)| g1.partial_cmp(g2).unwrap_or(std::cmp::Ordering::Equal))
            .map(|(action, _)| action.clone())
    }

    /// Perform a full Active Inference cycle.
    pub fn cycle(&mut self, observation: &str) -> Option<String> {
        self.perceive(observation);
        self.compute_expected_free_energy();
        self.select_action()
    }

    /// Get current belief state.
    pub fn belief(&self) -> &BeliefState {
        &self.belief
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
        
        // BUG FIX: Added "look" action mappings
        let mut look_trans = HashMap::new();
        let mut look_on = HashMap::new(); look_on.insert("light_on".to_string(), 1.0);
        let mut look_off = HashMap::new(); look_off.insert("light_off".to_string(), 1.0);
        look_trans.insert("light_on".to_string(), look_on);
        look_trans.insert("light_off".to_string(), look_off);
        transitions.insert("look".to_string(), look_trans);

        // BUG FIX: Added "toggle" action mappings
        let mut toggle_trans = HashMap::new();
        let mut toggle_on = HashMap::new(); toggle_on.insert("light_off".to_string(), 1.0);
        let mut toggle_off = HashMap::new(); toggle_off.insert("light_on".to_string(), 1.0);
        toggle_trans.insert("light_on".to_string(), toggle_on);
        toggle_trans.insert("light_off".to_string(), toggle_off);
        transitions.insert("toggle".to_string(), toggle_trans);

        let mut prior = HashMap::new();
        prior.insert("light_on".to_string(), 0.5);
        prior.insert("light_off".to_string(), 0.5);

        GenerativeModel::new(likelihood, transitions, prior)
    }

    #[test]
    fn test_belief_update() {
        let model = build_simple_model();
        let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
        let mut agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string()]);

        let obs = "bright";
        agent.perceive(obs);
        let belief = agent.belief();
        assert!(belief.probability("light_on") > belief.probability("light_off"));
    }

    #[test]
    fn test_free_energy_decreases_with_perception() {
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
    fn test_action_selection() {
        let model = build_simple_model();
        let initial_belief = BeliefState::uniform(&["light_on".to_string(), "light_off".to_string()]);
        let mut agent = FreeEnergyMinimizer::new(initial_belief, model, vec!["look".to_string(), "toggle".to_string()]);

        agent.compute_expected_free_energy();
        let action = agent.select_action();
        assert!(action.is_some());
    }
}
