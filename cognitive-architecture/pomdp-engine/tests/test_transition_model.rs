//! test_transition_model.rs
//! Unit tests for Transition Matrix and Transition Model.

#[cfg(test)]
mod tests {
    use std::collections::HashMap;
    use rand::thread_rng;

    include!("../transition_model.rs");

    #[test]
    fn test_transition_matrix_creation() {
        let data = vec![
            vec![0.8, 0.2],
            vec![0.3, 0.7],
        ];
        let tm = TransitionMatrix::new(data).unwrap();
        assert_eq!(tm.n_states(), 2);
        assert!((tm.probability(0, 0) - 0.8).abs() < 1e-9);
        assert!((tm.probability(0, 1) - 0.2).abs() < 1e-9);
        assert!((tm.probability(1, 0) - 0.3).abs() < 1e-9);
        assert!((tm.probability(1, 1) - 0.7).abs() < 1e-9);
    }

    #[test]
    fn test_transition_matrix_normalization() {
        let data = vec![
            vec![4.0, 1.0],
            vec![1.0, 1.0],
        ];
        let tm = TransitionMatrix::new(data).unwrap();
        assert!((tm.probability(0, 0) - 0.8).abs() < 1e-9);
        assert!((tm.probability(0, 1) - 0.2).abs() < 1e-9);
        assert!((tm.probability(1, 0) - 0.5).abs() < 1e-9);
        assert!((tm.probability(1, 1) - 0.5).abs() < 1e-9);
    }

    #[test]
    fn test_identity_matrix() {
        let tm = TransitionMatrix::identity(3);
        assert_eq!(tm.probability(0, 0), 1.0);
        assert_eq!(tm.probability(0, 1), 0.0);
        assert_eq!(tm.probability(1, 1), 1.0);
        assert_eq!(tm.probability(2, 2), 1.0);
    }

    #[test]
    fn test_uniform_matrix() {
        let tm = TransitionMatrix::uniform(4);
        for i in 0..4 {
            for j in 0..4 {
                assert!((tm.probability(i, j) - 0.25).abs() < 1e-9);
            }
        }
    }

    #[test]
    fn test_sampling() {
        let mut rng = thread_rng();
        let tm = TransitionMatrix::new(vec![
            vec![1.0, 0.0],
            vec![0.0, 1.0],
        ]).unwrap();
        assert_eq!(tm.sample(&mut rng, 0), 0);
        assert_eq!(tm.sample(&mut rng, 1), 1);
    }

    #[test]
    fn test_stationary_distribution() {
        let tm = TransitionMatrix::new(vec![
            vec![0.5, 0.5],
            vec![0.5, 0.5],
        ]).unwrap();
        let dist = tm.stationary_distribution(100, 1e-6);
        assert!((dist[0] - 0.5).abs() < 1e-6);
        assert!((dist[1] - 0.5).abs() < 1e-6);
    }

    #[test]
    fn test_transition_model_creation() {
        let mut matrices = HashMap::new();
        matrices.insert("move".to_string(), TransitionMatrix::new(vec![
            vec![0.9, 0.1],
            vec![0.2, 0.8],
        ]).unwrap());
        matrices.insert("stay".to_string(), TransitionMatrix::identity(2));
        let model = TransitionModel::new(matrices).unwrap();
        assert_eq!(model.n_states(), 2);
        assert_eq!(model.actions().len(), 2);
    }

    #[test]
    fn test_transition_model_probability() {
        let mut matrices = HashMap::new();
        matrices.insert("move".to_string(), TransitionMatrix::new(vec![
            vec![0.9, 0.1],
            vec![0.2, 0.8],
        ]).unwrap());
        let model = TransitionModel::new(matrices).unwrap();
        assert!(model.probability("move", 0, 0).unwrap() > 0.8);
        assert!(model.probability("move", 0, 1).unwrap() < 0.2);
    }

    #[test]
    fn test_transition_model_sampling() {
        let mut rng = thread_rng();
        let mut matrices = HashMap::new();
        matrices.insert("stay".to_string(), TransitionMatrix::identity(2));
        let model = TransitionModel::new(matrices).unwrap();
        assert_eq!(model.sample(&mut rng, "stay", 0).unwrap(), 0);
        assert_eq!(model.sample(&mut rng, "stay", 1).unwrap(), 1);
    }

    #[test]
    fn test_invalid_matrix_squareness() {
        let data = vec![
            vec![0.8, 0.2],
            vec![0.3],
        ];
        assert!(TransitionMatrix::new(data).is_err());
    }

    #[test]
    fn test_validity_check() {
        let tm = TransitionMatrix::new(vec![
            vec![0.8, 0.2],
            vec![0.3, 0.7],
        ]).unwrap();
        assert!(tm.is_valid(1e-9));
    }

    #[test]
    fn test_insert_action() {
        let mut matrices = HashMap::new();
        matrices.insert("a".to_string(), TransitionMatrix::identity(2));
        let mut model = TransitionModel::new(matrices).unwrap();
        let new_matrix = TransitionMatrix::uniform(2);
        assert!(model.insert("b".to_string(), new_matrix).is_ok());
        assert_eq!(model.actions().len(), 2);
    }
}
