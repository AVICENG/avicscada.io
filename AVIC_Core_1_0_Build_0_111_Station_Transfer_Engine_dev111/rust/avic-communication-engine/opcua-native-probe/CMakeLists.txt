cmake_minimum_required(VERSION 3.20)
project(avic_opcua_native_probe VERSION 0.1.0 LANGUAGES C)
include(FetchContent)
include(CTest)

set(UA_ENABLE_ENCRYPTION "MBEDTLS" CACHE STRING "" FORCE)
set(UA_ENABLE_PARSING ON CACHE BOOL "" FORCE)
set(UA_ENABLE_SUBSCRIPTIONS ON CACHE BOOL "" FORCE)
set(UA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(UA_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(UA_BUILD_UNIT_TESTS OFF CACHE BOOL "" FORCE)
set(UA_ENABLE_DISCOVERY OFF CACHE BOOL "" FORCE)
set(UA_ENABLE_AMALGAMATION OFF CACHE BOOL "" FORCE)

FetchContent_Declare(open62541
  GIT_REPOSITORY https://github.com/open62541/open62541.git
  GIT_TAG v1.4.21
  GIT_SHALLOW TRUE
  # The OPC UA client library does not need the large UA-Nodeset submodule.
  # Avoid Windows MAX_PATH failures while keeping the upstream source pinned.
  GIT_SUBMODULES "")
FetchContent_MakeAvailable(open62541)

add_executable(avic-opcua-native-probe src/main.c)
target_link_libraries(avic-opcua-native-probe PRIVATE open62541::open62541)
if(MSVC)
  target_compile_options(avic-opcua-native-probe PRIVATE /W4 /WX)
else()
  target_compile_options(avic-opcua-native-probe PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
if(BUILD_TESTING)
  add_test(NAME opcua_native_nodeid_selftest COMMAND avic-opcua-native-probe --self-test)
endif()
