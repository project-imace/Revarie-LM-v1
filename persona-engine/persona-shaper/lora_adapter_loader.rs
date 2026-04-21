//! lora_adapter_loader.rs – Persona Shaper: LoRA Adapter Loader
//!
//! Dynamically loads and applies Low-Rank Adaptation (LoRA) adapters to
//! modulate the base language model's behavior. Enables runtime switching
//! between Samara (high anthropomorphism) and Artery (low anthropomorphism).
//!
//! Theoretical Foundations:
//! - Hu et al. (2021): "LoRA: Low-Rank Adaptation of Large Language Models"
//! - Dettmers et al. (2023): "QLoRA: Efficient Finetuning of Quantized LLMs"
//! - Valipour et al. (2022): "DyLoRA: Parameter Efficient Tuning with Dynamic Search"
//!
//! Architecture:
//! - Base model weights W ∈ R^{d×k} remain frozen
//! - LoRA adapter: W' = W + B·A where B ∈ R^{d×r}, A ∈ R^{r×k}, r ≪ min(d,k)
//! - Samara adapter: r=16, α=32, trained on empathetic dialogues
//! - Artery adapter: r=8, α=16, trained on functional/neutral dialogues

use std::collections::HashMap;
use std::fs::File;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum LoRAError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON parsing error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("Invalid adapter configuration: {0}")]
    InvalidConfig(String),
    #[error("Adapter not found: {0}")]
    NotFound(String),
    #[error("Dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoRAConfig {
    /// Adapter name (e.g., "samara", "artery")
    pub name: String,
    /// Rank of the low-rank decomposition
    pub rank: usize,
    /// Scaling factor α (applied as α/r)
    pub alpha: f64,
    /// Base model dimension
    pub model_dim: usize,
    /// Target modules to apply LoRA to (e.g., ["q_proj", "v_proj"])
    pub target_modules: Vec<String>,
    /// Dropout rate for LoRA layers
    pub dropout: f64,
    /// Persona-specific metadata
    pub persona_metadata: PersonaMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonaMetadata {
    pub persona_id: String,
    pub anthropomorphism_level: f64,
    pub training_dataset: String,
    pub training_steps: usize,
    pub version: String,
    pub created_at: String,
}

#[derive(Debug, Clone)]
pub struct LoRAAdapter {
    pub config: LoRAConfig,
    /// Low-rank matrices: B ∈ R^{d×r}
    pub lora_b: HashMap<String, Vec<Vec<f32>>>,
    /// Low-rank matrices: A ∈ R^{r×k}
    pub lora_a: HashMap<String, Vec<Vec<f32>>>,
    /// Scaling factor = α/r
    pub scaling: f64,
}

impl LoRAAdapter {
    /// Load a LoRA adapter from a directory containing config and weights.
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self, LoRAError> {
        let base_path = path.as_ref();
        
        // Load configuration
        let config_path = base_path.join("adapter_config.json");
        let config_content = std::fs::read_to_string(&config_path)?;
        let config: LoRAConfig = serde_json::from_str(&config_content)?;
        
        // Validate config
        if config.rank == 0 {
            return Err(LoRAError::InvalidConfig("Rank must be > 0".to_string()));
        }
        
        let scaling = config.alpha / config.rank as f64;
        
        // Load weight files (in production, these would be safetensors format)
        let lora_b = Self::load_weights(base_path, "lora_b")?;
        let lora_a = Self::load_weights(base_path, "lora_a")?;
        
        Ok(Self {
            config,
            lora_b,
            lora_a,
            scaling,
        })
    }

    fn load_weights(
        base_path: &Path,
        prefix: &str,
    ) -> Result<HashMap<String, Vec<Vec<f32>>>, LoRAError> {
        let weights_path = base_path.join(format!("{}.json", prefix));
        if !weights_path.exists() {
            return Ok(HashMap::new());
        }
        
        let content = std::fs::read_to_string(&weights_path)?;
        let weights: HashMap<String, Vec<Vec<f32>>> = serde_json::from_str(&content)?;
        Ok(weights)
    }

    /// Apply LoRA adaptation to base hidden states.
    /// Δh = (α/r) · (h @ A^T) @ B^T
    pub fn apply(&self, module_name: &str, hidden_states: &[Vec<f32>]) -> Option<Vec<Vec<f32>>> {
        let a = self.lora_a.get(module_name)?;
        let b = self.lora_b.get(module_name)?;
        
        let batch_size = hidden_states.len();
        let seq_len = hidden_states[0].len();
        let rank = self.config.rank;
        
        // h @ A^T: (batch × seq_len × dim) @ (dim × rank) -> (batch × seq_len × rank)
        let mut lora_intermediate = vec![vec![0.0; rank]; batch_size];
        for b_idx in 0..batch_size {
            for r in 0..rank {
                let mut sum = 0.0;
                for d in 0..hidden_states[b_idx].len() {
                    sum += hidden_states[b_idx][d] * a[r][d];
                }
                lora_intermediate[b_idx][r] = sum;
            }
        }
        
        // intermediate @ B^T: (batch × seq_len × rank) @ (rank × dim) -> (batch × seq_len × dim)
        let mut lora_output = vec![vec![0.0; seq_len]; batch_size];
        for b_idx in 0..batch_size {
            for d in 0..seq_len {
                let mut sum = 0.0;
                for r in 0..rank {
                    sum += lora_intermediate[b_idx][r] * b[d][r];
                }
                lora_output[b_idx][d] = sum * self.scaling as f32;
            }
        }
        
        Some(lora_output)
    }

