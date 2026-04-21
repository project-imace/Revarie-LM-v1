//! elasticity_constant.rs
//! Rebound Mechanism – Elasticity Constant.
//! Defines the elasticity constant k that determines how strongly the agent
//! is pulled back toward the axiomatic manifold M. This parameter is the
//! primary differentiator between Samara (low k, organic drift) and
//! Artery (high k, rigid constraint).

use std::f64;

/// Elasticity constant for the rebound mechanism.
/// Higher values cause stronger, more immediate correction toward M.
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
pub struct ElasticityConstant {
    value: f64,
}

impl ElasticityConstant {
    /// Create a new elasticity constant.
    /// Value is clamped to [0.0, ∞).
    pub fn new(value: f64) -> Self {
        Self { value: value.max(0.0) }
    }
    
    /// Get the raw value.
    pub fn value(&self) -> f64 {
        self.value
    }
    
    /// Predefined constant for Samara (low elasticity).
    /// Allows organic, human‑like deviation before snap‑back.
    pub const SAMARA: f64 = 0.1;
    
    /// Predefined constant for Artery 1.0 (high elasticity).
    /// Results in immediate, surgical correction toward the axiomatic invariant.
    pub const ARTERY: f64 = 10.0;
    
    /// Default elasticity (neutral).
    pub const DEFAULT: f64 = 1.0;
}

impl Default for ElasticityConstant {
    fn default() -> Self {
        Self::new(Self::DEFAULT)
    }
}

/// Persona‑specific elasticity profiles.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PersonaElasticity {
    Samara,
    Artery,
    Custom(f64),
}

impl PersonaElasticity {
    /// Convert persona profile to concrete elasticity constant.
    pub fn to_constant(&self) -> ElasticityConstant {
        match self {
            PersonaElasticity::Samara => ElasticityConstant::new(ElasticityConstant::SAMARA),
            PersonaElasticity::Artery => ElasticityConstant::new(ElasticityConstant::ARTERY),
            PersonaElasticity::Custom(v) => ElasticityConstant::new(*v),
        }
    }
}

/// Compute the rebound force magnitude F = -k * distance.
/// The full vector is F * gradient.
pub fn rebound_magnitude(k: ElasticityConstant, manifold_distance: f64) -> f64 {
    -k.value() * manifold_distance
}

/// Adaptive elasticity: dynamically adjust k based on accumulated structural tension.
/// This allows the system to increase rigidity if it repeatedly violates constraints.
pub struct AdaptiveElasticity {
    base_k: ElasticityConstant,
    tension_threshold: f64,
    max_multiplier: f64,
    accumulated_tension: f64,
    decay_rate: f64,
}

impl AdaptiveElasticity {
    /// Create a new adaptive elasticity controller.
    pub fn new(base_k: ElasticityConstant) -> Self {
        Self {
            base_k,
            tension_threshold: 0.5,
            max_multiplier: 5.0,
            accumulated_tension: 0.0,
            decay_rate: 0.1,
        }
    }
    
    /// Update accumulated tension based on constraint violation.
    pub fn update(&mut self, violation: f64) {
        self.accumulated_tension = (self.accumulated_tension + violation.abs()) * (1.0 - self.decay_rate);
    }
    
    /// Get the current effective elasticity constant.
    pub fn effective_k(&self) -> ElasticityConstant {
        if self.accumulated_tension > self.tension_threshold {
            let multiplier = (1.0 + (self.accumulated_tension - self.tension_threshold))
                .min(self.max_multiplier);
            ElasticityConstant::new(self.base_k.value() * multiplier)
        } else {
            self.base_k
        }
    }
    
    /// Reset accumulated tension.
    pub fn reset(&mut self) {
        self.accumulated_tension = 0.0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_elasticity_constants() {
        assert_eq!(ElasticityConstant::SAMARA, 0.1);
        assert_eq!(ElasticityConstant::ARTERY, 10.0);
        assert_eq!(ElasticityConstant::DEFAULT, 1.0);
    }
    
    #[test]
    fn test_persona_elasticity() {
        let samara = PersonaElasticity::Samara.to_constant();
        let artery = PersonaElasticity::Artery.to_constant();
        assert_eq!(samara.value(), 0.1);
        assert_eq!(artery.value(), 10.0);
        
        let custom = PersonaElasticity::Custom(2.5).to_constant();
        assert_eq!(custom.value(), 2.5);
    }
    
    #[test]
    fn test_rebound_magnitude() {
        let k = ElasticityConstant::new(2.0);
        assert_eq!(rebound_magnitude(k, 1.0), -2.0);
        assert_eq!(rebound_magnitude(k, -0.5), 1.0);
    }
    
    #[test]
    fn test_adaptive_elasticity() {
        let mut adaptive = AdaptiveElasticity::new(ElasticityConstant::new(1.0));
        assert_eq!(adaptive.effective_k().value(), 1.0);
        
        // Accumulate tension
        adaptive.update(0.6);
        assert!(adaptive.effective_k().value() > 1.0);
        
        // Decay should reduce tension over time
        adaptive.update(0.0);
        adaptive.update(0.0);
        assert!(adaptive.accumulated_tension < 0.6);
    }
    
    #[test]
    fn test_adaptive_elasticity_reset() {
        let mut adaptive = AdaptiveElasticity::new(ElasticityConstant::new(1.0));
        adaptive.update(2.0);
        assert!(adaptive.effective_k().value() > 1.0);
        adaptive.reset();
        assert_eq!(adaptive.effective_k().value(), 1.0);
        assert_eq!(adaptive.accumulated_tension, 0.0);
    }
}
