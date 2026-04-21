//! test_rebound_monotonicity.rs
//! Property‑based tests for rebound force monotonicity.
//! Verifies that the rebound force magnitude increases with distance
//! and that the direction correctly opposes the gradient.

#[cfg(test)]
mod tests {
    use proptest::prelude::*;

    // Include the elasticity constant module directly
    include!("../../elasticity_constant.rs");

    /// Strategy to generate a valid manifold distance in [-10.0, 10.0].
    fn distance_strategy() -> impl Strategy<Value = f64> {
        -10.0..10.0
    }

    /// Strategy to generate a positive elasticity constant in [0.1, 100.0].
    fn elasticity_strategy() -> impl Strategy<Value = f64> {
        0.1..100.0
    }

    /// Strategy to generate a 2D or 3D unit gradient vector.
    fn gradient_strategy() -> impl Strategy<Value = Vec<f64>> {
        (2usize..=3).prop_flat_map(|dim| {
            prop::collection::vec(-1.0..1.0, dim).prop_map(|mut v| {
                let norm: f64 = v.iter().map(|x| x * x).sum::<f64>().sqrt();
                if norm > 1e-9 {
                    for x in &mut v {
                        *x /= norm;
                    }
                } else {
                    v[0] = 1.0;
                }
                v
            })
        })
    }

    // FIXED: Moved standard unit test outside the proptest! macro block
    #[test]
    fn samara_elasticity_less_than_artery() {
        let samara = ElasticityConstant::SAMARA;
        let artery = ElasticityConstant::ARTERY;
        assert!(samara < artery);
    }

    proptest! {
        /// Property: Rebound force magnitude is proportional to distance.
        /// |F(d)| = k * |d|
        #[test]
        fn force_magnitude_proportional_to_distance(
            distance in distance_strategy(),
            k_val in elasticity_strategy(),
        ) {
            let k = ElasticityConstant::new(k_val);
            let magnitude = rebound_magnitude(k, distance).abs();
            let expected = k_val * distance.abs();
            prop_assert!((magnitude - expected).abs() < 1e-9,
                "Force magnitude {} should equal k * |d| = {}", magnitude, expected);
        }

        /// Property: Force direction is opposite to gradient for positive distance.
        /// For d > 0, F = -k * d * ∇d, so F should be antiparallel to ∇d.
        #[test]
        fn force_direction_opposes_gradient_for_positive_distance(
            distance in (0.1..10.0),
            k_val in elasticity_strategy(),
            gradient in gradient_strategy(),
        ) {
            let k = ElasticityConstant::new(k_val);
            let magnitude = rebound_magnitude(k, distance);
            // Since magnitude = -k * d (negative), multiplying by gradient gives
            // a vector opposite to gradient.
            for &g in &gradient {
                let force_component = magnitude * g;
                // For positive distance, force component should have opposite sign to gradient
                if g.abs() > 1e-9 {
                    prop_assert!(force_component * g <= 0.0,
                        "Force component {} should oppose gradient component {}", force_component, g);
                }
            }
        }

        /// Property: Force direction aligns with gradient for negative distance.
        /// For d < 0, F = -k * d * ∇d with -k*d positive, so F is parallel to ∇d.
        #[test]
        fn force_direction_aligns_with_gradient_for_negative_distance(
            distance in (-10.0..-0.1),
            k_val in elasticity_strategy(),
            gradient in gradient_strategy(),
        ) {
            let k = ElasticityConstant::new(k_val);
            let magnitude = rebound_magnitude(k, distance);
            // magnitude is positive when distance is negative
            prop_assert!(magnitude > 0.0);
            for &g in &gradient {
                let force_component = magnitude * g;
                if g.abs() > 1e-9 {
                    prop_assert!(force_component * g >= 0.0,
                        "Force component {} should align with gradient component {}", force_component, g);
                }
            }
        }

        /// Property: Adaptive elasticity never decreases below base k
        /// and never exceeds max_multiplier * base k.
        #[test]
        fn adaptive_elasticity_bounded(
            base_k in elasticity_strategy(),
            violations in prop::collection::vec(0.0..5.0, 1..20),
        ) {
            let mut adaptive = AdaptiveElasticity::new(ElasticityConstant::new(base_k));
            for &v in &violations {
                adaptive.update(v);
            }
            let effective = adaptive.effective_k().value();
            prop_assert!(effective >= base_k,
                "Effective k {} should be >= base k {}", effective, base_k);
            prop_assert!(effective <= base_k * 5.0 + 1e-9,
                "Effective k {} should be <= max_multiplier * base k = {}", effective, base_k * 5.0);
        }

        /// Property: Applying zero violation repeatedly causes adaptive k to decay to base.
        #[test]
        fn adaptive_elasticity_decays_to_base(
            base_k in elasticity_strategy(),
            initial_violation in 1.0..5.0,
            zero_steps in 10..30usize,
        ) {
            let mut adaptive = AdaptiveElasticity::new(ElasticityConstant::new(base_k));
            adaptive.update(initial_violation);
            for _ in 0..zero_steps {
                adaptive.update(0.0);
            }
            let effective = adaptive.effective_k().value();
            // Should be close to base after sufficient decay
            prop_assert!((effective - base_k).abs() < 0.5 * base_k + 0.1,
                "Effective k {} should decay toward base k {}", effective, base_k);
        }
    }
}
