#[cfg(test)]
mod tests {
    include!("../parameter_loader.rs");
    use super::*;
    use tempfile::TempDir;

    fn setup_test_config(temp: &TempDir) -> std::path::PathBuf {
        let root = temp.path().to_path_buf();
        std::fs::write(root.join("persona_vector_samara.json"), r#"{"persona_id":"samara_v1.0","name":"Samara","description":"test","version":"1.0.0","anthropomorphism":{"warmth":0.9,"empathy":0.85,"curiosity":0.8,"formality":0.2,"playfulness":0.6,"directness":0.4,"emotional_expressiveness":0.85},"cognitive_style":{"system1_weight":0.55,"system2_weight":0.45,"reasoning_depth":0.7,"ambiguity_tolerance":0.75,"certainty_threshold":0.6},"social_orientation":{"use_participant_name":true,"first_person_pronouns":true,"relational_continuity":0.9,"emotional_mirroring":0.85,"rapport_building":0.9,"self_disclosure":0.7},"memory_consolidation":{"summary_style":"warm_personal","include_emotional_tags":true,"include_name_in_summary":true,"recency_boost":0.25,"emotional_salience_boost":0.3},"affective_modulation":{"dopamine_baseline":0.7,"serotonin_baseline":0.65,"norepinephrine_baseline":0.5,"acetylcholine_baseline":0.55,"emotional_contagion_rate":0.2,"mood_recovery_rate":0.15},"rebound_mechanism":{"elasticity_constant_k":0.1,"max_deviation_tolerance":0.3,"rebound_damping":0.8}}"#).unwrap();
        std::fs::write(root.join("persona_vector_artery.json"), r#"{"persona_id":"artery_v1.0","name":"Artery 1.0","description":"test","version":"1.0.0","anthropomorphism":{"warmth":0.15,"empathy":0.1,"curiosity":0.3,"formality":0.9,"playfulness":0.05,"directness":0.95,"emotional_expressiveness":0.1},"cognitive_style":{"system1_weight":0.35,"system2_weight":0.65,"reasoning_depth":0.85,"ambiguity_tolerance":0.25,"certainty_threshold":0.85},"social_orientation":{"use_participant_name":false,"first_person_pronouns":false,"relational_continuity":0.1,"emotional_mirroring":0.05,"rapport_building":0.1,"self_disclosure":0.05},"memory_consolidation":{"summary_style":"neutral_factual","include_emotional_tags":false,"include_name_in_summary":false,"recency_boost":0.05,"emotional_salience_boost":0.0},"affective_modulation":{"dopamine_baseline":0.3,"serotonin_baseline":0.35,"norepinephrine_baseline":0.3,"acetylcholine_baseline":0.7,"emotional_contagion_rate":0.02,"mood_recovery_rate":0.5},"rebound_mechanism":{"elasticity_constant_k":10.0,"max_deviation_tolerance":0.05,"rebound_damping":0.95}}"#).unwrap();
        std::fs::write(root.join("cognitive_depth.yaml"), r#"version: "1.0.0"
default:
  max_reasoning_steps: 5
  inference_depth: 3
  counterfactual_branches: 2
  verification_passes: 1
persona_overrides:
  samara:
    max_reasoning_steps: 4
    inference_depth: 2
    counterfactual_branches: 2
    verification_passes: 1
  artery:
    max_reasoning_steps: 7
    inference_depth: 4
    counterfactual_branches: 3
    verification_passes: 2
task_specific: {}
runtime_modulation:
  fatigue_factor: 0.1
  time_pressure_factor: 0.2
  cognitive_load_threshold: 0.7"#).unwrap();
        std::fs::write(root.join("anthropomorphism_level.toml"), r#"version = "1.0.0"
[dimensions.warmth]
min = 0.0
max = 1.0
description = "Perceived kindness"
[profiles.samara]
warmth = 0.9
empathy = 0.85
agency = 0.8
experience = 0.75
[profiles.artery]
warmth = 0.15
empathy = 0.1
agency = 0.9
experience = 0.1
[linguistic_markers]
high_anthropomorphism = ["I feel"]
low_anthropomorphism = ["Data indicates"]
[behavioral_cues.high_anthropomorphism]
use_name = true
first_person = true
ask_followup = true
express_curiosity = true"#).unwrap();
        root
    }

    #[test]
    fn test_load_samara_vector() {
        let temp = TempDir::new().unwrap();
        let root = setup_test_config(&temp);
        let loader = ParameterLoader::new(root).unwrap();
        let samara = loader.samara();
        assert_eq!(samara.name, "Samara");
        assert_eq!(samara.anthropomorphism.warmth, 0.9);
    }

    #[test]
    fn test_artery_elasticity_is_higher() {
        let temp = TempDir::new().unwrap();
        let root = setup_test_config(&temp);
        let loader = ParameterLoader::new(root).unwrap();
        let samara = loader.samara();
        let artery = loader.artery();
        assert!(artery.rebound_mechanism.elasticity_constant_k > samara.rebound_mechanism.elasticity_constant_k);
    }
}
