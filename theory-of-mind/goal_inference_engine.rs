//! goal_inference_engine.rs
//! Theory of Mind – Goal Inference Engine.

use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct Goal {
    pub id: String,
    pub description: String,
    pub prior: f64,
}

#[derive(Debug, Clone)]
pub struct Action {
    pub id: String,
    pub effects: Vec<String>,
}

pub struct GoalInferenceEngine {
    goals: HashMap<String, Goal>,
    actions: HashMap<String, Action>,
    posteriors: HashMap<String, f64>,
    observed: Vec<String>,
    rationality: f64,
}

impl GoalInferenceEngine {
    pub fn new(rationality: f64) -> Self {
        Self {
            goals: HashMap::new(),
            actions: HashMap::new(),
            posteriors: HashMap::new(),
            observed: Vec::new(),
            rationality,
        }
    }

    pub fn add_goal(&mut self, goal: Goal) {
        self.posteriors.insert(goal.id.clone(), goal.prior);
        self.goals.insert(goal.id.clone(), goal);
    }

    pub fn add_action(&mut self, action: Action) {
        self.actions.insert(action.id.clone(), action);
    }

    pub fn observe(&mut self, action_id: &str) {
        self.observed.push(action_id.to_string());
        self.update_beliefs();
    }

    fn update_beliefs(&mut self) {
        let mut new_posteriors = HashMap::new();
        let mut total = 0.0;
        for (goal_id, goal) in &self.goals {
            let likelihood = self.compute_likelihood(goal_id);
            let posterior = likelihood * goal.prior;
            new_posteriors.insert(goal_id.clone(), posterior);
            total += posterior;
        }
        if total > 0.0 {
            for (id, prob) in new_posteriors.iter_mut() {
                *prob /= total;
                self.posteriors.insert(id.clone(), *prob);
            }
        }
    }

    fn compute_likelihood(&self, goal_id: &str) -> f64 {
        let mut log_likelihood = 0.0;
        for action_id in &self.observed {
            log_likelihood += self.rationality * self.q_value(goal_id, action_id);
        }
        log_likelihood.exp()
    }

    fn q_value(&self, goal_id: &str, action_id: &str) -> f64 {
        if let Some(action) = self.actions.get(action_id) {
            if action.effects.iter().any(|e| e == goal_id) {
                return 2.0;
            }
        }
        0.1
    }

    pub fn infer_goals(&self) -> HashMap<String, f64> {
        self.posteriors.clone()
    }
}
