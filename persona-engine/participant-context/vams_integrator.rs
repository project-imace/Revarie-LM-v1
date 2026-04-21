//! vams_integrator.rs – Participant Context: VAMS Integrator
//!
//! Integrates Visual Analogue Mood Scale (VAMS) data into participant context.
//! Computes mood trends, emotional trajectories, and provides mood-aware
//! response modulation for both Samara and Artery.
//!
//! Theoretical Foundations:
//! - Machado et al. (2019): VAMS mood scale validation
//! - Russell (1980): Circumplex model of affect
//! - Watson & Tellegen (1985): Two-factor model of affect (PA/NA)

use std::collections::HashMap;
use serde::{Serialize, Deserialize};

/// Six VAMS dimensions
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum VAMSDimension {
    Happy,
    Sad,
    Calm,
    Tense,
    Energetic,
    Sleepy,
}

impl VAMSDimension {
    pub fn from_q_number(q: u8) -> Option<Self> {
        match q {
            1 => Some(Self::Happy),
            2 => Some(Self::Sad),
            3 => Some(Self::Calm),
            4 => Some(Self::Tense),
            5 => Some(Self::Energetic),
            6 => Some(Self::Sleepy),
            _ => None,
        }
    }

    /// Valence: positive or negative (-1.0 to 1.0)
    pub fn valence(&self) -> f64 {
        match self {
            Self::Happy | Self::Calm => 0.8,
            Self::Sad | Self::Tense => -0.7,
            Self::Energetic => 0.3,
            Self::Sleepy => -0.2,
        }
    }

