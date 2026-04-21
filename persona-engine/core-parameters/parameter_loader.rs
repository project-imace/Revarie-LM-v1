//! parameter_loader.rs – Persona Engine: Parameter Loader
//!
//! Loads and validates persona configuration parameters from JSON, YAML, and TOML.
//! Provides runtime access to persona vectors, cognitive depth settings, and
//! anthropomorphism levels for both Samara and Artery.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnthropomorphismParams {
    pub warmth: f64,
    pub empathy: f64,
    pub curiosity: f64,
    pub formality: f64,
    pub playfulness: f64,
    pub directness: f64,
    pub emotional_expressiveness: f64,
}

impl Default for AnthropomorphismParams {
    fn default() -> Self {
        Self {
            warmth: 0.5, empathy: 0.5, curiosity: 0.5, formality: 0.5,
            playfulness: 0.5, directness: 0.5, emotional_expressiveness: 0.5,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CognitiveStyleParams {
    pub system1_weight: f64,
    pub system2_weight: f64,
    pub reasoning_depth: f64,
    pub ambiguity_tolerance: f64,
    pub certainty_threshold: f64,
}

impl Default for CognitiveStyleParams {
    fn default() -> Self {
        Self {
            system1_weight: 0.5, system2_weight: 0.5, reasoning_depth: 0.5,
            ambiguity_tolerance: 0.5, certainty_threshold: 0.5,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SocialOrientationParams {
    pub use_participant_name: bool,
    pub first_person_pronouns: bool,
    pub relational_continuity: f64,
    pub emotional_mirroring: f64,
    pub rapport_building: f64,
    pub self_disclosure: f64,
}

impl Default for SocialOrientationParams {
    fn default() -> Self {
        Self {
            use_participant_name: true, first_person_pronouns: true,
            relational_continuity: 0.5, emotional_mirroring: 0.5,
            rapport_building: 0.5, self_disclosure: 0.5,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryConsolidationParams {
    pub summary_style: String,
    pub include_emotional_tags: bool,
    pub include_name_in_summary: bool,
    pub recency_boost: f64,
    pub emotional_salience_boost: f64,
}

impl Default for MemoryConsolidationParams {
    fn default() -> Self {
        Self {
            summary_style: "neutral".to_string(), include_emotional_tags: true,
            include_name_in_summary: true, recency_boost: 0.1, emotional_salience_boost: 0.1,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AffectiveModulationParams {
    pub dopamine_baseline: f64,
    pub serotonin_baseline: f64,
    pub norepinephrine_baseline: f64,
    pub acetylcholine_baseline: f64,
    pub emotional_contagion_rate: f64,
    pub mood_recovery_rate: f64,
}

impl Default for AffectiveModulationParams {
    fn default() -> Self {
        Self {
            dopamine_baseline: 0.5, serotonin_baseline: 0.5, norepinephrine_baseline: 0.5,
            acetylcholine_baseline: 0.5, emotional_contagion_rate: 0.1, mood_recovery_rate: 0.2,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReboundParams {
    pub elasticity_constant_k: f64,
    pub max_deviation_tolerance: f64,
    pub rebound_damping: f64,
}

impl Default for ReboundParams {
    fn default() -> Self {
        Self { elasticity_constant_k: 1.0, max_deviation_tolerance: 0.2, rebound_damping: 0.8 }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonaVector {
    pub persona_id: String,
    pub name: String,
    pub description: String,
    pub version: String,
    pub anthropomorphism: AnthropomorphismParams,
    pub cognitive_style: CognitiveStyleParams,
    pub social_orientation: SocialOrientationParams,
    pub memory_consolidation: MemoryConsolidationParams,
    pub affective_modulation: AffectiveModulationParams,
    pub rebound_mechanism: ReboundParams,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CognitiveDepthConfig {
    pub version: String,
    pub default: DepthSettings,
    pub persona_overrides: HashMap<String, DepthSettings>,
    pub task_specific: HashMap<String, DepthSettings>,
    pub runtime_modulation: ModulationSettings,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DepthSettings {
    pub max_reasoning_steps: usize,
    pub inference_depth: usize,
    pub counterfactual_branches: usize,
    pub verification_passes: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModulationSettings {
    pub fatigue_factor: f64,
    pub time_pressure_factor: f64,
    pub cognitive_load_threshold: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnthropomorphismLevelConfig {
    pub version: String,
    pub dimensions: HashMap<String, DimensionDef>,
    pub profiles: HashMap<String, ProfileValues>,
    pub linguistic_markers: HashMap<String, Vec<String>>,
    pub behavioral_cues: HashMap<String, BehavioralCues>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DimensionDef {
    pub min: f64,
    pub max: f64,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProfileValues {
    pub warmth: f64,
    pub empathy: f64,
    pub agency: f64,
    pub experience: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BehavioralCues {
    pub use_name: bool,
    pub first_person: bool,
    pub ask_followup: bool,
    pub express_curiosity: bool,
}

pub struct ParameterLoader {
    config_root: PathBuf,
    samara_vector: Arc<PersonaVector>,
    artery_vector: Arc<PersonaVector>,
    cognitive_depth: Arc<CognitiveDepthConfig>,
    anthropomorphism_levels: Arc<AnthropomorphismLevelConfig>,
}

impl ParameterLoader {
    pub fn new<P: AsRef<Path>>(config_root: P) -> Result<Self, Box<dyn std::error::Error>> {
        let root = config_root.as_ref().to_path_buf();
        
        let samara_path = root.join("persona_vector_samara.json");
        let artery_path = root.join("persona_vector_artery.json");
        let depth_path = root.join("cognitive_depth.yaml");
        let anthro_path = root.join("anthropomorphism_level.toml");
        
        let samara_content = fs::read_to_string(&samara_path)?;
        let artery_content = fs::read_to_string(&artery_path)?;
        let depth_content = fs::read_to_string(&depth_path)?;
        let anthro_content = fs::read_to_string(&anthro_path)?;
        
        let samara_vector: PersonaVector = serde_json::from_str(&samara_content)?;
        let artery_vector: PersonaVector = serde_json::from_str(&artery_content)?;
        let cognitive_depth: CognitiveDepthConfig = serde_yaml::from_str(&depth_content)?;
        let anthropomorphism_levels: AnthropomorphismLevelConfig = toml::from_str(&anthro_content)?;
        
        Ok(Self {
            config_root: root,
            samara_vector: Arc::new(samara_vector),
            artery_vector: Arc::new(artery_vector),
            cognitive_depth: Arc::new(cognitive_depth),
            anthropomorphism_levels: Arc::new(anthropomorphism_levels),
        })
    }

    pub fn get_persona(&self, persona: &str) -> Option<Arc<PersonaVector>> {
        match persona.to_lowercase().as_str() {
            "samara" => Some(self.samara_vector.clone()),
            "artery" => Some(self.artery_vector.clone()),
            _ => None,
        }
    }

    pub fn get_persona_by_study_group(&self, study_group: &str) -> Option<Arc<PersonaVector>> {
        match study_group {
            "A" => Some(self.samara_vector.clone()),
            "B" => Some(self.artery_vector.clone()),
            _ => None,
        }
    }

    pub fn samara(&self) -> Arc<PersonaVector> {
        self.samara_vector.clone()
    }

    pub fn artery(&self) -> Arc<PersonaVector> {
        self.artery_vector.clone()
    }

    pub fn cognitive_depth(&self) -> Arc<CognitiveDepthConfig> {
        self.cognitive_depth.clone()
    }

    pub fn anthropomorphism_levels(&self) -> Arc<AnthropomorphismLevelConfig> {
        self.anthropomorphism_levels.clone()
    }

    pub fn get_depth_for_persona(&self, persona: &str) -> DepthSettings {
        if let Some(overrides) = self.cognitive_depth.persona_overrides.get(persona) {
            overrides.clone()
        } else {
            self.cognitive_depth.default.clone()
        }
    }

    pub fn get_profile_for_persona(&self, persona: &str) -> Option<ProfileValues> {
        self.anthropomorphism_levels.profiles.get(persona).cloned()
    }
}
