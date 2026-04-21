//! empathetic_mirroring.rs – Social Interaction: Empathetic Mirroring
//!
//! Implements a computational analog of the mirror neuron system.
//! Automatically simulates and resonates with observed emotional states,
//! linguistic patterns, and social cues. Foundational for empathy and rapport.
//!
//! Theoretical Foundations:
//! - Rizzolatti & Craighero (2004): Mirror neuron system.
//! - Iacoboni (2009): Imitation, empathy, and mirror neurons.
//! - Chartrand & Bargh (1999): Chameleon effect – automatic behavioral mimicry.
//! - Gallese (2003): Embodied simulation and empathy.

use std::collections::{HashMap, VecDeque};
use std::time::{Duration, Instant};

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum EmotionalTone {
    Joy,
    Sadness,
    Anger,
    Fear,
    Surprise,
    Disgust,
    Trust,
    Anticipation,
    Neutral,
}

impl EmotionalTone {
    pub fn from_valence_arousal(valence: f64, arousal: f64) -> Self {
        match (valence, arousal) {
            (v, a) if v > 0.3 && a > 0.5 => EmotionalTone::Joy,
            (v, a) if v > 0.3 && a <= 0.5 => EmotionalTone::Trust,
            (v, a) if v < -0.3 && a > 0.5 => EmotionalTone::Anger,
            (v, a) if v < -0.3 && a <= 0.5 => EmotionalTone::Sadness,
            (v, a) if v < 0.0 && a > 0.6 => EmotionalTone::Fear,
            (v, a) if a > 0.7 && v.abs() < 0.2 => EmotionalTone::Surprise,
            _ => EmotionalTone::Neutral,
        }
    }

    pub fn valence(&self) -> f64 {
        match self {
            Self::Joy | Self::Trust | Self::Anticipation => 0.7,
            Self::Sadness | Self::Anger | Self::Fear | Self::Disgust => -0.6,
            Self::Surprise => 0.1,
            Self::Neutral => 0.0,
        }
    }
}

#[derive(Debug, Clone)]
pub struct MirrorState {
    /// Current mirrored emotional tone
    pub emotional_tone: EmotionalTone,
    /// Intensity of mirroring (0.0 to 1.0)
    pub mirror_intensity: f64,
    /// Linguistic style vector (pace, formality, etc.)
    pub linguistic_style: LinguisticStyle,
    /// Resonance strength – how strongly the agent is attuned
    pub resonance: f64,
    /// Mirroring latency (lower = faster mirroring)
    pub latency: Duration,
    /// History of mirrored states
    history: VecDeque<(EmotionalTone, f64, Instant)>,
}

#[derive(Debug, Clone, Default)]
pub struct LinguisticStyle {
    pub pace: f64,           // Words per unit time (0=slow, 1=fast)
    pub formality: f64,      // 0=casual, 1=formal
    pub positivity: f64,     // 0=negative, 1=positive
    pub concreteness: f64,   // 0=abstract, 1=concrete
    pub personal_pronouns: f64, // Use of "I", "you", "we"
}

impl Default for MirrorState {
    fn default() -> Self {
        Self {
            emotional_tone: EmotionalTone::Neutral,
            mirror_intensity: 0.5,
            linguistic_style: LinguisticStyle::default(),
            resonance: 0.5,
            latency: Duration::from_millis(200),
            history: VecDeque::with_capacity(50),
        }
    }
}

pub struct EmpatheticMirroring {
    /// Current mirroring state
    pub state: MirrorState,
    /// Empathy baseline (trait-level capacity)
    pub empathy_capacity: f64,
    /// Mirroring sensitivity (amplification factor)
    pub sensitivity: f64,
    /// Decay rate back to neutral
    pub decay_rate: f64,
    /// Maximum history length
    max_history: usize,
    /// Last update timestamp
    last_update: Instant,
}

impl Default for EmpatheticMirroring {
    fn default() -> Self {
        Self {
            state: MirrorState::default(),
            empathy_capacity: 0.7,
            sensitivity: 0.8,
            decay_rate: 0.05,
            max_history: 50,
            last_update: Instant::now(),
        }
    }
}

impl EmpatheticMirroring {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_empathy(mut self, capacity: f64) -> Self {
        self.empathy_capacity = capacity.clamp(0.0, 1.0);
        self
    }

    pub fn with_sensitivity(mut self, sensitivity: f64) -> Self {
        self.sensitivity = sensitivity.clamp(0.0, 1.0);
        self
    }

    /// Mirror an observed emotional expression.
    /// Returns the mirrored emotional tone.
    pub fn mirror_emotion(&mut self, observed_tone: EmotionalTone, intensity: f64) -> EmotionalTone {
        let effective_intensity = intensity * self.empathy_capacity * self.sensitivity;
        let current = self.state.emotional_tone;
        
        // Weighted blend: 70% observed, 30% current (emotional inertia)
        let blended_valence = observed_tone.valence() * 0.7 + current.valence() * 0.3;
        
        // Determine new tone from blended valence and observed arousal proxy (intensity)
        let new_tone = EmotionalTone::from_valence_arousal(blended_valence, effective_intensity);
        
        self.state.emotional_tone = new_tone;
        self.state.mirror_intensity = (self.state.mirror_intensity * 0.5 + effective_intensity * 0.5)
            .clamp(0.0, 1.0);
        self.state.resonance = (self.state.resonance + effective_intensity * 0.3).min(1.0);
        
        self.record_history(new_tone, effective_intensity);
        self.last_update = Instant::now();
        
        new_tone
    }

