#[cfg(test)]
mod tests {
    include!("../vams_integrator.rs");
    use super::*;
    use std::collections::HashMap;

    fn create_test_vams() -> VAMSData {
        let mut current = HashMap::new();
        current.insert(VAMSDimension::Happy, 65);
        current.insert(VAMSDimension::Sad, 30);
        current.insert(VAMSDimension::Calm, 70);
        current.insert(VAMSDimension::Tense, 25);
        current.insert(VAMSDimension::Energetic, 60);
        current.insert(VAMSDimension::Sleepy, 20);

        VAMSData {
            current,
            previous: None,
            pre_session: None,
            post_session: None,
            session_date: Some("2026-04-21".to_string()),
            day_number: 3,
        }
    }

    #[test]
    fn test_valence_positive() {
        let integrator = VAMSIntegrator::new("samara");
        let data = create_test_vams();
        let profile = integrator.compute_profile(&data);
        assert!(profile.valence > 0.0);
    }

    #[test]
    fn test_samara_modulation_for_negative_mood() {
        let mut integrator = VAMSIntegrator::new("samara");
        let mut data = create_test_vams();
        data.current.insert(VAMSDimension::Sad, 85);
        integrator.update(data);

        let modulation = integrator.get_response_modulation();
        assert!(modulation.supportive_language);
        assert!(modulation.acknowledge_emotion);
    }

    #[test]
    fn test_artery_minimal_modulation() {
        let mut integrator = VAMSIntegrator::new("artery");
        let data = create_test_vams();
        integrator.update(data);

        let modulation = integrator.get_response_modulation();
        assert!(!modulation.supportive_language);
        assert!(!modulation.celebratory_tone);
    }

    #[test]
    fn test_mood_description_format() {
        let mut integrator = VAMSIntegrator::new("samara");
        let data = create_test_vams();
        integrator.update(data);

        let desc = integrator.mood_description();
        assert!(!desc.is_empty());
    }
}