    /// Get the adapter's persona metadata.
    pub fn persona_metadata(&self) -> &PersonaMetadata {
        &self.config.persona_metadata
    }

    /// Check if this adapter targets a specific module.
    pub fn targets_module(&self, module_name: &str) -> bool {
        self.config.target_modules.iter().any(|m| m == module_name)
    }
}

/// Manages multiple LoRA adapters and provides runtime switching.
pub struct LoRAAdapterManager {
    adapters: HashMap<String, LoRAAdapter>,
    active_adapter: Option<String>,
    base_path: PathBuf,
}

impl LoRAAdapterManager {
    pub fn new<P: AsRef<Path>>(base_path: P) -> Self {
        Self {
            adapters: HashMap::new(),
            active_adapter: None,
            base_path: base_path.as_ref().to_path_buf(),
        }
    }

    /// Load all available adapters from the base directory.
    pub fn load_all(&mut self) -> Result<(), LoRAError> {
        if !self.base_path.exists() {
            return Ok(());
        }

        for entry in std::fs::read_dir(&self.base_path)? {
            let entry = entry?;
            if entry.file_type()?.is_dir() {
                let adapter_name = entry.file_name().to_string_lossy().to_string();
                if adapter_name.ends_with("_lora") {
                    let adapter = LoRAAdapter::load(entry.path())?;
                    let name = adapter.config.name.clone();
                    self.adapters.insert(name, adapter);
                }
            }
        }
        Ok(())
    }

    /// Load a specific adapter by name.
    pub fn load_adapter(&mut self, name: &str) -> Result<(), LoRAError> {
        let adapter_path = self.base_path.join(format!("{}_lora", name));
        if !adapter_path.exists() {
            return Err(LoRAError::NotFound(name.to_string()));
        }
        let adapter = LoRAAdapter::load(adapter_path)?;
        self.adapters.insert(adapter.config.name.clone(), adapter);
        Ok(())
    }

    /// Activate an adapter by name.
    pub fn activate(&mut self, name: &str) -> Result<(), LoRAError> {
        if !self.adapters.contains_key(name) {
            self.load_adapter(name)?;
        }
        self.active_adapter = Some(name.to_string());
        Ok(())
    }

    /// Deactivate the current adapter (return to base model).
    pub fn deactivate(&mut self) {
        self.active_adapter = None;
    }

    /// Get the currently active adapter.
    pub fn active(&self) -> Option<&LoRAAdapter> {
        self.active_adapter
            .as_ref()
            .and_then(|name| self.adapters.get(name))
    }

    /// Apply the active adapter to hidden states.
    pub fn apply_active(
        &self,
        module_name: &str,
        hidden_states: &[Vec<f32>],
    ) -> Option<Vec<Vec<f32>>> {
        self.active()?.apply(module_name, hidden_states)
    }

    /// Get adapter by name.
    pub fn get(&self, name: &str) -> Option<&LoRAAdapter> {
        self.adapters.get(name)
    }

    /// List all loaded adapters.
    pub fn list_adapters(&self) -> Vec<&LoRAAdapter> {
        self.adapters.values().collect()
    }

    /// Get the active adapter's persona metadata.
    pub fn active_persona(&self) -> Option<&PersonaMetadata> {
        self.active().map(|a| &a.config.persona_metadata)
    }

    /// Save a newly trained adapter to disk.
    pub fn save_adapter<P: AsRef<Path>>(
        &self,
        adapter: &LoRAAdapter,
        path: P,
    ) -> Result<(), LoRAError> {
        let base = path.as_ref();
        std::fs::create_dir_all(base)?;
        
        // Save config
        let config_path = base.join("adapter_config.json");
        let config_json = serde_json::to_string_pretty(&adapter.config)?;
        std::fs::write(config_path, config_json)?;
        
        // Save weights
        if !adapter.lora_b.is_empty() {
            let b_path = base.join("lora_b.json");
            let b_json = serde_json::to_string(&adapter.lora_b)?;
            std::fs::write(b_path, b_json)?;
        }
        if !adapter.lora_a.is_empty() {
            let a_path = base.join("lora_a.json");
            let a_json = serde_json::to_string(&adapter.lora_a)?;
            std::fs::write(a_path, a_json)?;
        }
        
        Ok(())
    }
}

// =============================================================================
// Tests
// =============================================================================
