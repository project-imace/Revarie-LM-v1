/**
 * test_central_executive.cpp
 * Unit tests for Central Executive.
 * Compile with: g++ -std=c++17 -o test_ce test_central_executive.cpp
 */

#include "../central_executive.cpp"
#include <cassert>
#include <iostream>
#include <thread>
#include <chrono>

using namespace revarie::memory;

void test_submit_and_process() {
    CentralExecutive ce;
    ce.submit_task(ExecutiveTask(TaskType::Rehearsal, 1));
    assert(ce.pending_tasks() == 1);
    ce.process_next();
    assert(ce.pending_tasks() == 0);
    std::cout << "[PASS] test_submit_and_process\n";
}

void test_priority_ordering() {
    CentralExecutive ce;
    ce.submit_task(ExecutiveTask(TaskType::Rehearsal, 1));
    ce.submit_task(ExecutiveTask(TaskType::Encoding, 5));
    ce.submit_task(ExecutiveTask(TaskType::Retrieval, 3));
    ce.process_next();
    assert(ce.pending_tasks() == 2);
    std::cout << "[PASS] test_priority_ordering\n";
}

void test_inhibition() {
    CentralExecutive ce;
    assert(!ce.is_inhibited("distractor"));
    ce.inhibit("distractor");
    assert(ce.is_inhibited("distractor"));
    ce.release_inhibition("distractor");
    assert(!ce.is_inhibited("distractor"));
    std::cout << "[PASS] test_inhibition\n";
}

void test_switch_cost() {
    CentralExecutive ce;
    ce.focus_on(AttentionFocus::Phonological);
    double cost1 = ce.switch_cost();
    ce.focus_on(AttentionFocus::Visuospatial);
    double cost2 = ce.switch_cost();
    assert(cost2 > cost1);
    std::cout << "[PASS] test_switch_cost\n";
}

void test_max_tasks_eviction() {
    CentralExecutive::Config config;
    config.max_tasks = 3;
    CentralExecutive ce(config);
    ce.submit_task(ExecutiveTask(TaskType::Rehearsal, 1));
    ce.submit_task(ExecutiveTask(TaskType::Encoding, 2));
    ce.submit_task(ExecutiveTask(TaskType::Retrieval, 3));
    ce.submit_task(ExecutiveTask(TaskType::Inhibition, 4));
    assert(ce.pending_tasks() == 3);
    std::cout << "[PASS] test_max_tasks_eviction\n";
}

void test_attention_span_depletion() {
    CentralExecutive::Config config;
    config.attention_span_ms = 10;
    CentralExecutive ce(config);
    ce.focus_on(AttentionFocus::Phonological);
    assert(ce.current_focus() == AttentionFocus::Phonological);
    std::this_thread::sleep_for(std::chrono::milliseconds(15));
    ce.update_attention();
    assert(ce.current_focus() == AttentionFocus::None);
    std::cout << "[PASS] test_attention_span_depletion\n";
}

int main() {
    test_submit_and_process();
    test_priority_ordering();
    test_inhibition();
    test_switch_cost();
    test_max_tasks_eviction();
    test_attention_span_depletion();
    std::cout << "All Central Executive tests passed.\n";
    return 0;
}
