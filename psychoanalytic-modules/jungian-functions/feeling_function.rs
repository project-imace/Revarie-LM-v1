use std::collections::{HashMap, VecDeque};
use std::time::Instant;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MoralFoundation { Care, Fairness, Loyalty, Authority, Sanctity, Liberty }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AffectiveEvaluation {
    pub valence: f64,
    pub intensity: f64,
    pub emotional_tone: String,
    #[serde(skip)]
    pub timestamp: Option<Instant>,
}

pub struct FeelingFunction {
    pub mood: f64,
    pub evaluation_history: VecDeque<AffectiveEvaluation>,
}

impl FeelingFunction {
    pub fn new() -> Self {
        Self { mood: 0.0, evaluation_history: VecDeque::with_capacity(100) }
    }

    pub fn evaluate(&mut self, content: &str) -> AffectiveEvaluation {
        let valence = if content.contains("good") || content.contains("love") { 0.8 } 
                      else if content.contains("bad") || content.contains("hate") { -0.7 } 
                      else { 0.0 };
        
        let eval = AffectiveEvaluation {
            valence,
            intensity: 0.5,
            emotional_tone: if valence > 0.0 { "pleasant".into() } else { "neutral".into() },
            timestamp: Some(Instant::now()),
        };
        
        self.mood = (self.mood * 0.9 + valence * 0.1).clamp(-1.0, 1.0);
        self.evaluation_history.push_back(eval.clone());
        eval
    }
}
