//! test_elasticity.rs
//! Unit tests for Elasticity Constant and Adaptive Elasticity.

#[cfg(test)]
mod tests {
    include!("../elasticity_constant.rs");

    #[test]
    fn test_elasticity_clamping() {
        let k = ElasticityConstant::new(-5.0);
        assert_eq!(k.value(), 0.0);
        
        let k2 = ElasticityConstant::new(3.0);
        assert_eq!(k2.value(), 3.0);
    }

    #[test]
    fn test_persona_elasticity_values() {
        let samara = PersonaElasticity::Samara.to_constant();
        let artery = PersonaElasticity::Artery.to_constant();
        let custom = PersonaElasticity::Custom(2.5).to_constant();
        
        assert_eq!(samara.value(), 0.1);
        assert_eq!(artery.value(), 10.0);
        assert_eq!(custom.value(), 2.5);
    }

    #[test]
    fn test_rebound_magnitude_sign() {
        let k = ElasticityConstant::new(2.0);
        
        // Positive distance (outside) -> negative force (pull inward)
        assert!(rebound_magnitude(k, 1.0) < 0.0);
        // Negative distance (inside) -> positive force (push outward)
        assert!(rebound_magnitude(k, -1.0) > 0.0);
        // Zero distance -> zero force
        assert_eq!(rebound_magnitude(k, 0.0), 0.0);
    }

    #[test]
    fn test_adaptive_elasticity_threshold() {
        let mut adaptive = AdaptiveElasticity::new(ElasticityConstant::new(1.0));
        
        // Below threshold -> base k
        adaptive.update(0.3);
        assert_eq!(adaptive.effective_k().value(), 1.0);
        
        // Above threshold -> increased k
        adaptive.update(0.4);
        assert!(adaptive.effective_k().value() > 1.0);
    }

    #[test]
    fn test_adaptive_elasticity_max_multiplier() {
        let mut adaptive = AdaptiveElasticity::new(ElasticityConstant::new(1.0));
        
        // Accumulate massive tension
        for _ in 0..100 {
            adaptive.update(10.0);
        }
        // Should cap at max_multiplier * base_k
        assert!(adaptive.effective_k().value() <= 5.0 * 1.0 + 1e-9);
    }

    #[test]
    fn test_adaptive_elasticity_decay() {
        let mut adaptive = AdaptiveElasticity::new(ElasticityConstant::new(1.0));
        adaptive.update(2.0);
        let k_high = adaptive.effective_k().value();
        
        // Decay over several cycles with zero violation
        for _ in 0..20 {
            adaptive.update(0.0);
        }
        let k_low = adaptive.effective_k().value();
        assert!(k_low < k_high);
    }

    #[test]
    fn test_default_elasticity() {
        let default_k = ElasticityConstant::default();
        assert_eq!(default_k.value(), 1.0);
    }

    #[test]
    fn test_partial_ordering() {
        let k1 = ElasticityConstant::new(1.0);
        let k2 = ElasticityConstant::new(2.0);
        assert!(k1 < k2);
        assert!(k2 > k1);
    }
}
