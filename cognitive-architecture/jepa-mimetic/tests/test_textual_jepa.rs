//! test_textual_jepa.rs
//! Unit tests for Textual JEPA module.

#[cfg(test)]
mod tests {
    include!("../textual_jepa.rs");

    #[test]
    fn test_text_encoder_normalized_output() {
        let encoder = TextEncoder::new(100, 16, 10);
        let obs = TextObservation::from_tokens(vec![1, 2, 3]);
        let latent = encoder.encode(&obs);
        assert_eq!(latent.len(), 16);
        let norm: f32 = latent.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!((norm - 1.0).abs() < 1e-3, "Latent vector should be normalized");
    }

    #[test]
    fn test_text_encoder_empty_observation() {
        let encoder = TextEncoder::new(100, 16, 10);
        let obs = TextObservation::from_tokens(vec![]);
        let latent = encoder.encode(&obs);
        assert_eq!(latent.len(), 16);
        // Should not panic and produce a valid normalized vector
        let norm: f32 = latent.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!((norm - 1.0).abs() < 1e-3);
    }

    #[test]
    fn test_predictor_gradient_update() {
        let mut pred = TextLatentPredictor::new(4, 2);
        let z = vec![0.5, 0.3, -0.2, 0.8];
        let target = vec![0.1, 0.4, 0.0, 0.9];
        
        let (loss_initial, b_grad, w_grad) = pred.calculate_gradients(&z, 0, &target);
        pred.apply_gradients(&b_grad, &w_grad, 0.01);
        
        let (loss_final, _, _) = pred.calculate_gradients(&z, 0, &target);
        assert!(loss_final < loss_initial, 
                "Loss should decrease after gradient update. Initial: {}, Final: {}", loss_initial, loss_final);
    }

    #[test]
    fn test_predictor_batch_training() {
        let mut agent = TextualJEPAAgent::new(50, 8, 2, 5, 100, 4, 0.01);
        // Populate memory with simple patterns
        for _ in 0..10 {
            let obs = TextObservation::from_tokens(vec![1, 2, 3]);
            let next_obs = TextObservation::from_tokens(vec![2, 3, 4]);
            agent.store_transition(obs, 0, next_obs);
        }
        let loss_before = agent.learn().unwrap();
        let loss_after = agent.learn().unwrap();
        // Loss should generally decrease over time (though due to random init, not guaranteed to be monotonic)
        // We just assert that learning doesn't produce NaN or crash.
        assert!(!loss_before.is_nan());
        assert!(!loss_after.is_nan());
    }

    #[test]
    fn test_agent_predict_next_consistency() {
        let agent = TextualJEPAAgent::new(50, 8, 2, 5, 100, 4, 0.01);
        let z = vec![0.1; 8];
        let next1 = agent.predict_next(&z, 0);
        let next2 = agent.predict_next(&z, 0);
        assert_eq!(next1.len(), 8);
        assert_eq!(next2.len(), 8);
        // Predictions should be deterministic given the same input
        assert_eq!(next1, next2);
    }

    #[test]
    fn test_memory_overflow() {
        let mut agent = TextualJEPAAgent::new(50, 8, 2, 5, 10, 4, 0.01);
        for i in 0..15 {
            let obs = TextObservation::from_tokens(vec![i % 10]);
            let next_obs = TextObservation::from_tokens(vec![(i + 1) % 10]);
            agent.store_transition(obs, 0, next_obs);
        }
        assert_eq!(agent.memory_len(), 10);
    }

    #[test]
    fn test_target_encoder_update() {
        let mut agent = TextualJEPAAgent::new(50, 8, 2, 5, 10, 4, 0.01);
        // Initially target equals encoder
        let initial_embedding = agent.target_encoder.embeddings[0][0];
        // Manually change encoder
        agent.encoder.embeddings[0][0] = 0.5;
        agent.update_target_encoder();
        // With tau=0.005, target should move slightly towards 0.5
        let updated_embedding = agent.target_encoder.embeddings[0][0];
        assert!((updated_embedding - initial_embedding).abs() > 0.0);
    }

    #[test]
    fn test_encode_timestamp() {
        let agent = TextualJEPAAgent::new(50, 8, 2, 5, 10, 4, 0.01);
        let obs = TextObservation::from_tokens(vec![1, 2]);
        let state = agent.encode(&obs);
        assert!(state.timestamp > 0);
    }

    #[test]
    fn test_raw_text_storage() {
        let obs = TextObservation::from_tokens(vec![1, 2])
            .with_raw("Hello world".to_string());
        assert_eq!(obs.raw, Some("Hello world".to_string()));
    }
}
