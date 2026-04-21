//! feeling_function.rs – Jungian Feeling Function
//!
//! Implements Jung's Feeling psychological function: value-based evaluation,
//! affective judgment, and interpersonal attunement. Feeling assesses through
//! subjective valuation, seeking harmony and authentic expression.
//!
//! Theoretical Foundations:
//! - Jung (1921): "Psychological Types" – Feeling as rational function oriented
//!   by subjective values and interpersonal harmony.
//! - Damasio (1994): "Descartes' Error" – Somatic marker hypothesis.
//! - Haidt (2001): Moral foundations theory – Care, Fairness, Loyalty, Authority, Sanctity.
//!
//! Mathematical Model:
//! - Affective valence V(s) = Σ w_i * f_i(s) where f_i are foundation activations.
//! - Value congruence C(a,b) = 1 - ||v_a - v_b|| / √2
//! - Feeling tone = σ(Σ valence - dissonance)

use std::collections::{HashMap, VecDeque};
use std::time::{Duration, Instant};
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MoralFoundation {
    Care,       // Compassion, protection from harm
    Fairness,   // Justice, reciprocity, equality
    Loyalty,    // In-group commitment, patriotism
    Authority,  // Respect for tradition, hierarchy
    Sanctity,   // Purity, sacredness, disgust
    Liberty,    // Freedom, autonomy, anti-oppression
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValueProfile {
    pub foundations: HashMap<MoralFoundation, f64>,
    pub authenticity: f64,      // Congruence with true self (0-1)
    pub empathy: f64,           // Capacity for emotional resonance (0-1)
    pub harmony_seeking: f64,   // Preference for social harmony (0-1)
}

impl Default for ValueProfile {
    fn default() -> Self {
        let mut foundations = HashMap::new();
        foundations.insert(MoralFoundation::Care, 0.7);
        foundations.insert(MoralFoundation::Fairness, 0.6);
        foundations.insert(MoralFoundation::Loyalty, 0.4);
        foundations.insert(MoralFoundation::Authority, 0.3);
        foundations.insert(MoralFoundation::Sanctity, 0.3);
        foundations.insert(MoralFoundation::Liberty, 0.5);
        
        Self {
            foundations,
            authenticity: 0.6,
            empathy: 0.5,
            harmony_seeking: 0.5,
        }
    }
}

#[derive(Debug, Clone)]
pub struct AffectiveEvaluation {
    pub valence: f64,               // -1.0 (negative) to 1.0 (positive)
    pub intensity: f64,             // 0.0 to 1.0
    pub foundation_activations: HashMap<MoralFoundation, f64>,
    pub value_congruence: f64,      // How well this aligns with values
    pub emotional_tone: String,     // Descriptive label
    pub timestamp: Instant,
}

#[derive(Debug, Clone)]
pub struct FeelingMemory {
    pub evaluation: AffectiveEvaluation,
    pub context: String,
    pub decay_factor: f64,
}

pub struct FeelingFunction {
    pub name: String,
    pub values: ValueProfile,
    pub mood: f64,                  // Baseline affective state (-1.0 to 1.0)
    pub emotional_memory: VecDeque<FeelingMemory>,
    pub evaluation_history: VecDeque<AffectiveEvaluation>,
    pub max_memory: usize,
    pub sentiment_lexicon: HashMap<String, f64>,
}

impl Default for FeelingFunction {
    fn default() -> Self {
        let mut sentiment = HashMap::new();
        // Positive valence words
        for w in ["good", "great", "wonderful", "excellent", "happy", "joy", "love", 
                  "beautiful", "kind", "compassionate", "fair", "just", "honest"] {
            sentiment.insert(w.to_string(), 0.7);
        }
        // Negative valence words
        for w in ["bad", "terrible", "awful", "sad", "angry", "hate", "cruel", 
                  "unfair", "dishonest", "hurt", "suffer", "pain"] {
            sentiment.insert(w.to_string(), -0.6);
        }
        
        Self {
            name: "Feeling".to_string(),
            values: ValueProfile::default(),
            mood: 0.0,
            emotional_memory: VecDeque::with_capacity(100),
            evaluation_history: VecDeque::with_capacity(100),
            max_memory: 100,
            sentiment_lexicon: sentiment,
        }
    }
}

impl FeelingFunction {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            ..Default::default()
        }
    }

    pub fn with_value_profile(mut self, profile: ValueProfile) -> Self {
        self.values = profile;
        self
    }

    pub fn with_mood(mut self, mood: f64) -> Self {
        self.mood = mood.clamp(-1.0, 1.0);
        self
    }

    /// Evaluate content and return affective judgment.
    pub fn evaluate(&mut self, content: &str, context: Option<&str>) -> AffectiveEvaluation {
        let words: Vec<String> = content
            .to_lowercase()
            .split_whitespace()
            .map(|s| s.trim_matches(|c: char| !c.is_alphabetic()).to_string())
            .collect();
        
        // Compute lexical valence
        let mut valence_sum = 0.0;
        let mut word_count = 0;
        for word in &words {
            if let Some(&v) = self.sentiment_lexicon.get(word) {
                valence_sum += v;
                word_count += 1;
            }
        }
        let lexical_valence = if word_count > 0 {
            valence_sum / word_count as f64
        } else {
            0.0
        };

        // Activate moral foundations
        let mut foundation_activations = HashMap::new();
        for foundation in [
            MoralFoundation::Care, MoralFoundation::Fairness, MoralFoundation::Loyalty,
            MoralFoundation::Authority, MoralFoundation::Sanctity, MoralFoundation::Liberty,
        ] {
            let activation = self.activate_foundation(foundation, content);
            foundation_activations.insert(foundation, activation);
        }

        // Compute value congruence
        let value_congruence = self.compute_value_congruence(&foundation_activations);

        // Combine lexical and value-based valence
        let lexical_weight = 0.4;
        let value_weight = 0.6;
        let combined_valence = lexical_weight * lexical_valence 
                             + value_weight * value_congruence * 0.5;

        // Mood modulation
        let mood_influence = 0.2;
        let valence = (combined_valence * (1.0 - mood_influence) + self.mood * mood_influence)
            .clamp(-1.0, 1.0);

        // Intensity from activation strength and word count
        let intensity = (word_count as f64 / 20.0).min(1.0) * 0.5 
                      + foundation_activations.values().sum::<f64>() / 6.0 * 0.5;

        let emotional_tone = self.classify_emotion(valence, intensity);

        let evaluation = AffectiveEvaluation {
            valence,
            intensity,
            foundation_activations,
            value_congruence,
            emotional_tone,
            timestamp: Instant::now(),
        };

        // Store in history
        self.evaluation_history.push_back(evaluation.clone());
        if self.evaluation_history.len() > self.max_memory {
            self.evaluation_history.pop_front();
        }

        // Update mood via emotional contagion
        self.mood = (self.mood * 0.9 + valence * 0.1).clamp(-1.0, 1.0);

        evaluation
    }

    fn activate_foundation(&self, foundation: MoralFoundation, content: &str) -> f64 {
        let content_lower = content.to_lowercase();
        let keywords: &[&str] = match foundation {
            MoralFoundation::Care => &["care", "compassion", "hurt", "suffer", "pain", "help", "protect"],
            MoralFoundation::Fairness => &["fair", "just", "unfair", "equal", "cheat", "deserve"],
            MoralFoundation::Loyalty => &["loyal", "betray", "faithful", "devoted", "abandon"],
            MoralFoundation::Authority => &["respect", "disrespect", "obey", "rebel", "authority"],
            MoralFoundation::Sanctity => &["pure", "disgust", "clean", "dirty", "sacred", "profane"],
            MoralFoundation::Liberty => &["freedom", "oppress", "autonomy", "control", "liberty"],
        };

        let matches = keywords.iter().filter(|&&kw| content_lower.contains(kw)).count();
        let base_activation = (matches as f64 / keywords.len() as f64).min(1.0);
        let value_weight = *self.values.foundations.get(&foundation).unwrap_or(&0.3);
        
        base_activation * value_weight
    }

    fn compute_value_congruence(&self, activations: &HashMap<MoralFoundation, f64>) -> f64 {
        let mut dot_product = 0.0;
        let mut norm_activations = 0.0;
        let mut norm_values = 0.0;

        for foundation in self.values.foundations.keys() {
            let a = *activations.get(foundation).unwrap_or(&0.0);
            let v = *self.values.foundations.get(foundation).unwrap_or(&0.0);
            dot_product += a * v;
            norm_activations += a * a;
            norm_values += v * v;
        }

        if norm_activations < 1e-9 || norm_values < 1e-9 {
            return 0.5;
        }

        (dot_product / (norm_activations.sqrt() * norm_values.sqrt()) + 1.0) / 2.0
    }

    fn classify_emotion(&self, valence: f64, intensity: f64) -> String {
        match (valence, intensity) {
            (v, i) if v > 0.3 && i > 0.5 => "joyful".to_string(),
            (v, i) if v > 0.3 && i <= 0.5 => "content".to_string(),
            (v, i) if v > 0.1 && v <= 0.3 => "pleasant".to_string(),
            (v, _) if v < -0.3 && intensity > 0.5 => "distressed".to_string(),
            (v, _) if v < -0.3 && intensity <= 0.5 => "sad".to_string(),
            (v, _) if v < -0.1 && v >= -0.3 => "uneasy".to_string(),
            _ => "neutral".to_string(),
        }
    }

    pub fn empathize(&self, other_valence: f64, other_intensity: f64) -> f64 {
        let resonance = self.values.empathy * (1.0 - (self.mood - other_valence).abs());
        resonance * other_intensity
    }

    pub fn resolve_dissonance(&mut self, evaluations: &[AffectiveEvaluation]) -> f64 {
        if evaluations.len() < 2 {
            return 0.0;
        }
        
        let mean_valence: f64 = evaluations.iter().map(|e| e.valence).sum::<f64>() / evaluations.len() as f64;
        let variance: f64 = evaluations.iter()
            .map(|e| (e.valence - mean_valence).powi(2))
            .sum::<f64>() / evaluations.len() as f64;
        
        let dissonance = variance.sqrt();
        let resolution = self.values.harmony_seeking * (1.0 - dissonance);
        
        self.mood = (self.mood * 0.8 + mean_valence * 0.2).clamp(-1.0, 1.0);
        resolution
    }

    pub fn get_mood(&self) -> f64 {
        self.mood
    }

    pub fn get_recent_evaluations(&self, n: usize) -> Vec<AffectiveEvaluation> {
        self.evaluation_history.iter().rev().take(n).cloned().collect()
    }
}

// =============================================================================
// Tests
// =============================================================================
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_evaluate_positive_content() {
        let mut ff = FeelingFunction::new("Test");
        let eval = ff.evaluate("This is wonderful and good!", None);
        assert!(eval.valence > 0.0);
        assert!(eval.intensity > 0.0);
    }

    #[test]
    fn test_evaluate_negative_content() {
        let mut ff = FeelingFunction::new("Test");
        let eval = ff.evaluate("This is terrible and sad.", None);
        assert!(eval.valence < 0.0);
    }

    #[test]
    fn test_mood_contagion() {
        let mut ff = FeelingFunction::new("Test").with_mood(0.0);
        ff.evaluate("wonderful great excellent!", None);
        assert!(ff.mood > 0.0);
    }

    #[test]
    fn test_value_congruence() {
        let profile = ValueProfile::default();
        let mut ff = FeelingFunction::new("Test").with_value_profile(profile);
        let eval = ff.evaluate("care compassion help", None);
        assert!(eval.value_congruence > 0.5);
    }

    #[test]
    fn test_empathy_resonance() {
        let ff = FeelingFunction::new("Test");
        let resonance = ff.empathize(0.8, 0.9);
        assert!(resonance > 0.0);
    }
}
