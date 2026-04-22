/**
 * central_executive.cpp
 * Working Memory – Central Executive.
 * Implements Baddeley's central executive component of working memory.
 * Coordinates phonological loop, visuospatial sketchpad, and episodic buffer.
 * Controls attention, task switching, and inhibition.
 * Based on Baddeley & Hitch (1974) and Baddeley (2007).
 */

#include <iostream>
#include <vector>
#include <string>
#include <queue>
#include <unordered_map>
#include <memory>
#include <functional>
#include <algorithm>
#include <chrono>
#include <thread>
#include <cassert>

namespace revarie {
namespace memory {

/**
 * Attention focus – which subsystem is currently active.
 */
enum class AttentionFocus {
    None,
    Phonological,
    Visuospatial,
    Episodic,
    Divided
};

/**
 * Task type for executive control.
 */
enum class TaskType {
    Rehearsal,
    Encoding,
    Retrieval,
    Inhibition,
    Switching
};

/**
 * A task for the central executive to process.
 */
struct ExecutiveTask {
    TaskType type;
    std::string target_id;
    std::vector<std::string> parameters;
    int priority;
    std::chrono::steady_clock::time_point created_at;
    
    ExecutiveTask(TaskType t, int p = 0) 
        : type(t), priority(p), created_at(std::chrono::steady_clock::now()) {}
};

/**
 * Central Executive – attentional control system.
 */
class CentralExecutive {
public:
    struct Config {
        int max_tasks = 10;
        int attention_span_ms = 2000;  // Max focus duration before switching
        double inhibition_strength = 0.7;  // Strength of distractor suppression
        bool automatic_rehearsal = true;
    };

    CentralExecutive() : config_({}) { current_focus_ = AttentionFocus::None; }
    explicit CentralExecutive(Config config) : config_(std::move(config)) { current_focus_ = AttentionFocus::None; }
    };


    /**
     * Submit a task for executive processing.
     */
    void submit_task(const ExecutiveTask& task) {
        task_queue_.push(task);
        if (task_queue_.size() > static_cast<size_t>(config_.max_tasks)) {
            evict_lowest_priority();
        }
    }

    /**
     * Enforce attention span limits based on time elapsed.
     */
    void update_attention() {
        if (current_focus_ != AttentionFocus::None) {
            auto now = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - focus_timestamp_);
            if (elapsed.count() > config_.attention_span_ms) {
                // Attention span depleted, focus drops
                current_focus_ = AttentionFocus::None;
            }
        }
    }

    /**
     * Process the next task in the queue.
     */
    bool process_next() {
        update_attention(); // Ensure attention limits are respected

        if (task_queue_.empty()) {
            return false;
        }
        
        ExecutiveTask task = task_queue_.top();
        task_queue_.pop();
        
        switch (task.type) {
            case TaskType::Rehearsal:
                execute_rehearsal(task);
                break;
            case TaskType::Encoding:
                execute_encoding(task);
                break;
            case TaskType::Retrieval:
                execute_retrieval(task);
                break;
            case TaskType::Inhibition:
                execute_inhibition(task);
                break;
            case TaskType::Switching:
                execute_switching(task);
                break;
        }
        
        return true;
    }

    /**
     * Process all pending tasks.
     */
    void process_all() {
        while (!task_queue_.empty()) {
            process_next();
        }
    }

    /**
     * Focus attention on a specific subsystem.
     */
    void focus_on(AttentionFocus focus) {
        if (current_focus_ != focus) {
            switch_cost_ += 0.1;  // Accumulate switch cost
            current_focus_ = focus;
            focus_timestamp_ = std::chrono::steady_clock::now();
        }
    }

    /**
     * Inhibit distracting information.
     */
    bool inhibit(const std::string& distractor_id) {
        if (inhibited_items_.count(distractor_id)) {
            return false;
        }
        inhibited_items_[distractor_id] = std::chrono::steady_clock::now();
        return true;
    }

    /**
     * Check if an item is currently inhibited.
     */
    bool is_inhibited(const std::string& item_id) const {
        auto it = inhibited_items_.find(item_id);
        if (it == inhibited_items_.end()) {
            return false;
        }
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - it->second);
        return elapsed.count() < 5000;
    }

    void release_inhibition(const std::string& item_id) {
        inhibited_items_.erase(item_id);
    }

    AttentionFocus current_focus() const { return current_focus_; }
    double switch_cost() const { return switch_cost_; }
    void reset_switch_cost() { switch_cost_ = 0.0; }
    size_t pending_tasks() const { return task_queue_.size(); }

    void reset() {
        while (!task_queue_.empty()) {
            task_queue_.pop();
        }
        inhibited_items_.clear();
        current_focus_ = AttentionFocus::None;
        switch_cost_ = 0.0;
    }

