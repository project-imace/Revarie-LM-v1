#[cfg(test)]
mod tests {
    include!("../goal_inference_engine.rs");
    #[test]
    fn test_inference_logic() {
        let mut engine = GoalInferenceEngine::new(2.0);
        engine.add_goal(Goal { id: "A".into(), description: "X".into(), prior: 0.5 });
        engine.add_goal(Goal { id: "B".into(), description: "Y".into(), prior: 0.5 });
        engine.add_action(Action { id: "act".into(), effects: vec!["A".into()] });
        engine.observe("act");
        let results = engine.infer_goals();
        assert!(results["A"] > results["B"]);
    }
}
