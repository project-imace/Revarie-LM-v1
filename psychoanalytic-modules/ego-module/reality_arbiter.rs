//! reality_arbiter.rs – Ego Module: Reality Arbiter

use std::collections::{VecDeque, HashMap};
use std::time::{Duration, Instant};
use rand::{Rng, SeedableRng};

#[derive(Debug, Clone)]
pub struct IdImpulse {
    pub id: String,
    pub drive: String,
    pub content: String,
    pub intensity: f64,
    pub valence: f64,
    pub timestamp: Instant,
}

#[derive(Debug, Clone)]
pub struct SuperegoConstraint {
    pub rule: String,
    pub description: String,
    pub severity: f64,
    pub violation_cost: f64,
}

#[derive(Debug, Clone)]
pub struct RealityCheck {
    pub context: String,
    pub risk_level: f64,
    pub available_resources: Vec<String>,
    pub social_appropriateness: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum DefenseMechanism {
    Repression, Sublimation, Rationalization, Projection, 
    Displacement, Denial, ReactionFormation, Intellectualization, Undoing,
}

impl DefenseMechanism {
    pub fn name(&self) -> &'static str {
        match self {
            Self::Repression => "Repression",
            Self::Sublimation => "Sublimation",
            Self::Rationalization => "Rationalization",
            Self::Projection => "Projection",
            Self::Displacement => "Displacement",
            Self::Denial => "Denial",
            Self::ReactionFormation => "ReactionFormation",
            Self::Intellectualization => "Intellectualization",
            Self::Undoing => "Undoing",
        }
    }

    pub fn energy_cost(&self) -> f64 {
        match self {
            Self::Denial => 0.1,
            Self::Projection => 0.15,
            Self::Displacement => 0.2,
            Self::Repression => 0.3,
            Self::ReactionFormation => 0.35,
            Self::Intellectualization => 0.4,
            Self::Undoing => 0.45,
            Self::Rationalization => 0.25,
            Self::Sublimation => 0.5,
        }
    }

    pub fn maturity(&self) -> u8 {
        match self {
            Self::Denial | Self::Projection => 0,
            Self::Displacement | Self::ReactionFormation => 1,
            Self::Repression | Self::Intellectualization | Self::Undoing => 2,
            Self::Sublimation | Self::Rationalization => 3,
        }
    }
}

#[derive(Debug, Clone)]
pub struct EgoState {
    pub energy: f64,
    pub baseline_energy: f64,
    pub fatigue: f64,
    pub defense_history: VecDeque<(DefenseMechanism, f64, Instant)>,
    pub delayed_impulses: VecDeque<(IdImpulse, Instant, f64)>,
    pub ego_strength: f64,
}

impl Default for EgoState {
    fn default() -> Self {
        Self {
            energy: 0.8, baseline_energy: 0.7, fatigue: 0.0,
            defense_history: VecDeque::with_capacity(100),
            delayed_impulses: VecDeque::new(), ego_strength: 0.6,
        }
    }
}

pub struct RealityArbiter {
    state: EgoState,
    defense_thresholds: HashMap<DefenseMechanism, f64>,
    max_delay: Duration,
    discount_rate: f64,
    rng: rand::rngs::StdRng,
}

impl Default for RealityArbiter {
    fn default() -> Self {
        let mut thresholds = HashMap::new();
        thresholds.insert(DefenseMechanism::Repression, 0.5);
        thresholds.insert(DefenseMechanism::Sublimation, 0.7);
        thresholds.insert(DefenseMechanism::Rationalization, 0.4);
        thresholds.insert(DefenseMechanism::Projection, 0.3);
        thresholds.insert(DefenseMechanism::Displacement, 0.4);
        thresholds.insert(DefenseMechanism::Denial, 0.2);
        thresholds.insert(DefenseMechanism::ReactionFormation, 0.6);
        thresholds.insert(DefenseMechanism::Intellectualization, 0.5);
        thresholds.insert(DefenseMechanism::Undoing, 0.45);

        Self {
            state: EgoState::default(),
            defense_thresholds: thresholds,
            max_delay: Duration::from_secs(300),
            discount_rate: 0.01,
            rng: rand::rngs::StdRng::from_entropy(),
        }
    }
}

