#[cfg(test)]
mod tests {
    include!("../reality_arbiter.rs");
    use super::*;

    #[test]
    fn test_arbitrate_energy_depletion() {
        let mut arbiter = RealityArbiter::new();
        let start_energy = arbiter.state.energy;
        let impulse = IdImpulse {
            id: "1".into(), drive: "libido".into(), content: "test".into(),
            intensity: 0.9, valence: 0.1, timestamp: Instant::now()
        };
        let reality = RealityCheck { context: "pub".into(), risk_level: 0.1, available_resources: vec![], social_appropriateness: 0.5 };
        arbiter.arbitrate(&impulse, &[], &reality);
        assert!(arbiter.state.energy < start_energy);
    }
}