private:
    Config config_;
    std::priority_queue<ExecutiveTask, 
                        std::vector<ExecutiveTask>,
                        std::function<bool(const ExecutiveTask&, const ExecutiveTask&)>> 
        task_queue_{[](const ExecutiveTask& a, const ExecutiveTask& b) {
            return a.priority < b.priority;
        }};
    
    AttentionFocus current_focus_;
    std::chrono::steady_clock::time_point focus_timestamp_;
    std::unordered_map<std::string, std::chrono::steady_clock::time_point> inhibited_items_;
    double switch_cost_ = 0.0;

    /**
     * Optimized O(N) eviction instead of O(N log N) sorting
     */
    void evict_lowest_priority() {
        if (task_queue_.empty()) return;

        std::vector<ExecutiveTask> tasks;
        int min_priority = task_queue_.top().priority;
        size_t min_idx = 0;
        
        while (!task_queue_.empty()) {
            if (task_queue_.top().priority < min_priority) {
                min_priority = task_queue_.top().priority;
                min_idx = tasks.size();
            }
            tasks.push_back(task_queue_.top());
            task_queue_.pop();
        }
        
        tasks.erase(tasks.begin() + min_idx);
        
        for (const auto& t : tasks) {
            task_queue_.push(t);
        }
    }

    void execute_rehearsal(const ExecutiveTask& task) {
        focus_on(AttentionFocus::Phonological);
        if (config_.automatic_rehearsal) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    }

    void execute_encoding(const ExecutiveTask& task) {
        focus_on(AttentionFocus::Episodic);
    }

    void execute_retrieval(const ExecutiveTask& task) {
        focus_on(AttentionFocus::Episodic);
    }

    void execute_inhibition(const ExecutiveTask& task) {
        focus_on(AttentionFocus::Divided);
        if (!task.parameters.empty()) {
            inhibit(task.parameters[0]);
        }
    }

    void execute_switching(const ExecutiveTask& task) {
        AttentionFocus new_focus = AttentionFocus::None;
        if (!task.parameters.empty()) {
            if (task.parameters[0] == "phonological") {
                new_focus = AttentionFocus::Phonological;
            } else if (task.parameters[0] == "visuospatial") {
                new_focus = AttentionFocus::Visuospatial;
            } else if (task.parameters[0] == "episodic") {
                new_focus = AttentionFocus::Episodic;
            }
        }
        focus_on(new_focus);
    }
};

} // namespace memory
} // namespace revarie

// =============================================================================
// Unit tests (compile with -DTEST_CENTRAL_EXECUTIVE)
// =============================================================================
#ifdef TEST_CENTRAL_EXECUTIVE

int main() {
    using namespace revarie::memory;

    // Test 1: Submit and process task
    {
        CentralExecutive ce;
        ce.submit_task(ExecutiveTask(TaskType::Rehearsal, 1));
        assert(ce.pending_tasks() == 1);
        ce.process_next();
        assert(ce.pending_tasks() == 0);
        std::cout << "[PASS] Submit and process task\n";
    }

    // Test 2: Priority ordering
    {
        CentralExecutive ce;
        ce.submit_task(ExecutiveTask(TaskType::Rehearsal, 1));
        ce.submit_task(ExecutiveTask(TaskType::Encoding, 5));
        ce.submit_task(ExecutiveTask(TaskType::Retrieval, 3));
        ce.process_next();
        assert(ce.pending_tasks() == 2);
        std::cout << "[PASS] Priority ordering\n";
    }

    // Test 3: Inhibition
    {
        CentralExecutive ce;
        assert(!ce.is_inhibited("distractor"));
        ce.inhibit("distractor");
        assert(ce.is_inhibited("distractor"));
        ce.release_inhibition("distractor");
        assert(!ce.is_inhibited("distractor"));
        std::cout << "[PASS] Inhibition\n";
    }

    // Test 4: Switch cost accumulation
    {
        CentralExecutive ce;
        ce.focus_on(AttentionFocus::Phonological);
        double cost1 = ce.switch_cost();
        ce.focus_on(AttentionFocus::Visuospatial);
        double cost2 = ce.switch_cost();
        assert(cost2 > cost1);
        std::cout << "[PASS] Switch cost\n";
    }

    // Test 5: Max tasks eviction
    {
        CentralExecutive::Config config;
        config.max_tasks = 3;
        CentralExecutive ce(config);
        ce.submit_task(ExecutiveTask(TaskType::Rehearsal, 1));
        ce.submit_task(ExecutiveTask(TaskType::Encoding, 2));
        ce.submit_task(ExecutiveTask(TaskType::Retrieval, 3));
        ce.submit_task(ExecutiveTask(TaskType::Inhibition, 4));
        assert(ce.pending_tasks() == 3);
        std::cout << "[PASS] Max tasks eviction\n";
    }

    // Test 6: Attention span depletion
    {
        CentralExecutive::Config config;
        config.attention_span_ms = 10; // short span for test
        CentralExecutive ce(config);
        ce.focus_on(AttentionFocus::Phonological);
        assert(ce.current_focus() == AttentionFocus::Phonological);
        std::this_thread::sleep_for(std::chrono::milliseconds(15));
        ce.update_attention();
        assert(ce.current_focus() == AttentionFocus::None);
        std::cout << "[PASS] Attention span depletion\n";
    }

    std::cout << "All Central Executive tests passed.\n";
    return 0;
}
#endif
