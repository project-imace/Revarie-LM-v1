//! textual_jepa.rs
//! JEPA-Mimetic – Textual Joint Embedding Predictive Architecture.
//! Implements a self-supervised predictive model for textual latent spaces.
//! Predicts future text embeddings from current context and actions,
//! enabling language-based world modeling.
//!
//! Theoretical foundations:
//! - LeCun (2022): JEPA for autonomous intelligence.
//! - Devlin et al. (2019): BERT masked language modeling.
//! - Radford et al. (2019): Language models as unsupervised multitask learners.
//! - Johnson-Lindenstrauss lemma: Random projections preserve distance.

use std::collections::{VecDeque, HashMap};
use rand::Rng;
use rand::seq::SliceRandom;
use serde::{Serialize, Deserialize};

/// A textual observation represented as a bag-of-words or embedding vector.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextObservation {
    /// Token indices or embedding vector.
    pub tokens: Vec<usize>,
    /// Optional raw text for debugging.
    #[serde(skip)]
    pub raw: Option<String>,
}

impl TextObservation {
    pub fn from_tokens(tokens: Vec<usize>) -> Self {
        Self { tokens, raw: None }
    }

    pub fn with_raw(mut self, text: String) -> Self {
        self.raw = Some(text);
        self
    }
}

/// A latent state vector in the textual JEPA model.
#[derive(Debug, Clone)]
pub struct TextLatentState {
    pub vector: Vec<f32>,
    pub timestamp: u64,
    pub surprisal: f32,
}

/// Simple linear encoder for text observations.
#[derive(Debug, Clone)]
pub struct TextEncoder {
    /// Embedding matrix: vocab_size x latent_dim
    embeddings: Vec<Vec<f32>>,
    /// Projection matrix: (embedding_dim * max_seq_len) x latent_dim
    projection: Vec<Vec<f32>>,
    latent_dim: usize,
    vocab_size: usize,
    max_seq_len: usize,
}

impl TextEncoder {
    pub fn new(vocab_size: usize, latent_dim: usize, max_seq_len: usize) -> Self {
        let mut rng = rand::thread_rng();
        let embeddings: Vec<Vec<f32>> = (0..vocab_size)
            .map(|_| (0..latent_dim).map(|_| rng.gen_range(-0.1..0.1)).collect())
            .collect();
        let projection: Vec<Vec<f32>> = (0..(latent_dim * max_seq_len))
            .map(|_| (0..latent_dim).map(|_| rng.gen_range(-0.1..0.1)).collect())
            .collect();
        Self {
            embeddings,
            projection,
            latent_dim,
            vocab_size,
            max_seq_len,
        }
    }

    /// Encode a text observation into a latent vector.
    pub fn encode(&self, obs: &TextObservation) -> Vec<f32> {
        let mut combined = vec![0.0; self.latent_dim * self.max_seq_len];
        for (pos, &token) in obs.tokens.iter().take(self.max_seq_len).enumerate() {
            if token < self.vocab_size {
                let emb = &self.embeddings[token];
                let offset = pos * self.latent_dim;
                for (i, &val) in emb.iter().enumerate() {
                    combined[offset + i] = val;
                }
            }
        }
        // Project to latent space
        let mut latent = vec![0.0; self.latent_dim];
        for i in 0..self.latent_dim {
            for j in 0..combined.len() {
                latent[i] += combined[j] * self.projection[j][i];
            }
        }
        // LayerNorm approximation
        let norm: f32 = latent.iter().map(|x| x * x).sum::<f32>().sqrt() + 1e-5;
        latent.iter_mut().for_each(|x| *x /= norm);
        latent
    }
}

/// Predicts next latent state from current latent and action.
#[derive(Debug, Clone)]
pub struct TextLatentPredictor {
    weights: Vec<Vec<f32>>,  // (latent_dim + action_dim) x latent_dim
    bias: Vec<f32>,
    latent_dim: usize,
    action_dim: usize,
}

impl TextLatentPredictor {
    pub fn new(latent_dim: usize, action_dim: usize) -> Self {
        let mut rng = rand::thread_rng();
        let weights: Vec<Vec<f32>> = (0..latent_dim + action_dim)
            .map(|_| (0..latent_dim).map(|_| rng.gen_range(-0.1..0.1)).collect())
            .collect();
        let bias: Vec<f32> = (0..latent_dim).map(|_| rng.gen_range(-0.1..0.1)).collect();
        Self {
            weights,
            bias,
            latent_dim,
            action_dim,
        }
    }

