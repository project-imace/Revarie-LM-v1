//! lagrangian_multiplier.rs
//! Belief Space – Lagrangian Multiplier for Constrained Optimization.
//! Implements the method of Lagrange multipliers to enforce constraints
//! on the belief manifold M. This is the mathematical foundation for the
//! "rebound" mechanism that keeps the agent within its axiomatic bounds.

use std::f64;

/// A constraint function g(x) = 0 that defines the admissible region.
pub trait Constraint {
    /// Evaluate the constraint at point x.
    fn evaluate(&self, x: &[f64]) -> f64;
    
    /// Compute the gradient of the constraint at point x.
    fn gradient(&self, x: &[f64]) -> Vec<f64>;
    
    /// Dimension of the space this constraint operates on.
    fn dimension(&self) -> usize;
}

/// A spherical constraint: ||x||² = R².
pub struct SphericalConstraint {
    radius: f64,
    dim: usize,
}

impl SphericalConstraint {
    pub fn new(radius: f64, dimension: usize) -> Self {
        Self { radius, dim: dimension }
    }
}

impl Constraint for SphericalConstraint {
    fn evaluate(&self, x: &[f64]) -> f64 {
        let norm_sq: f64 = x.iter().map(|&xi| xi * xi).sum();
        norm_sq - self.radius * self.radius
    }
    
    fn gradient(&self, x: &[f64]) -> Vec<f64> {
        x.iter().map(|&xi| 2.0 * xi).collect()
    }
    
    fn dimension(&self) -> usize {
        self.dim
    }
}

/// A linear constraint: a·x = b.
pub struct LinearConstraint {
    coefficients: Vec<f64>,
    target: f64,
}

impl LinearConstraint {
    pub fn new(coefficients: Vec<f64>, target: f64) -> Self {
        Self { coefficients, target }
    }
}

impl Constraint for LinearConstraint {
    fn evaluate(&self, x: &[f64]) -> f64 {
        x.iter().zip(&self.coefficients).map(|(xi, &ai)| xi * ai).sum::<f64>() - self.target
    }
    
    fn gradient(&self, _x: &[f64]) -> Vec<f64> {
        self.coefficients.clone()
    }
    
    fn dimension(&self) -> usize {
        self.coefficients.len()
    }
}

/// Lagrangian multiplier state for constrained optimization.
#[derive(Debug, Clone)]
pub struct LagrangianMultiplier {
    /// Current value of the multiplier λ.
    lambda: f64,
    /// Learning rate for multiplier updates.
    learning_rate: f64,
    /// Damping factor to prevent oscillations.
    damping: f64,
    /// Previous lambda for momentum.
    prev_lambda: f64,
    /// Accumulated constraint violation for integral term.
    integral_error: f64,
    /// Integral gain (for PID-like control).
    integral_gain: f64,
}

impl Default for LagrangianMultiplier {
    fn default() -> Self {
        Self {
            lambda: 0.0,
            learning_rate: 0.1,
            damping: 0.9,
            prev_lambda: 0.0,
            integral_error: 0.0,
            integral_gain: 0.01,
        }
    }
}

impl LagrangianMultiplier {
    pub fn new() -> Self {
        Self::default()
    }
    
    pub fn with_learning_rate(mut self, lr: f64) -> Self {
        self.learning_rate = lr;
        self
    }
    
    pub fn with_damping(mut self, d: f64) -> Self {
        self.damping = d;
        self
    }
    
    pub fn with_integral_gain(mut self, ig: f64) -> Self {
        self.integral_gain = ig;
        self
    }
    
    /// Update the multiplier based on constraint violation.
    /// λ_{t+1} = λ_t + η * g(x) + β * (λ_t - λ_{t-1}) + ki * ∫g(x)
    pub fn update(&mut self, constraint_value: f64) {
        self.integral_error += constraint_value;
        let delta = self.learning_rate * constraint_value
                  + self.integral_gain * self.integral_error;
        let momentum = self.damping * (self.lambda - self.prev_lambda);
        self.prev_lambda = self.lambda;
        self.lambda += delta + momentum;
    }
    
    /// Get the current multiplier value.
    pub fn value(&self) -> f64 {
        self.lambda
    }
    
    /// Reset the multiplier state.
    pub fn reset(&mut self) {
        self.lambda = 0.0;
        self.prev_lambda = 0.0;
        self.integral_error = 0.0;
    }
    
    /// Compute the Lagrangian L(x, λ) = f(x) + λ * g(x).
    /// Here f(x) is the objective function value.
    pub fn lagrangian(&self, objective: f64, constraint_value: f64) -> f64 {
        objective + self.lambda * constraint_value
    }
    
