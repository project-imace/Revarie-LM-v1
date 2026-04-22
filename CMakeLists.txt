cmake_minimum_required(VERSION 3.16)
project(revarie-cognitive-architecture VERSION 1.0.0 LANGUAGES CXX)

# C++17 standard required for std::optional, std::variant, etc.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Direct output so supervisord knows exactly where to find the binary
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Compiler options
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|AppleClang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
    set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
endif()

# Find required packages
find_package(Threads REQUIRED)

# Crow (header-only) internal network communication
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
# 1. Cognitive Architecture Library (Welding scattered C++ lobes)
# ------------------------------------------------------------------------------
add_library(revarie_cognitive STATIC
    main.cpp
    cognitive-architecture/global-workspace/module_competition.cpp
    cognitive-architecture/active-inference/predictive_coder.cpp
    cognitive-architecture/belief-space/manifold_geometry.cpp
    cognitive-architecture/rebound-mechanism/rebound_force.cpp
    cognitive-architecture/pomdp-engine/belief_state.cpp
    # Incorporating the broader polyglot C++ lobes
    memory-systems/working-memory/central_executive.cpp
    memory-systems/semantic-memory/knowledge_graph.cpp
    orchestrator/api-key-vault/rate_limit_monitor.cpp
    persona-engine/affective-modulator/acetylcholine_analog.cpp
    psychoanalytic-modules/jungian-functions/sensing_function.cpp
    theory-of-mind/bayesian_inverse_planner.cpp
)

target_include_directories(revarie_cognitive PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/cognitive-architecture/dual-process
    ${CMAKE_CURRENT_SOURCE_DIR}/cognitive-architecture/global-workspace
    ${CMAKE_CURRENT_SOURCE_DIR}/cognitive-architecture/active-inference
    ${CMAKE_CURRENT_SOURCE_DIR}/cognitive-architecture/belief-space
    ${CMAKE_CURRENT_SOURCE_DIR}/cognitive-architecture/rebound-mechanism
    ${CMAKE_CURRENT_SOURCE_DIR}/cognitive-architecture/pomdp-engine
    ${CMAKE_CURRENT_SOURCE_DIR}/memory-systems
    ${CMAKE_CURRENT_SOURCE_DIR}/orchestrator
    ${CMAKE_CURRENT_SOURCE_DIR}/persona-engine
    ${CMAKE_CURRENT_SOURCE_DIR}/psychoanalytic-modules
    ${CMAKE_CURRENT_SOURCE_DIR}/theory-of-mind
)

target_link_libraries(revarie_cognitive PUBLIC
    Threads::Threads
    Crow::Crow
)

# ------------------------------------------------------------------------------
# 2. Supervisord Executable (The C++ Reasoner Engine)
# ------------------------------------------------------------------------------
# We compile the library into the executable that supervisord will run on port 9000.
# Assuming your main Crow app() boot sequence is inside sequential_reasoner.cpp 
# or another file included in the static library.
add_executable(revarie_reasoner 
    main.cpp
)
target_link_libraries(revarie_reasoner revarie_cognitive)

# ------------------------------------------------------------------------------
# 3. Tests
# ------------------------------------------------------------------------------
option(BUILD_TESTS "Build unit tests" ON)

if(BUILD_TESTS)
    enable_testing()
    
    add_executable(test_sequential_reasoner cognitive-architecture/dual-process/system_two/tests/test_sequential_reasoner.cpp)
    target_link_libraries(test_sequential_reasoner revarie_cognitive)
    add_test(NAME SequentialReasoner COMMAND test_sequential_reasoner)
    
    add_executable(test_module_competition cognitive-architecture/global-workspace/tests/test_module_competition.cpp)
    target_link_libraries(test_module_competition revarie_cognitive)
    add_test(NAME ModuleCompetition COMMAND test_module_competition)
    
    add_executable(test_predictive_coder cognitive-architecture/active-inference/tests/test_predictive_coder.cpp)
    target_link_libraries(test_predictive_coder revarie_cognitive)
    add_test(NAME PredictiveCoder COMMAND test_predictive_coder)
    
    add_executable(test_manifold_geometry cognitive-architecture/belief-space/tests/test_manifold_geometry.cpp)
    target_link_libraries(test_manifold_geometry revarie_cognitive)
    add_test(NAME ManifoldGeometry COMMAND test_manifold_geometry)
    
    add_executable(test_rebound_force cognitive-architecture/rebound-mechanism/tests/test_rebound_force.cpp)
    target_link_libraries(test_rebound_force revarie_cognitive)
    add_test(NAME ReboundForce COMMAND test_rebound_force)
    
    add_executable(test_belief_state cognitive-architecture/pomdp-engine/tests/test_belief_state.cpp)
    target_link_libraries(test_belief_state revarie_cognitive)
    add_test(NAME BeliefState COMMAND test_belief_state)
endif()