    /// Predict next latent from current latent and one-hot action.
    pub fn predict(&self, z: &[f32], action: usize) -> Vec<f32> {
        let mut input = z.to_vec();
        let mut action_onehot = vec![0.0; self.action_dim];
        if action < self.action_dim {
            action_onehot[action] = 1.0;
        }
        input.extend(action_onehot);
        let mut output = self.bias.clone();
        for i in 0..self.latent_dim {
            for j in 0..input.len() {
                output[i] += input[j] * self.weights[j][i];
            }
        }
        output
    }

    /// FIXED: Calculate gradient for a single pass without immediately updating weights
    pub fn calculate_gradients(&self, z: &[f32], action: usize, target: &[f32]) -> (f32, Vec<f32>, Vec<Vec<f32>>) {
        let pred = self.predict(z, action);
        let mut loss = 0.0;
        let mut bias_grad = vec![0.0; self.latent_dim];
        let mut weight_grad = vec![vec![0.0; self.latent_dim]; self.weights.len()];
        
        let mut input = z.to_vec();
        let mut action_onehot = vec![0.0; self.action_dim];
        if action < self.action_dim {
            action_onehot[action] = 1.0;
        }
        input.extend(action_onehot);

        for i in 0..self.latent_dim {
            let diff = pred[i] - target[i];
            loss += diff * diff;
            bias_grad[i] = 2.0 * diff;
            
            for j in 0..input.len() {
                weight_grad[j][i] = 2.0 * diff * input[j];
            }
        }
        (loss, bias_grad, weight_grad)
    }
    
    /// FIXED: Apply accumulated batch gradients
    pub fn apply_gradients(&mut self, bias_grad: &[f32], weight_grad: &[Vec<f32>], lr: f32) {
        for i in 0..self.latent_dim {
            self.bias[i] -= lr * bias_grad[i];
            for j in 0..self.weights.len() {
                self.weights[j][i] -= lr * weight_grad[j][i];
            }
        }
    }
}

/// Textual JEPA agent with replay buffer and target encoder.
pub struct TextualJEPAAgent {
    encoder: TextEncoder,
    target_encoder: TextEncoder,
    predictor: TextLatentPredictor,
    memory: VecDeque<(TextObservation, usize, TextObservation)>,
    latent_dim: usize,
    action_dim: usize,
    batch_size: usize,
    memory_size: usize,
    learning_rate: f32,
    tau: f32,
    step_counter: usize,
}

impl TextualJEPAAgent {
    pub fn new(
        vocab_size: usize,
        latent_dim: usize,
        action_dim: usize,
        max_seq_len: usize,
        memory_size: usize,
        batch_size: usize,
        learning_rate: f32,
    ) -> Self {
        let encoder = TextEncoder::new(vocab_size, latent_dim, max_seq_len);
        let target_encoder = encoder.clone();
        let predictor = TextLatentPredictor::new(latent_dim, action_dim);
        Self {
            encoder,
            target_encoder,
            predictor,
            memory: VecDeque::with_capacity(memory_size),
            latent_dim,
            action_dim,
            batch_size,
            memory_size,
            learning_rate,
            tau: 0.005,
            step_counter: 0,
        }
    }

    /// Encode an observation into latent state.
    pub fn encode(&self, obs: &TextObservation) -> TextLatentState {
        let vector = self.encoder.encode(obs);
        TextLatentState {
            vector,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            surprisal: 0.0,
        }
    }

    /// Predict next latent state.
    pub fn predict_next(&self, z: &[f32], action: usize) -> Vec<f32> {
        self.predictor.predict(z, action)
    }

    /// Store a transition in the replay buffer.
    pub fn store_transition(
        &mut self,
        obs: TextObservation,
        action: usize,
        next_obs: TextObservation,
    ) {
        if self.memory.len() >= self.memory_size {
            self.memory.pop_front();
        }
        self.memory.push_back((obs, action, next_obs));
    }