    /// Arousal: activation level (-1.0 to 1.0)
    pub fn arousal(&self) -> f64 {
        match self {
            Self::Energetic | Self::Tense => 0.7,
            Self::Happy => 0.4,
            Self::Sad | Self::Calm => -0.3,
            Self::Sleepy => -0.8,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VAMSData {
    /// Current session scores (0-100)
    pub current: HashMap<VAMSDimension, u8>,
    /// Previous session scores
    pub previous: Option<HashMap<VAMSDimension, u8>>,
    /// Pre-VAMS (before chat)
    pub pre_session: Option<HashMap<VAMSDimension, u8>>,
    /// Post-VAMS (after chat)
    pub post_session: Option<HashMap<VAMSDimension, u8>>,
    /// Session timestamp
    pub session_date: Option<String>,
    /// Day number
    pub day_number: u32,
}

impl Default for VAMSData {
    fn default() -> Self {
        Self {
            current: HashMap::new(),
            previous: None,
            pre_session: None,
            post_session: None,
            session_date: None,
            day_number: 1,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoodProfile {
    /// Overall valence (-1.0 to 1.0)
    pub valence: f64,
    /// Overall arousal (-1.0 to 1.0)
    pub arousal: f64,
    /// Positive affect component
    pub positive_affect: f64,
    /// Negative affect component
    pub negative_affect: f64,
    /// Mood stability (inverse of volatility)
    pub stability: f64,
    /// Trend direction (+ improving, - declining, 0 stable)
    pub trend: f64,
}

impl Default for MoodProfile {
    fn default() -> Self {
        Self {
            valence: 0.0,
            arousal: 0.0,
            positive_affect: 0.5,
            negative_affect: 0.5,
            stability: 0.5,
            trend: 0.0,
        }
    }
}

/// Integrates VAMS data and provides mood-aware response modulation.
pub struct VAMSIntegrator {
    /// Historical VAMS data for participant
    history: Vec<VAMSData>,
    /// Current mood profile
    profile: MoodProfile,
    /// Persona (samara/artery) for response modulation
    persona: String,
    /// Maximum history length
    max_history: usize,
}

impl VAMSIntegrator {
    pub fn new(persona: impl Into<String>) -> Self {
        Self {
            history: Vec::new(),
            profile: MoodProfile::default(),
            persona: persona.into(),
            max_history: 14,
        }
    }

    /// Update with new VAMS data.
    pub fn update(&mut self, data: VAMSData) {
        self.history.push(data.clone());
        if self.history.len() > self.max_history {
            self.history.remove(0);
        }
        self.profile = self.compute_profile(&data);
    }

    /// Compute current mood profile from VAMS data.
    fn compute_profile(&self, current: &VAMSData) -> MoodProfile {
        let mut profile = MoodProfile::default();

        if current.current.is_empty() {
            return profile;
        }

        // Compute valence and arousal from current VAMS
        let mut valence_sum = 0.0;
        let mut arousal_sum = 0.0;
        let mut count = 0;

        for (dim, &score) in &current.current {
            let normalized = score as f64 / 100.0;
            valence_sum += dim.valence() * normalized;
            arousal_sum += dim.arousal() * normalized;
            count += 1;
        }

        if count > 0 {
            profile.valence = (valence_sum / count as f64).clamp(-1.0, 1.0);
            profile.arousal = (arousal_sum / count as f64).clamp(-1.0, 1.0);
        }

        // Compute positive/negative affect
        profile.positive_affect = self.compute_positive_affect(current);
        profile.negative_affect = self.compute_negative_affect(current);

        // Compute trend if previous available
        if let Some(prev) = &current.previous {
            profile.trend = self.compute_trend(current, prev);
        } else if self.history.len() >= 2 {
            let prev = &self.history[self.history.len() - 2];
            profile.trend = self.compute_trend(current, prev);
        }

        // Compute stability from historical variance
        profile.stability = self.compute_stability();

        profile
    }

    fn compute_positive_affect(&self, data: &VAMSData) -> f64 {
        let pos_dims = [VAMSDimension::Happy, VAMSDimension::Calm, VAMSDimension::Energetic];
        let mut sum = 0.0;
        let mut count = 0;

        for dim in pos_dims {
            if let Some(&score) = data.current.get(&dim) {
                sum += score as f64 / 100.0;
                count += 1;
            }
        }

        if count > 0 {
            (sum / count as f64).clamp(0.0, 1.0)
        } else {
            0.5
        }
    }

    fn compute_negative_affect(&self, data: &VAMSData) -> f64 {
        let neg_dims = [VAMSDimension::Sad, VAMSDimension::Tense, VAMSDimension::Sleepy];
        let mut sum = 0.0;
        let mut count = 0;

        for dim in neg_dims {
            if let Some(&score) = data.current.get(&dim) {
                sum += score as f64 / 100.0;
                count += 1;
            }
        }

        if count > 0 {
            (sum / count as f64).clamp(0.0, 1.0)
        } else {
            0.5
        }
    }

    fn compute_trend(&self, current: &VAMSData, previous: &VAMSData) -> f64 {
        let mut diff_sum = 0.0;
        let mut count = 0;

        for dim in &[
            VAMSDimension::Happy,
            VAMSDimension::Sad,
            VAMSDimension::Calm,
            VAMSDimension::Tense,
            VAMSDimension::Energetic,
            VAMSDimension::Sleepy,
        ] {
            if let (Some(&curr), Some(&prev)) = (current.current.get(dim), previous.current.get(dim)) {
                diff_sum += (curr as f64 - prev as f64) / 100.0;
                count += 1;
            }
        }

        if count > 0 {
            (diff_sum / count as f64).clamp(-1.0, 1.0)
        } else {
            0.0
        }
    }

    fn compute_stability(&self) -> f64 {
        if self.history.len() < 3 {
            return 0.5;
        }

        let recent: Vec<f64> = self.history.iter()
            .rev()
            .take(5)
            .filter_map(|d| {
                if d.current.is_empty() {
                    None
                } else {
                    let mut sum = 0.0;
                    for (&score, _) in d.current.iter() {
                        sum += score as f64;
                    }
                    Some(sum / d.current.len() as f64)
                }
            })
            .collect();

        if recent.len() < 2 {
            return 0.5;
        }

        let mean = recent.iter().sum::<f64>() / recent.len() as f64;
        let variance = recent.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / recent.len() as f64;
        let volatility = variance.sqrt() / 100.0;

        (1.0 - volatility).clamp(0.0, 1.0)
    }

    /// Get recommended response modulation based on mood.
    pub fn get_response_modulation(&self) -> ResponseModulation {
        let mut mod_params = ResponseModulation::default();

        if self.persona == "samara" {
            // Samara is empathetic and responsive to mood
            if self.profile.valence < -0.3 {
                mod_params.warmth_boost = 0.2;
                mod_params.supportive_language = true;
                mod_params.acknowledge_emotion = true;
            } else if self.profile.valence > 0.3 {
                mod_params.warmth_boost = 0.1;
                mod_params.celebratory_tone = true;
            }

            if self.profile.arousal > 0.5 {
                mod_params.pacing = "calming".to_string();
            }

            if self.profile.trend < -0.2 {
                mod_params.supportive_language = true;
                mod_params.check_in = true;
            }
        } else {
            // Artery is functional, minimal modulation
            if self.profile.negative_affect > 0.7 {
                mod_params.efficiency_boost = 0.1;
                mod_params.direct_response = true;
            }
        }

        mod_params
    }

    /// Get current mood profile.
    pub fn get_profile(&self) -> &MoodProfile {
        &self.profile
    }

    /// Get historical VAMS data.
    pub fn get_history(&self) -> &[VAMSData] {
        &self.history
    }

    /// Get a natural language description of current mood.
    pub fn mood_description(&self) -> String {
        let valence_desc = if self.profile.valence > 0.3 {
            "positive"
        } else if self.profile.valence < -0.3 {
            "negative"
        } else {
            "neutral"
        };

        let arousal_desc = if self.profile.arousal > 0.4 {
            "energetic"
        } else if self.profile.arousal < -0.4 {
            "low-energy"
        } else {
            "calm"
        };

        let trend_desc = if self.profile.trend > 0.2 {
            "improving"
        } else if self.profile.trend < -0.2 {
            "declining"
        } else {
            "stable"
        };

        format!("{} {} mood, {}", valence_desc, arousal_desc, trend_desc)
    }
}

#[derive(Debug, Clone, Default)]
pub struct ResponseModulation {
    pub warmth_boost: f64,
    pub supportive_language: bool,
    pub acknowledge_emotion: bool,
    pub celebratory_tone: bool,
    pub pacing: String,
    pub efficiency_boost: f64,
    pub direct_response: bool,
    pub check_in: bool,
}

// =============================================================================
// Tests
// =============================================================================
