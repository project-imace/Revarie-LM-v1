//! test_lagrangian.rs
//! Unit tests for Lagrangian Multiplier and Constrained Optimizer.

#[cfg(test)]
mod tests {
    use std::f64;

    // Include the source file directly for testing
    include!("../lagrangian_multiplier.rs");

    #[test]
    fn test_spherical_constraint_evaluate() {
        let constraint = SphericalConstraint::new(1.0, 2);
        let x = vec![0.6, 0.8];
        assert!((constraint.evaluate(&x) - 0.0).abs() < 1e-9);
        
        let x2 = vec![2.0, 0.0];
        assert!((constraint.evaluate(&x2) - 3.0).abs() < 1e-9);
    }

    #[test]
    fn test_spherical_constraint_gradient() {
        let constraint = SphericalConstraint::new(1.0, 2);
        let x = vec![0.6, 0.8];
        let grad = constraint.gradient(&x);
        assert_eq!(grad, vec![1.2, 1.6]);
    }

    #[test]
    fn test_linear_constraint_evaluate() {
        let constraint = LinearConstraint::new(vec![1.0, -1.0], 0.0);
        let x = vec![2.0, 2.0];
        assert_eq!(constraint.evaluate(&x), 0.0);
        
        let x2 = vec![3.0, 2.0];
        assert_eq!(constraint.evaluate(&x2), 1.0);
    }

    #[test]
    fn test_linear_constraint_gradient() {
        let constraint = LinearConstraint::new(vec![1.0, -1.0], 0.0);
        let x = vec![2.0, 2.0];
        let grad = constraint.gradient(&x);
        assert_eq!(grad, vec![1.0, -1.0]);
    }

    #[test]
    fn test_lagrangian_multiplier_update() {
        let mut lm = LagrangianMultiplier::new()
            .with_learning_rate(0.1)
            .with_damping(0.0)
            .with_integral_gain(0.0);
        
        lm.update(1.0);
        assert!((lm.value() - 0.1).abs() < 1e-9);
        
        lm.update(0.5);
        assert!((lm.value() - 0.15).abs() < 1e-9);
    }

    #[test]
    fn test_lagrangian_multiplier_with_damping() {
        let mut lm = LagrangianMultiplier::new()
            .with_learning_rate(0.1)
            .with_damping(0.5)
            .with_integral_gain(0.0);
        
        lm.update(1.0);
        let first = lm.value();
        lm.update(1.0);
        let second = lm.value();
        // Damping should smooth the update
        assert!(second > first);
    }

    #[test]
    fn test_lagrangian_multiplier_with_integral() {
        let mut lm = LagrangianMultiplier::new()
            .with_learning_rate(0.1)
            .with_damping(0.0)
            .with_integral_gain(0.05);
        
        lm.update(1.0);
        let first = lm.value();
        lm.update(1.0);
        let second = lm.value();
        // Integral term should cause larger second update
        assert!(second - first > 0.01);
    }

    #[test]
    fn test_lagrangian_calculation() {
        let lm = LagrangianMultiplier::new();
        let objective = 5.0;
        let constraint_val = 2.0;
        let lag = lm.lagrangian(objective, constraint_val);
        assert_eq!(lag, 5.0);
        
        // FIXED: Zeroed out integral_gain and damping for strict math matching
        let mut lm2 = LagrangianMultiplier::new()
            .with_learning_rate(0.1)
            .with_damping(0.0)
            .with_integral_gain(0.0);
        lm2.update(2.0);
        let lag2 = lm2.lagrangian(objective, constraint_val);
        assert!((lag2 - (5.0 + 0.2 * 2.0)).abs() < 1e-9);
    }

    #[test]
    fn test_lagrangian_gradient() {
        let lm = LagrangianMultiplier::new();
        let obj_grad = vec![1.0, 2.0];
        let constraint_grad = vec![0.5, 0.5];
        let lag_grad = lm.lagrangian_gradient(&obj_grad, &constraint_grad);
        assert_eq!(lag_grad, vec![1.0, 2.0]);
        
        // FIXED: Zeroed out integral_gain and damping for strict math matching
        let mut lm2 = LagrangianMultiplier::new()
            .with_learning_rate(0.1)
            .with_damping(0.0)
            .with_integral_gain(0.0);
        lm2.update(4.0); // lambda is now exactly 0.4
        let lag_grad2 = lm2.lagrangian_gradient(&obj_grad, &constraint_grad);
        assert!((lag_grad2[0] - (1.0 + 0.4 * 0.5)).abs() < 1e-9);
        assert!((lag_grad2[1] - (2.0 + 0.4 * 0.5)).abs() < 1e-9);
    }

    #[test]
    fn test_constrained_projection_spherical() {
        let constraint = SphericalConstraint::new(1.0, 2);
        let mut optimizer = ConstrainedOptimizer::new(constraint)
            .with_max_iterations(1000)
            .with_tolerance(1e-8)
            .with_step_size(0.05);
        
        let x0 = vec![2.0, 0.0];
        let proj = optimizer.project(&x0);
        
        let norm: f64 = proj.iter().map(|&xi| xi * xi).sum();
        assert!((norm.sqrt() - 1.0).abs() < 1e-6);
        assert!((proj[0] - 1.0).abs() < 1e-6);
    }

    #[test]
    fn test_constrained_projection_linear() {
        let constraint = LinearConstraint::new(vec![1.0, 1.0], 2.0);
        let mut optimizer = ConstrainedOptimizer::new(constraint)
            .with_max_iterations(1000)
            .with_tolerance(1e-8)
            .with_step_size(0.05);
        
        let x0 = vec![3.0, 3.0];
        let proj = optimizer.project(&x0);
        
        // Should satisfy x1 + x2 = 2.0
        assert!((proj[0] + proj[1] - 2.0).abs() < 1e-6);
        // Should be close to original point while satisfying constraint
        assert!((proj[0] - 1.0).abs() < 1e-6);
        assert!((proj[1] - 1.0).abs() < 1e-6);
    }

    #[test]
    fn test_multiplier_reset() {
        let mut lm = LagrangianMultiplier::new();
        lm.update(1.0);
        lm.update(1.0);
        assert!(lm.value() > 0.0);
        
        lm.reset();
        assert_eq!(lm.value(), 0.0);
        assert_eq!(lm.integral_error, 0.0);
    }

    #[test]
    fn test_constrained_projection_convergence() {
        let constraint = SphericalConstraint::new(2.0, 3);
        let mut optimizer = ConstrainedOptimizer::new(constraint)
            .with_max_iterations(500)
            .with_tolerance(1e-6)
            .with_step_size(0.03);
        
        let x0 = vec![5.0, 0.0, 0.0];
        let proj = optimizer.project(&x0);
        
        let norm: f64 = proj.iter().map(|&xi| xi * xi).sum();
        assert!((norm.sqrt() - 2.0).abs() < 1e-5);
    }
}
