/**
 * bayesian_inverse_planner.cpp
 * Theory of Mind – Bayesian Inverse Planner.
 */

#include <vector>
#include <string>
#include <unordered_map>
#include <cmath>
#include <random>
#include <algorithm>
#include <iostream>
#include <cassert>

namespace revarie {
namespace tom {

struct Goal {
    std::string id;
    std::string description;
    double prior;
};

struct Action {
    std::string id;
    std::vector<std::string> preconditions;
    std::vector<std::string> effects;
};

class BayesianInversePlanner {
public:
    BayesianInversePlanner(double rationality = 1.0) : rationality_(rationality) {}

    void add_goal(const Goal& goal) {
        goals_[goal.id] = goal;
        goal_posterior_[goal.id] = goal.prior;
    }

    void add_action(const Action& action) {
        actions_[action.id] = action;
    }

    void observe_action(const std::string& action_id) {
        observed_actions_.push_back(action_id);
        update_beliefs();
    }

    std::unordered_map<std::string, double> infer_goals() const {
        return goal_posterior_;
    }

    void reset() {
        observed_actions_.clear();
        for (auto& [id, goal] : goals_) {
            goal_posterior_[id] = goal.prior;
        }
    }

private:
    void update_beliefs() {
        std::unordered_map<std::string, double> new_posterior;
        double total = 0.0;
        for (const auto& [goal_id, goal] : goals_) {
            double likelihood = compute_likelihood(goal_id);
            double posterior = likelihood * goal.prior;
            new_posterior[goal_id] = posterior;
            total += posterior;
        }
        if (total > 0.0) {
            for (auto& [id, prob] : new_posterior) {
                goal_posterior_[id] = prob / total;
            }
        }
    }

    double compute_likelihood(const std::string& goal_id) const {
        double log_likelihood = 0.0;
        for (const auto& action_id : observed_actions_) {
            log_likelihood += rationality_ * q_value(goal_id, action_id);
        }
        return std::exp(log_likelihood);
    }

    double q_value(const std::string& goal_id, const std::string& action_id) const {
        if (actions_.find(action_id) == actions_.end()) return 0.01;
        const auto& action = actions_.at(action_id);
        for (const auto& effect : action.effects) {
            if (effect == goal_id) return 2.0;
        }
        return 0.1;
    }

    std::unordered_map<std::string, Goal> goals_;
    std::unordered_map<std::string, Action> actions_;
    std::unordered_map<std::string, double> goal_posterior_;
    std::vector<std::string> observed_actions_;
    double rationality_;
};

} // namespace tom
} // namespace revarie