    /// Soft update target encoder.
    fn update_target_encoder(&mut self) {
        // Simple EMA update for embeddings and projection
        for (t_emb, emb) in self.target_encoder.embeddings
            .iter_mut()
            .zip(&self.encoder.embeddings)
        {
            for (t, e) in t_emb.iter_mut().zip(emb) {
                *t = self.tau * e + (1.0 - self.tau) * *t;
            }
        }
        for (t_proj, proj) in self.target_encoder.projection
            .iter_mut()
            .zip(&self.encoder.projection)
        {
            for (t, p) in t_proj.iter_mut().zip(proj) {
                *t = self.tau * p + (1.0 - self.tau) * *t;
            }
        }
    }

    /// Sample a batch from memory.
    fn sample_batch(&self) -> Vec<(TextObservation, usize, TextObservation)> {
        let mut rng = rand::thread_rng();
        let mut indices: Vec<usize> = (0..self.memory.len()).collect();
        indices.shuffle(&mut rng);
        indices.truncate(self.batch_size);
        indices
            .into_iter()
            .map(|i| self.memory[i].clone())
            .collect()
    }

    /// FIXED: Compute loss on a batch using gradient accumulation
    fn compute_loss(&mut self, batch: &[(TextObservation, usize, TextObservation)]) -> f32 {
        let mut total_loss = 0.0;
        let mut accum_bias_grad = vec![0.0; self.latent_dim];
        let mut accum_weight_grad = vec![vec![0.0; self.latent_dim]; self.predictor.weights.len()];
        
        for (obs, action, next_obs) in batch {
            let z = self.encoder.encode(obs);
            let z_next_target = self.target_encoder.encode(next_obs);
            
            let (loss, b_grad, w_grad) = self.predictor.calculate_gradients(&z, *action, &z_next_target);
            total_loss += loss;
            
            for i in 0..self.latent_dim {
                accum_bias_grad[i] += b_grad[i] / batch.len() as f32;
                for j in 0..self.predictor.weights.len() {
                    accum_weight_grad[j][i] += w_grad[j][i] / batch.len() as f32;
                }
            }
        }
        
        self.predictor.apply_gradients(&accum_bias_grad, &accum_weight_grad, self.learning_rate);
        total_loss / batch.len() as f32
    }

    /// Perform one learning step.
    pub fn learn(&mut self) -> Option<f32> {
        if self.memory.len() < self.batch_size {
            return None;
        }
        let batch = self.sample_batch();
        let loss = self.compute_loss(&batch);
        self.update_target_encoder();
        self.step_counter += 1;
        Some(loss)
    }

    /// Get memory size.
    pub fn memory_len(&self) -> usize {
        self.memory.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_text_encoder() {
        let encoder = TextEncoder::new(100, 16, 10);
        let obs = TextObservation::from_tokens(vec![1, 2, 3]);
        let latent = encoder.encode(&obs);
        assert_eq!(latent.len(), 16);
        let norm: f32 = latent.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!((norm - 1.0).abs() < 1e-3);
    }

    #[test]
    fn test_predictor_update() {
        let mut pred = TextLatentPredictor::new(4, 2);
        let z = vec![0.5, 0.3, -0.2, 0.8];
        let target = vec![0.1, 0.4, 0.0, 0.9];
        
        let (loss_initial, b_grad, w_grad) = pred.calculate_gradients(&z, 0, &target);
        pred.apply_gradients(&b_grad, &w_grad, 0.01);
        
        let (loss_final, _, _) = pred.calculate_gradients(&z, 0, &target);
        assert!(loss_final < loss_initial);
    }

    #[test]
    fn test_agent_store_and_learn() {
        let mut agent = TextualJEPAAgent::new(50, 8, 2, 5, 100, 4, 0.01);
        for _ in 0..10 {
            let obs = TextObservation::from_tokens(vec![1, 2]);
            let next_obs = TextObservation::from_tokens(vec![2, 3]);
            agent.store_transition(obs, 0, next_obs);
        }
        let loss = agent.learn();
        assert!(loss.is_some());
    }

    #[test]
    fn test_predict_next() {
        let agent = TextualJEPAAgent::new(50, 8, 2, 5, 100, 4, 0.01);
        let z = vec![0.1; 8];
        let next = agent.predict_next(&z, 0);
        assert_eq!(next.len(), 8);
    }
}