    /// Compute the gradient of the Lagrangian with respect to x.
    /// ∇_x L = ∇f(x) + λ * ∇g(x).
    pub fn lagrangian_gradient(
        &self,
        obj_grad: &[f64],
        constraint_grad: &[f64],
    ) -> Vec<f64> {
        obj_grad.iter()
            .zip(constraint_grad)
            .map(|(&df, &dg)| df + self.lambda * dg)
            .collect()
    }
}

/// A constrained optimizer that uses Lagrangian multipliers.
pub struct ConstrainedOptimizer<C: Constraint> {
    constraint: C,
    multiplier: LagrangianMultiplier,
    max_iterations: usize,
    tolerance: f64,
    step_size: f64, // FIXED: Exposed step_size to prevent overshoot
}

impl<C: Constraint> ConstrainedOptimizer<C> {
    pub fn new(constraint: C) -> Self {
        Self {
            constraint,
            multiplier: LagrangianMultiplier::new(),
            max_iterations: 100,
            tolerance: 1e-6,
            step_size: 0.05, 
        }
    }
    
    pub fn with_multiplier(mut self, mult: LagrangianMultiplier) -> Self {
        self.multiplier = mult;
        self
    }
    
    pub fn with_max_iterations(mut self, max_iter: usize) -> Self {
        self.max_iterations = max_iter;
        self
    }
    
    pub fn with_tolerance(mut self, tol: f64) -> Self {
        self.tolerance = tol;
        self
    }

    pub fn with_step_size(mut self, step: f64) -> Self {
        self.step_size = step;
        self
    }
    
    /// Project a point onto the constraint manifold using Lagrangian method.
    /// Solves: min ||x - x0||² subject to g(x) = 0.
    pub fn project(&mut self, x0: &[f64]) -> Vec<f64> {
        let dim = self.constraint.dimension();
        assert_eq!(x0.len(), dim, "Dimension mismatch");
        
        let mut x = x0.to_vec();
        self.multiplier.reset();
        
        for _ in 0..self.max_iterations {
            let g_val = self.constraint.evaluate(&x);
            
            // Check convergence
            if g_val.abs() < self.tolerance {
                break;
            }
            
            // Update multiplier
            self.multiplier.update(g_val);
            
            // Objective gradient for ||x - x0||² is 2(x - x0)
            let obj_grad: Vec<f64> = x.iter().zip(x0).map(|(&xi, &x0i)| 2.0 * (xi - x0i)).collect();
            let constraint_grad = self.constraint.gradient(&x);
            
            // Lagrangian gradient
            let lag_grad = self.multiplier.lagrangian_gradient(&obj_grad, &constraint_grad);
            
            // Update x: x_{t+1} = x_t - α * ∇_x L
            for i in 0..dim {
                x[i] -= self.step_size * lag_grad[i];
            }
        }
        x
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_spherical_constraint() {
        let constraint = SphericalConstraint::new(1.0, 2);
        let x = vec![0.6, 0.8];
        assert!((constraint.evaluate(&x) - 0.0).abs() < 1e-9);
        
        let grad = constraint.gradient(&x);
        assert_eq!(grad, vec![1.2, 1.6]);
    }
    
    #[test]
    fn test_linear_constraint() {
        let constraint = LinearConstraint::new(vec![1.0, -1.0], 0.0);
        let x = vec![2.0, 2.0];
        assert_eq!(constraint.evaluate(&x), 0.0);
        assert_eq!(constraint.gradient(&x), vec![1.0, -1.0]);
    }
    
    #[test]
    fn test_lagrangian_update() {
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
    fn test_constrained_projection() {
        let constraint = SphericalConstraint::new(1.0, 2);
        let mut optimizer = ConstrainedOptimizer::new(constraint)
            .with_max_iterations(1000)
            .with_tolerance(1e-8)
            .with_step_size(0.05); // Use the new configurable step
        
        let x0 = vec![2.0, 0.0];
        let proj = optimizer.project(&x0);
        
        let norm: f64 = proj.iter().map(|&xi| xi * xi).sum();
        assert!((norm.sqrt() - 1.0).abs() < 1e-6);
        assert!((proj[0] - 1.0).abs() < 1e-6);
    }
    
    #[test]
    fn test_lagrangian_calculation() {
        let lm = LagrangianMultiplier::new();
        let objective = 5.0;
        let constraint_val = 2.0;
        let lag = lm.lagrangian(objective, constraint_val);
        assert_eq!(lag, 5.0);
        
        let mut lm2 = LagrangianMultiplier::new();
        lm2.update(2.0);
        let lag2 = lm2.lagrangian(objective, constraint_val);
        assert_eq!(lag2, 5.0 + 0.2 * 2.0);
    }
}
