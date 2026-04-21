//! skill_compiler.rs
//! Procedural Memory – Skill Compiler.
//! Implements Anderson's ACT-R theory of skill acquisition: declarative
//! knowledge is compiled into procedural production rules through practice.
//! Strengthens frequently used productions and applies decay to unused ones.
//!
//! Theoretical foundations:
//! - Anderson (1983, 2007): ACT-R cognitive architecture.
//! - Newell & Rosenbloom (1981): Power law of practice.

use std::collections::{HashMap, VecDeque};
use std::time::{Duration, Instant};

/// A production rule representing a compiled skill.
#[derive(Debug, Clone)]
pub struct ProductionRule {
    /// Unique identifier for this rule.
    pub id: String,
    /// Condition pattern (simplified as string for this implementation).
    pub condition: String,
    /// Action to execute when condition matches.
    pub action: String,
    /// Current strength (activation) of this production.
    pub strength: f64,
    /// Number of times this production has been successfully used.
    pub usage_count: usize,
    /// Timestamp of last use.
    pub last_used: Instant,
    /// Base-level activation (from usage history).
    pub base_activation: f64,
    /// Whether this is a compiled (automatic) skill.
    pub compiled: bool,
}

impl ProductionRule {
    pub fn new(id: impl Into<String>, condition: impl Into<String>, action: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            condition: condition.into(),
            action: action.into(),
            strength: 0.1,
            usage_count: 0,
            last_used: Instant::now(),
            base_activation: 0.0,
            compiled: false,
        }
    }

    /// Update strength based on usage (power law of practice).
    /// strength = base_activation + recency_boost
    pub fn update_strength(&mut self) {
        self.usage_count += 1;
        self.last_used = Instant::now();
        
        // Power law: base activation increases with practice
        self.base_activation = (self.usage_count as f64).ln();
        
        // Strength = base + noise (simplified)
        self.strength = self.base_activation.clamp(0.1, 5.0);
        
        // Compile into automatic skill after sufficient practice
        if self.usage_count >= 5 && !self.compiled {
            self.compiled = true;
        }
    }

    /// Apply decay over time.
    pub fn decay(&mut self, decay_rate: f64) {
        let elapsed = self.last_used.elapsed().as_secs() as f64;
        self.strength = (self.strength * (-decay_rate * elapsed).exp()).max(0.1);
    }

    /// Check if this production matches a given context.
    pub fn matches(&self, context: &str) -> bool {
        context.contains(&self.condition)
    }
}

/// Skill Compiler – manages procedural knowledge.
pub struct SkillCompiler {
    productions: HashMap<String, ProductionRule>,
    /// Recently used productions for conflict resolution.
    recent_uses: VecDeque<String>,
    /// Decay rate for unused skills.
    decay_rate: f64,
    /// Compilation threshold (usage count to become automatic).
    compilation_threshold: usize,
    /// Maximum number of productions to retain.
    max_productions: usize,
}

impl Default for SkillCompiler {
    fn default() -> Self {
        Self {
            productions: HashMap::new(),
            recent_uses: VecDeque::new(),
            decay_rate: 0.5,
            compilation_threshold: 5,
            max_productions: 100,
        }
    }
}

impl SkillCompiler {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_decay_rate(mut self, rate: f64) -> Self {
        self.decay_rate = rate;
        self
    }

    pub fn with_compilation_threshold(mut self, threshold: usize) -> Self {
        self.compilation_threshold = threshold;
        self
    }

    /// Add or retrieve a production rule.
    pub fn get_or_create(&mut self, condition: &str, action: &str) -> &mut ProductionRule {
        let id = format!("{}->{}", condition, action);
        if !self.productions.contains_key(&id) {
            if self.productions.len() >= self.max_productions {
                self.evict_weakest();
            }
            self.productions.insert(id.clone(), ProductionRule::new(&id, condition, action));
        }
        self.productions.get_mut(&id).unwrap()
    }

    /// Evict the weakest production to maintain capacity.
    fn evict_weakest(&mut self) {
        let mut weakest_id = None;
        let mut weakest_strength = f64::MAX;
        for (id, prod) in &self.productions {
            if prod.strength < weakest_strength {
                weakest_strength = prod.strength;
                weakest_id = Some(id.clone());
            }
        }
        if let Some(id) = weakest_id {
            self.productions.remove(&id);
        }
    }

    /// Execute a skill: find matching production, update its strength, and return action.
    pub fn execute(&mut self, context: &str) -> Option<String> {
        // Find all matching productions
        let mut matches: Vec<&mut ProductionRule> = self.productions
            .values_mut()
            .filter(|p| p.matches(context))
            .collect();
        
        if matches.is_empty() {
            return None;
        }

        // Conflict resolution: choose highest strength
        matches.sort_by(|a, b| b.strength.partial_cmp(&a.strength).unwrap());
        // Idiomatic extraction of the best mutable match
        let best = matches.into_iter().next().unwrap();
        
        // Update usage statistics
        best.update_strength();
        self.recent_uses.push_back(best.id.clone());
        if self.recent_uses.len() > 50 {
            self.recent_uses.pop_front();
        }

        Some(best.action.clone())
    }

    /// Apply decay to all productions.
    pub fn decay_all(&mut self) {
        for prod in self.productions.values_mut() {
            prod.decay(self.decay_rate);
        }
    }

    /// Compile declarative sequence into a new production.
    pub fn compile_sequence(&mut self, condition: &str, actions: &[String]) {
        let compiled_action = actions.join("; ");
        let id = format!("compiled:{}", condition);
        let mut prod = ProductionRule::new(&id, condition, &compiled_action);
        prod.compiled = true;
        prod.strength = 1.0;
        prod.base_activation = 1.0;
        self.productions.insert(id, prod);
    }

    /// Get all compiled (automatic) skills.
    pub fn compiled_skills(&self) -> Vec<&ProductionRule> {
        self.productions.values().filter(|p| p.compiled).collect()
    }

    /// Get number of productions.
    pub fn len(&self) -> usize {
        self.productions.len()
    }

    pub fn is_empty(&self) -> bool {
        self.productions.is_empty()
    }
}
