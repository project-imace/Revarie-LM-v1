#include "../bayesian_inverse_planner.cpp"
#include <iostream>
#include <cassert>

int main() {
    using namespace revarie::tom;
    BayesianInversePlanner planner(1.5);
    planner.add_goal({"food", "Get food", 0.5});
    planner.add_goal({"water", "Get water", 0.5});
    planner.add_action({"goto_kitchen", {}, {"food"}});
    planner.observe_action("goto_kitchen");
    auto goals = planner.infer_goals();
    assert(goals["food"] > goals["water"]);
    std::cout << "[PASS] C++ Bayesian planner tests\n";
    return 0;
}