impl RealityArbiter {
    pub fn new() -> Self { Self::default() }

    pub fn arbitrate(&mut self, impulse: &IdImpulse, constraints: &[SuperegoConstraint], reality: &RealityCheck) -> ArbitrationResult {
        let drive_value = impulse.intensity * (0.5 + 0.5 * impulse.valence);
        let moral_cost: f64 = constraints.iter().map(|c| c.severity * c.violation_cost).sum::<f64>().min(1.0);
        let reality_risk = reality.risk_level * (1.0 - reality.social_appropriateness);
        
        let net_value = 0.6 * drive_value - 0.3 * moral_cost - 0.3 * reality_risk;
        let threshold = 0.2 + 0.15 * self.state.fatigue;
        
        let decision = if net_value > threshold && reality.risk_level < 0.7 {
            ArbitrationDecision::Accept { 
                original: impulse.clone(), 
                modified: impulse.content.clone(), 
                confidence: net_value.clamp(0.0, 1.0) 
            }
        } else if net_value > 0.0 && self.state.ego_strength > 0.3 {
            let discount = (-self.discount_rate * self.max_delay.as_secs() as f64).exp();
            self.state.delayed_impulses.push_back((impulse.clone(), Instant::now(), discount));
            ArbitrationDecision::Delay { impulse: impulse.clone(), suggested_wait: self.max_delay, reason: "Reality Principle".into() }
        } else {
            let defense = self.select_defense_mechanism(impulse, moral_cost, reality_risk);
            ArbitrationDecision::Reject { 
                impulse: impulse.clone(), 
                defense, 
                defended_content: self.apply_defense(impulse, defense),
                reason: "Unacceptable impulse".into() 
            }
        };

        self.update_state(&decision);
        ArbitrationResult { decision, state_snapshot: self.state.clone() }
    }

    fn select_defense_mechanism(&mut self, impulse: &IdImpulse, moral: f64, risk: f64) -> DefenseMechanism {
        let total_p = (impulse.intensity + moral + risk) / 3.0;
        let mut available: Vec<DefenseMechanism> = self.defense_thresholds.iter()
            .filter(|(_, &t)| impulse.intensity > (t - 0.2 * total_p))
            .map(|(&d, _)| d).collect();
        
        if available.is_empty() { return DefenseMechanism::Denial; }
        let weights: Vec<f64> = available.iter().map(|d| (d.maturity() as f64).exp()).collect();
        let total_w: f64 = weights.iter().sum();
        let mut r = self.rng.gen::<f64>() * total_w;
        
        for (i, def) in available.iter().enumerate() {
            r -= weights[i];
            if r <= 0.0 { return *def; }
        }
        available[0]
    }

    fn apply_defense(&self, impulse: &IdImpulse, defense: DefenseMechanism) -> String {
        match defense {
            DefenseMechanism::Repression => format!("[repressed]"),
            DefenseMechanism::Sublimation => format!("[sublimated] {}", impulse.content),
            _ => format!("[defended]"),
        }
    }

    fn update_state(&mut self, decision: &ArbitrationDecision) {
        let cost = match decision {
            ArbitrationDecision::Accept { .. } => 0.05,
            ArbitrationDecision::Delay { .. } => 0.03,
            ArbitrationDecision::Reject { defense, .. } => defense.energy_cost(),
        };
        self.state.energy = (self.state.energy - cost).max(0.1);
        self.state.fatigue = (self.state.fatigue + cost * 0.5).min(1.0);
    }
}

pub enum ArbitrationDecision {
    Accept { original: IdImpulse, modified: String, confidence: f64 },
    Delay { impulse: IdImpulse, suggested_wait: Duration, reason: String },
    Reject { impulse: IdImpulse, defense: DefenseMechanism, defended_content: String, reason: String },
}

pub struct ArbitrationResult {
    pub decision: ArbitrationDecision,
    pub state_snapshot: EgoState,
}