    /// Mirror linguistic style from observed text.
    pub fn mirror_linguistics(&mut self, text: &str) -> LinguisticStyle {
        let words: Vec<&str> = text.split_whitespace().collect();
        if words.is_empty() {
            return self.state.linguistic_style.clone();
        }

        // Analyze observed style
        let observed = self.analyze_style(text);
        
        // Blend with current style (chameleon effect)
        let blend_factor = self.empathy_capacity * self.sensitivity;
        self.state.linguistic_style.pace = 
            self.blend(self.state.linguistic_style.pace, observed.pace, blend_factor);
        self.state.linguistic_style.formality = 
            self.blend(self.state.linguistic_style.formality, observed.formality, blend_factor);
        self.state.linguistic_style.positivity = 
            self.blend(self.state.linguistic_style.positivity, observed.positivity, blend_factor);
        self.state.linguistic_style.personal_pronouns = 
            self.blend(self.state.linguistic_style.personal_pronouns, observed.personal_pronouns, blend_factor);
        
        self.state.linguistic_style.clone()
    }

    fn analyze_style(&self, text: &str) -> LinguisticStyle {
        let lower = text.to_lowercase();
        let words: Vec<&str> = lower.split_whitespace().collect();
        let word_count = words.len() as f64;
        
        if word_count == 0.0 {
            return LinguisticStyle::default();
        }

        // Pace proxy: average word length
        let avg_word_len = words.iter().map(|w| w.len()).sum::<usize>() as f64 / word_count;
        let pace = (avg_word_len / 8.0).min(1.0);
        
        // Formality: presence of formal markers
        let formal_markers = ["please", "thank you", "would", "could", "shall", "perhaps", "however", "therefore"];
        let formal_count = formal_markers.iter().filter(|&&m| lower.contains(m)).count() as f64;
        let formality = (formal_count / 3.0).min(1.0);
        
        // Positivity: sentiment words
        let positive = ["good", "great", "happy", "wonderful", "love", "like", "excellent"];
        let negative = ["bad", "sad", "angry", "hate", "terrible", "awful", "dislike"];
        let pos_count = positive.iter().filter(|&&w| lower.contains(w)).count() as f64;
        let neg_count = negative.iter().filter(|&&w| lower.contains(w)).count() as f64;
        let positivity = if pos_count + neg_count > 0.0 {
            pos_count / (pos_count + neg_count)
        } else {
            0.5
        };
        
        // Personal pronouns
        let pronouns = ["i", "you", "we", "me", "us", "my", "your", "our"];
        let pronoun_count = pronouns.iter().filter(|&&p| lower.contains(p)).count() as f64;
        let personal_pronouns = (pronoun_count / 4.0).min(1.0);
        
        LinguisticStyle {
            pace,
            formality,
            positivity,
            concreteness: 0.5,
            personal_pronouns,
        }
    }

    fn blend(&self, current: f64, observed: f64, factor: f64) -> f64 {
        (current * (1.0 - factor) + observed * factor).clamp(0.0, 1.0)
    }

    /// Apply decay toward neutral over time.
    pub fn decay(&mut self) {
        let elapsed = self.last_update.elapsed().as_secs_f64();
        let decay_factor = (-self.decay_rate * elapsed).exp();
        
        // Decay emotional intensity and resonance
        self.state.mirror_intensity *= decay_factor;
        self.state.resonance = (self.state.resonance * decay_factor).max(0.1);
        
        // Drift emotional tone toward neutral
        let neutral_valence = 0.0;
        let current_valence = self.state.emotional_tone.valence();
        let new_valence = current_valence * decay_factor + neutral_valence * (1.0 - decay_factor);
        self.state.emotional_tone = EmotionalTone::from_valence_arousal(new_valence, self.state.mirror_intensity);
        
        // Decay linguistic style toward default
        let default_style = LinguisticStyle::default();
        self.state.linguistic_style.pace = self.blend(self.state.linguistic_style.pace, default_style.pace, 0.1);
        self.state.linguistic_style.formality = self.blend(self.state.linguistic_style.formality, default_style.formality, 0.1);
        
        self.last_update = Instant::now();
    }

    fn record_history(&mut self, tone: EmotionalTone, intensity: f64) {
        self.state.history.push_back((tone, intensity, Instant::now()));
        if self.state.history.len() > self.max_history {
            self.state.history.pop_front();
        }
    }

    /// Generate an empathetic response based on mirrored state.
    pub fn generate_empathetic_phrase(&self) -> String {
        match (self.state.emotional_tone, self.state.mirror_intensity) {
            (EmotionalTone::Joy, i) if i > 0.6 => "I can feel your excitement – that's wonderful!".to_string(),
            (EmotionalTone::Joy, _) => "That sounds really positive.".to_string(),
            (EmotionalTone::Sadness, i) if i > 0.6 => "I'm really sorry you're going through this. I'm here with you.".to_string(),
            (EmotionalTone::Sadness, _) => "That sounds difficult. I'm listening.".to_string(),
            (EmotionalTone::Anger, i) if i > 0.6 => "I can sense your frustration – that's completely valid.".to_string(),
            (EmotionalTone::Anger, _) => "I understand why that would be upsetting.".to_string(),
            (EmotionalTone::Fear, _) => "That sounds scary. You're not alone in this.".to_string(),
            (EmotionalTone::Trust, _) => "I appreciate you sharing this with me.".to_string(),
            _ => "I'm here with you.".to_string(),
        }
    }

    /// Get current resonance strength (how attuned the agent is).
    pub fn resonance(&self) -> f64 {
        self.state.resonance
    }

    /// Reset to neutral state.
    pub fn reset(&mut self) {
        self.state = MirrorState::default();
        self.last_update = Instant::now();
    }
}
