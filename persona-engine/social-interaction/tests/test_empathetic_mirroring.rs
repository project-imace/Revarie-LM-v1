#[cfg(test)]
mod tests {
    include!("../empathetic_mirroring.rs");
    use super::*;

    #[test]
    fn test_mirror_emotion_basic() {
        let mut em = EmpatheticMirroring::new();
        let mirrored = em.mirror_emotion(EmotionalTone::Joy, 0.9);
        assert_eq!(mirrored, EmotionalTone::Joy);
    }

    #[test]
    fn test_resonance_builds_over_time() {
        let mut em = EmpatheticMirroring::new();
        em.mirror_emotion(EmotionalTone::Sadness, 0.8);
        em.mirror_emotion(EmotionalTone::Sadness, 0.8);
        assert!(em.state.resonance > 0.5);
    }

    #[test]
    fn test_linguistic_style_analysis() {
        let em = EmpatheticMirroring::new();
        let text = "I would greatly appreciate your assistance with this matter. Thank you.";
        let style = em.analyze_style(text);
        assert!(style.formality > 0.2);
    }
}
