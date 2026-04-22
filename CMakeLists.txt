cmake_minimum_required(VERSION 3.16)
project(revarie-cognitive-architecture VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Matches the supervisord path we will set below
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|AppleClang")
    add_compile_options(-Wall -Wextra -Wpedantic)
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
endif()

find_package(Threads REQUIRED)

# Crow for internal network communication
include(FetchContent)
FetchContent_Declare(
    Crow
    GIT_REPOSITORY https://github.com/CrowCpp/Crow.git
    GIT_TAG v1.0+5
)
FetchContent_MakeAvailable(Crow)

# 1. Cognitive Architecture Library (The Lobes)
add_library(revarie_cognitive STATIC
    cognitive-architecture/global-workspace/module_competition.cpp
    cognitive-architecture/active-inference/predictive_coder.cpp
    cognitive-architecture/belief-space/manifold_geometry.cpp
    cognitive-architecture/rebound-mechanism/rebound_force.cpp
    cognitive-architecture/pomdp-engine/belief_state.cpp
    memory-systems/working-memory/central_executive.cpp
    memory-systems/semantic-memory/knowledge_graph.cpp
    orchestrator/api-key-vault/rate_limit_monitor.cpp
    persona-engine/affective-modulator/acetylcholine_analog.cpp
    psychoanalytic-modules/jungian-functions/sensing_function.cpp
    theory-of-mind/bayesian_inverse_planner.cpp
)

target_include_directories(revarie_cognitive PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(revarie_cognitive PUBLIC Threads::Threads Crow::Crow)

# 2. The Reasoner Executable (The Boot-up)
add_executable(revarie_reasoner main.cpp)
target_link_libraries(revarie_reasoner revarie_cognitive)
