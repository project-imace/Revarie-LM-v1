//! test_skill_compiler.rs
//! Unit tests for Skill Compiler.

#[cfg(test)]
mod tests {
    use std::thread::sleep;
    use std::time::Duration;
    include!("../skill_compiler.rs");

    #[test]
    fn test_production_creation() {
        let prod = ProductionRule::new("test", "greeting", "hello");
        assert_eq!(prod.condition, "greeting");
        assert_eq!(prod.action, "hello");
        assert_eq!(prod.strength, 0.1);
    }

    #[test]
    fn test_strength_increases_with_use() {
        let mut prod = ProductionRule::new("test", "a", "b");
        let initial = prod.strength;
        prod.update_strength();
        prod.update_strength();
        assert!(prod.strength > initial);
        assert_eq!(prod.usage_count, 2);
    }

    #[test]
    fn test_compilation_after_practice() {
        let mut prod = ProductionRule::new("test", "a", "b");
        for _ in 0..5 {
            prod.update_strength();
        }
        assert!(prod.compiled);
    }

    #[test]
    fn test_execute_finds_best_match() {
        let mut compiler = SkillCompiler::new();
        compiler.get_or_create("greet", "Hello!");
        compiler.get_or_create("greet formal", "Good day.");
        
        for _ in 0..3 {
            compiler.execute("greet formal");
        }
        
        let result = compiler.execute("greet formal");
        assert_eq!(result, Some("Good day.".to_string()));
    }

    #[test]
    fn test_compile_sequence() {
        let mut compiler = SkillCompiler::new();
        compiler.compile_sequence("morning_routine", &["stretch".to_string(), "drink_water".to_string()]);
        let compiled = compiler.compiled_skills();
        assert_eq!(compiled.len(), 1);
        assert!(compiled[0].action.contains("stretch"));
    }

    #[test]
    fn test_capacity_eviction() {
        let mut compiler = SkillCompiler::new();
        compiler.max_productions = 3;
        for i in 0..5 {
            compiler.get_or_create(&format!("cond_{}", i), &format!("act_{}", i));
        }
        assert_eq!(compiler.len(), 3);
    }

    #[test]
    fn test_decay_all() {
        let mut compiler = SkillCompiler::new().with_decay_rate(1.0);
        compiler.get_or_create("test", "action");
        compiler.execute("test");
        let before = compiler.productions["test->action"].strength;
        sleep(Duration::from_millis(10));
        compiler.decay_all();
        let after = compiler.productions["test->action"].strength;
        assert!(after < before);
    }

    #[test]
    fn test_matches() {
        let prod = ProductionRule::new("test", "hello", "hi");
        assert!(prod.matches("hello world"));
        assert!(!prod.matches("goodbye"));
    }
}
