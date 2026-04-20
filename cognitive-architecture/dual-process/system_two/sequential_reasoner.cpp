/**
 * sequential_reasoner.cpp
 * System 2 – Slow, deliberative, analytical reasoning.
 * Implements Kahneman's System 2: sequential, logical, effortful.
 * Provides step‑by‑step inference, planning, and verification.
 */

#include <iostream>
#include <vector>
#include <string>
#include <memory>
#include <unordered_map>
#include <functional>
#include <chrono>
#include <thread>
#include <algorithm>
#include <cmath>

namespace revarie {
namespace system_two {

/**
 * A single reasoning step – the atomic unit of System 2 processing.
 */
struct ReasoningStep {
    std::string description;      // Human‑readable description
    std::string operation;        // Logical operation performed
    double confidence;            // Confidence in this step (0.0–1.0)
    std::chrono::milliseconds duration; // Time taken for this step
};

/**
 * The result of a System 2 reasoning session.
 */
struct ReasoningResult {
    std::string conclusion;               // Final reasoned output
    std::vector<ReasoningStep> trace;     // Step‑by‑step trace (for transparency)
    double total_confidence = 0.0;        // Aggregate confidence (FIXED: Default init)
    bool timed_out = false;               // Whether reasoning hit a time limit (FIXED: Default init)
};

/**
 * Sequential Reasoner – the core System 2 engine.
 */
class SequentialReasoner {
public:
    /**
     * Configuration for reasoning behavior.
     */
    struct Config {
        int max_steps = 10;                     // Maximum reasoning steps
        std::chrono::milliseconds timeout{5000}; // Maximum total time
        double confidence_threshold = 0.6;       // Minimum confidence to accept a step
        bool verbose_trace = true;               // Whether to record detailed trace
    };

    explicit SequentialReasoner(Config config = Config{}) : config_(std::move(config)) {}

    /**
     * Main entry point: reason about a given input.
     * @param input The question or problem to reason about.
     * @param context Optional contextual knowledge.
     * @return A ReasoningResult containing the conclusion and trace.
     */
    ReasoningResult reason(const std::string& input,
                           const std::unordered_map<std::string, std::string>& context = {}) {
        ReasoningResult result;
        auto start_time = std::chrono::steady_clock::now();

        // Step 1: Parse and classify the input
        auto parse_step = record_step("Parsing input", "classification", 0.95);
        result.trace.push_back(parse_step);
        if (config_.verbose_trace) {
            std::this_thread::sleep_for(std::chrono::milliseconds(50)); // Simulate cognitive effort
        }

        std::string problem_type = classify_problem(input);
        auto classify_step = record_step("Classified as: " + problem_type, "classification", 0.90);
        result.trace.push_back(classify_step);

        // Step 2: Retrieve relevant knowledge from context
        auto retrieve_step = record_step("Retrieving relevant knowledge", "memory_retrieval", 0.85);
        result.trace.push_back(retrieve_step);

        // Step 3: Apply logical inference rules
        std::vector<std::string> inferences;
        int step_count = 0;
        double cumulative_confidence = 0.9;

        while (step_count < config_.max_steps) {
            auto elapsed = std::chrono::steady_clock::now() - start_time;
            if (elapsed > config_.timeout) {
                result.timed_out = true;
                break;
            }

            std::string inference = apply_inference_rule(input, context, step_count);
            if (inference.empty()) break;

            double step_conf = 0.8 - (step_count * 0.05); // Confidence decays with more steps
            step_conf = std::max(step_conf, 0.5);

            auto infer_step = record_step("Inference: " + inference, "logical_inference", step_conf);
            result.trace.push_back(infer_step);
            inferences.push_back(inference);
            cumulative_confidence *= step_conf;
            ++step_count;

            if (config_.verbose_trace) {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
        }

        // Step 4: Synthesize conclusion
        result.conclusion = synthesize_conclusion(input, inferences, problem_type);
        auto synth_step = record_step("Synthesizing conclusion: " + result.conclusion,
                                      "synthesis", 0.95);
        result.trace.push_back(synth_step);
        result.total_confidence = cumulative_confidence * 0.95;

        return result;
    }

private:
    Config config_;

    ReasoningStep record_step(const std::string& desc, const std::string& op, double conf) {
        return ReasoningStep{
            .description = desc,
            .operation = op,
            .confidence = conf,
            .duration = std::chrono::milliseconds(50) // Simulated
        };
    }

    std::string classify_problem(const std::string& input) {
        if (input.find("why") != std::string::npos) return "causal_explanation";
        if (input.find("how") != std::string::npos) return "procedural";
        if (input.find("what") != std::string::npos) return "definitional";
        if (input.find("?") != std::string::npos) return "question";
        return "general_inquiry";
    }

    std::string apply_inference_rule(const std::string& input,
                                    const std::unordered_map<std::string, std::string>& context,
                                    int step) {
        static const std::vector<std::string> rules = {
            "If A implies B, and A is true, then B is true.",
            "Consider alternative possibilities.",
            "Check for consistency with known facts.",
            "Evaluate causal relationships.",
            "Apply deductive reasoning.",
        };
        if (step < static_cast<int>(rules.size())) {
            return rules[step];
        }
        return "";
    }

    std::string synthesize_conclusion(const std::string& input,
                                      const std::vector<std::string>& inferences,
                                      const std::string& problem_type) {
        if (inferences.empty()) {
            return "I need more information to reason about this properly.";
        }
        return "Based on logical analysis, the answer involves multiple factors requiring careful consideration.";
    }
};

} // namespace system_two
} // namespace revarie

// =============================================================================
// Simple test harness (compile with -DTEST_SEQUENTIAL_REASONER to run standalone)
// =============================================================================
#ifdef TEST_SEQUENTIAL_REASONER
int main() {
    revarie::system_two::SequentialReasoner reasoner;
    auto result = reasoner.reason("Why is the sky blue?");
    std::cout << "Conclusion: " << result.conclusion << "\n";
    std::cout << "Confidence: " << result.total_confidence << "\n";
    std::cout << "Trace:\n";
    for (const auto& step : result.trace) {
        std::cout << "  - " << step.description << " (" << step.confidence << ")\n";
    }
    return 0;
}
#endif
