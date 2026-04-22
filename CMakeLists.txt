cmake_minimum_required(VERSION 3.16)
project(revarie-cognitive-architecture VERSION 1.0.0 LANGUAGES CXX)

# C++17 standard required for std::optional, std::variant, etc.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler options
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|AppleClang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
    # Optimize for your environment, but keep debug symbols for now
    set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
endif()

# Find required packages
find_package(Threads REQUIRED)

# Crow (header-only) - we assume it's installed system-wide or via FetchContent
find_package(Crow QUIET)
if(NOT Crow_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        Crow
        GIT_REPOSITORY https://github.com/CrowCpp/Crow.git
        GIT_TAG v1.0+5
    )
    FetchContent_MakeAvailable(Crow)
endif()

# ------------------------------------------------------------------------------
# Cognitive Architecture Library (all C++ modules)
# ------------------------------------------------------------------------------
add_library(revarie_cognitive STATIC
    dual-process/system_two/sequential_reasoner.cpp
    global-workspace/module_competition.cpp
    active-inference/predictive_coder.cpp
    belief-space/manifold_geometry.cpp
    rebound-mechanism/rebound_force.cpp
    pomdp-engine/belief_state.cpp
)

target_include_directories(revarie_cognitive PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/dual-process
    ${CMAKE_CURRENT_SOURCE_DIR}/global-workspace
    ${CMAKE_CURRENT_SOURCE_DIR}/active-inference
    ${CMAKE_CURRENT_SOURCE_DIR}/belief-space
    ${CMAKE_CURRENT_SOURCE_DIR}/rebound-mechanism
    ${CMAKE_CURRENT_SOURCE_DIR}/pomdp-engine
)

target_link_libraries(revarie_cognitive PUBLIC
    Threads::Threads
    Crow::Crow
)

# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------
option(BUILD_TESTS "Build unit tests" ON)

if(BUILD_TESTS)
    enable_testing()
    
    # Sequential Reasoner Tests
    add_executable(test_sequential_reasoner
        dual-process/system_two/tests/test_sequential_reasoner.cpp
    )
    target_link_libraries(test_sequential_reasoner revarie_cognitive)
    add_test(NAME SequentialReasoner COMMAND test_sequential_reasoner)
    
    # Module Competition Tests
    add_executable(test_module_competition
        global-workspace/tests/test_module_competition.cpp
    )
    target_link_libraries(test_module_competition revarie_cognitive)
    add_test(NAME ModuleCompetition COMMAND test_module_competition)
    
    # Predictive Coder Tests
    add_executable(test_predictive_coder
        active-inference/tests/test_predictive_coder.cpp
    )
    target_link_libraries(test_predictive_coder revarie_cognitive)
    add_test(NAME PredictiveCoder COMMAND test_predictive_coder)
    
    # Manifold Geometry Tests
    add_executable(test_manifold_geometry
        belief-space/tests/test_manifold_geometry.cpp
    )
    target_link_libraries(test_manifold_geometry revarie_cognitive)
    add_test(NAME ManifoldGeometry COMMAND test_manifold_geometry)
    
    # Rebound Force Tests
    add_executable(test_rebound_force
        rebound-mechanism/tests/test_rebound_force.cpp
    )
    target_link_libraries(test_rebound_force revarie_cognitive)
    add_test(NAME ReboundForce COMMAND test_rebound_force)
    
    # Belief State Tests
    add_executable(test_belief_state
        pomdp-engine/tests/test_belief_state.cpp
    )
    target_link_libraries(test_belief_state revarie_cognitive)
    add_test(NAME BeliefState COMMAND test_belief_state)
endif()
