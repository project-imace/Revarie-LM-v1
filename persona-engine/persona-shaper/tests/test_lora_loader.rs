#[cfg(test)]
mod tests {
    include!("../lora_adapter_loader.rs");
    use super::*;
    use tempfile::TempDir;

    fn create_test_adapter(dir: &TempDir, name: &str) -> LoRAAdapter {
        let config = LoRAConfig {
            name: name.to_string(),
            rank: 8,
            alpha: 16.0,
            model_dim: 768,
            target_modules: vec!["q_proj".to_string()],
            dropout: 0.1,
            persona_metadata: PersonaMetadata {
                persona_id: name.to_string(),
                anthropomorphism_level: 0.5,
                training_dataset: "test".to_string(),
                training_steps: 100,
                version: "1.0.0".to_string(),
                created_at: "2026-01-01".to_string(),
            },
        };
        let lora_b = HashMap::new();
        let lora_a = HashMap::new();
        LoRAAdapter { config, lora_b, lora_a, scaling: 2.0 }
    }

    #[test]
    fn test_manager_activate_deactivate() {
        let temp = TempDir::new().unwrap();
        let adapter = create_test_adapter(&temp, "test");
        let mut manager = LoRAAdapterManager::new(temp.path());
        manager.adapters.insert("test".to_string(), adapter);
        
        manager.activate("test").unwrap();
        assert!(manager.active().is_some());
        
        manager.deactivate();
        assert!(manager.active().is_none());
    }

    #[test]
    fn test_list_adapters() {
        let temp = TempDir::new().unwrap();
        let adapter1 = create_test_adapter(&temp, "samara");
        let adapter2 = create_test_adapter(&temp, "artery");
        let mut manager = LoRAAdapterManager::new(temp.path());
        manager.adapters.insert("samara".to_string(), adapter1);
        manager.adapters.insert("artery".to_string(), adapter2);
        
        let list = manager.list_adapters();
        assert_eq!(list.len(), 2);
    }

    #[test]
    fn test_targets_module() {
        let temp = TempDir::new().unwrap();
        let adapter = create_test_adapter(&temp, "test");
        assert!(adapter.targets_module("q_proj"));
        assert!(!adapter.targets_module("k_proj"));
    }
}
