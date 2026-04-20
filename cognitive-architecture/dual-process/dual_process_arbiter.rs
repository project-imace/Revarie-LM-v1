//! dual_process_arbiter.rs
//! Arbiter that decides whether to engage System 1 or System 2.
//! Implements the dual‑process control logic described by Kahneman (2011)
//! and Stanovich (2010).

use std::time::Duration; // Removed unused Instant import

/// The type of cognitive task presented to the system.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskType {
    /// Simple, routine, pattern‑based queries (System 1).
    Routine,
    /// Complex, novel, or ambiguous queries (System 2).
    Complex,
    /// Emotional or social interaction (may use either).
    Social,
    /// Unknown; requires further analysis.
    Unknown,
}

/// Result of the arbitration decision.
#[derive(Debug, Clone, PartialEq)]
pub enum ArbitrationDecision {
    /// Use System 1 (fast, heuristic).
    System1 { confidence: f64, reason: String },
    /// Use System 2 (slow, deliberative).
    System2 { reason: String, expected_duration: Duration },
    /// Needs more information to decide.
    Undecided,
}

/// The DualProcessArbiter evaluates incoming stimuli and decides
/// which cognitive system should handle the response.
pub struct DualProcessArbiter {
    /// Minimum confidence required for System 1 to be used.
    system1_confidence_threshold: f64,
    /// Maximum expected duration (ms) before forcing System 1 fallback.
    max_system2_duration: Duration,
    /// Whether to log arbitration decisions.
    verbose: bool,
}

impl Default for DualProcessArbiter {
    fn default() -> Self {
        Self {
            system1_confidence_threshold: 0.7,
            max_system2_duration: Duration::from_millis(5000),
            verbose: false,
        }
    }
}

impl DualProcessArbiter {
    /// Creates a new arbiter with default settings.
    pub fn new() -> Self {
        Self::default()
    }

    /// Sets the confidence threshold for System 1 engagement.
    pub fn with_confidence_threshold(mut self, threshold: f64) -> Self {
        self.system1_confidence_threshold = threshold.clamp(0.0, 1.0);
        self
    }

    /// Sets the maximum allowed duration for System 2 reasoning.
    pub fn with_max_system2_duration(mut self, duration: Duration) -> Self {
        self.max_system2_duration = duration;
        self
    }

    /// Enables verbose logging of arbitration decisions.
    pub fn with_verbose(mut self, verbose: bool) -> Self {
        self.verbose = verbose;
        self
    }

    /// Main arbitration method.
    /// Takes the input text and optional System 1 confidence score.
    pub fn arbitrate(&self, input: &str, system1_confidence: Option<f64>) -> ArbitrationDecision {
        let task_type = self.classify_task(input);

        // 1. Complex or Unknown tasks always require System 2 deliberation.
        if task_type == TaskType::Complex || task_type == TaskType::Unknown {
            if self.verbose {
                eprintln!("[Arbiter] System 2 selected (task type: {:?})", task_type);
            }
            return ArbitrationDecision::System2 {
                reason: format!("Task classified as {:?}", task_type),
                expected_duration: self.max_system2_duration,
            };
        }

        // 2. For Routine or Social tasks, check System 1 confidence.
        if let Some(conf) = system1_confidence {
            if conf >= self.system1_confidence_threshold {
                if self.verbose {
                    eprintln!("[Arbiter] System 1 selected (confidence: {:.2})", conf);
                }
                return ArbitrationDecision::System1 {
                    confidence: conf,
                    reason: format!("High confidence heuristic match ({:.2})", conf),
                };
            } else {
                if self.verbose {
                    eprintln!("[Arbiter] System 2 selected (low confidence: {:.2})", conf);
                }
                return ArbitrationDecision::System2 {
                    reason: "System 1 confidence below threshold".to_string(),
                    expected_duration: self.max_system2_duration,
                };
            }
        }

        // 3. If no System 1 confidence was provided at all, fallback to System 2.
        if self.verbose {
            eprintln!("[Arbiter] System 2 selected (no System 1 match provided)");
        }
        ArbitrationDecision::System2 {
            reason: "No System 1 heuristic available".to_string(),
            expected_duration: self.max_system2_duration,
        }
    }

    /// Classifies the input text into a task type.
    fn classify_task(&self, input: &str) -> TaskType {
        let input_lower = input.to_lowercase();

        // Heuristics for classification.
        let is_question = input.contains('?');
        let is_emotional = input_lower.contains("feel")
            || input_lower.contains("sad")
            || input_lower.contains("happy")
            || input_lower.contains("angry")
            || input_lower.contains("love");
        let is_complex = input_lower.contains("why")
            || input_lower.contains("how")
            || input_lower.contains("explain")
            || input_lower.contains("analyze")
            || input_lower.contains("compare");
        let is_simple = input_lower.contains("hello")
            || input_lower.contains("hi")
            || input_lower.contains("thanks")
            || input_lower.contains("bye");

        if is_emotional {
            TaskType::Social
        } else if is_complex {
            TaskType::Complex
        } else if is_simple && !is_question {
            TaskType::Routine
        } else if is_question && !is_complex {
            TaskType::Routine
        } else {
            TaskType::Unknown
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arbitrate_system1_high_confidence() {
        let arbiter = DualProcessArbiter::new().with_confidence_threshold(0.6);
        let decision = arbiter.arbitrate("Hello there!", Some(0.9));
        assert!(matches!(decision, ArbitrationDecision::System1 { .. }));
    }

    #[test]
    fn test_arbitrate_system2_complex() {
        let arbiter = DualProcessArbiter::new();
        let decision = arbiter.arbitrate("Why is the sky blue?", None);
        assert!(matches!(decision, ArbitrationDecision::System2 { .. }));
    }

    #[test]
    fn test_arbitrate_system2_low_confidence() {
        let arbiter = DualProcessArbiter::new().with_confidence_threshold(0.8);
        let decision = arbiter.arbitrate("What is the time?", Some(0.4));
        assert!(matches!(decision, ArbitrationDecision::System2 { .. }));
    }

    #[test]
    fn test_classify_emotional() {
        let arbiter = DualProcessArbiter::new();
        let decision = arbiter.arbitrate("I feel sad today", None);
        assert!(matches!(decision, ArbitrationDecision::System2 { .. }));
    }
}
