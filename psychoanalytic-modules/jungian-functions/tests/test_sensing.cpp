#include "../sensing_function.cpp"
#include <cassert>

int main() {
    revarie::jungian::SensingFunction sf;
    sf.perceive("Red light", 0.9);
    assert(sf.size() == 1);
    sf.apply_decay(10.0); // Extreme decay
    std::cout << "[PASS] Sensing C++\n";
    return 0;
}
