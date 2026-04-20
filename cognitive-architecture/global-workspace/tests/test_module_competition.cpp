/**
 * test_module_competition.cpp
 * Unit tests for ModuleCompetition.
 * Compile with: g++ -std=c++17 -o test_mc test_module_competition.cpp
 */

#include "../module_competition.cpp"
#include <cassert>
#include <iostream>
#include <thread>
#include <chrono>

using namespace revarie::gwt;

void test_signal_activation() {
    ModuleSignal signal;
    signal.module_id = "test_module";
    signal.module_type = ModuleType::AFFECTIVE;
    signal.content = "Test content";
    signal.salience = 0.9;
    signal.confidence = 0.8;
    signal.novelty = 0.7;
    // Set timestamp to old value to disable recency boost
    signal.timestamp = std::chrono::steady_clock::now() - std::chrono::seconds(10);
    
    double activation = signal.compute_activation();
    double expected = 0.4 * 0.9 + 0.3 * 0.8 + 0.3 * 0.7;
    assert(std::abs(activation - expected) < 0.01);
    std::cout << "[PASS] test_signal_activation\n";
}

void test_competition_winner() {
    ModuleCompetition comp;
    
    ModuleSignal s1, s2;
    s1.module_id = "low";
    s1.salience = 0.3;
    s2.module_id = "high";
    s2.salience = 0.9;
    
    comp.submit_signal(s1);
    comp.submit_signal(s2);
    
    ModuleSignal winner;
    assert(comp.select_winner(winner));
    assert(winner.module_id == "high");
    std::cout << "[PASS] test_competition_winner\n";
}

void test_empty_competition() {
    ModuleCompetition comp;
    ModuleSignal dummy;
    assert(!comp.select_winner(dummy));
    assert(!comp.has_pending());
    assert(comp.pending_count() == 0);
    std::cout << "[PASS] test_empty_competition\n";
}

void test_peek_top_n() {
    ModuleCompetition comp;
    for (int i = 0; i < 5; ++i) {
        ModuleSignal s;
        s.module_id = "mod_" + std::to_string(i);
        s.salience = 0.1 * i;
        comp.submit_signal(s);
    }
    
    auto top = comp.peek_top_n(3);
    assert(top.size() == 3);
    // Should be the three with highest salience
    assert(top[0].salience >= top[1].salience);
    assert(top[1].salience >= top[2].salience);
    std::cout << "[PASS] test_peek_top_n\n";
}

void test_clear_signals() {
    ModuleCompetition comp;
    ModuleSignal s;
    s.module_id = "test";
    s.salience = 0.5;
    comp.submit_signal(s);
    assert(comp.has_pending());
    comp.clear();
    assert(!comp.has_pending());
    std::cout << "[PASS] test_clear_signals\n";
}

void test_recent_winners() {
    ModuleCompetition comp;
    for (int i = 0; i < 3; ++i) {
        ModuleSignal s;
        s.module_id = "mod_" + std::to_string(i);
        s.salience = 0.5;
        comp.submit_signal(s);
    }
    
    ModuleSignal w1, w2;
    comp.select_winner(w1);
    comp.select_winner(w2);
    
    auto recent = comp.get_recent_winners(2);
    assert(recent.size() == 2);
    assert(recent[0].module_id == w1.module_id);
    assert(recent[1].module_id == w2.module_id);
    std::cout << "[PASS] test_recent_winners\n";
}

void test_pending_count() {
    ModuleCompetition comp;
    for (int i = 0; i < 5; ++i) {
        ModuleSignal s;
        s.module_id = "mod_" + std::to_string(i);
        comp.submit_signal(s);
    }
    assert(comp.pending_count() == 5);
    ModuleSignal w;
    comp.select_winner(w);
    assert(comp.pending_count() == 4);
    std::cout << "[PASS] test_pending_count\n";
}

int main() {
    test_signal_activation();
    test_competition_winner();
    test_empty_competition();
    test_peek_top_n();
    test_clear_signals();
    test_recent_winners();
    test_pending_count();
    std::cout << "All ModuleCompetition tests passed.\n";
    return 0;
}
