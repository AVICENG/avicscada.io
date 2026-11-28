cmake_minimum_required(VERSION 3.20)
project(avic_mqtt_paho_c_worker VERSION 0.1.0 LANGUAGES C)

include(FetchContent)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

set(PAHO_BUILD_SHARED OFF CACHE BOOL "" FORCE)
set(PAHO_BUILD_STATIC ON CACHE BOOL "" FORCE)
set(PAHO_BUILD_SAMPLES OFF CACHE BOOL "" FORCE)
set(PAHO_BUILD_DOCUMENTATION OFF CACHE BOOL "" FORCE)
set(PAHO_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
set(PAHO_ENABLE_CPACK OFF CACHE BOOL "" FORCE)
set(PAHO_WITH_SSL OFF CACHE BOOL "" FORCE)
FetchContent_Declare(paho_mqtt_c
  GIT_REPOSITORY https://github.com/eclipse-paho/paho.mqtt.c.git
  GIT_TAG v1.3.16 GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(paho_mqtt_c)

set(JANSSON_BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(JANSSON_EXAMPLES OFF CACHE BOOL "" FORCE)
FetchContent_Declare(jansson
  GIT_REPOSITORY https://github.com/akheron/jansson.git
  GIT_TAG v2.14.1 GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(jansson)

if(NOT WIN32)
  find_package(Threads REQUIRED)
  find_library(UUID_LIBRARY NAMES uuid REQUIRED)
endif()

add_executable(avic-mqtt-paho-c-worker src/main.c)
target_link_libraries(avic-mqtt-paho-c-worker PRIVATE paho-mqtt3a-static jansson)
if(WIN32)
  target_link_libraries(avic-mqtt-paho-c-worker PRIVATE Rpcrt4)
else()
  target_link_libraries(avic-mqtt-paho-c-worker PRIVATE Threads::Threads ${UUID_LIBRARY})
endif()
if(MSVC)
  target_compile_options(avic-mqtt-paho-c-worker PRIVATE /W4 /WX)
else()
  target_compile_options(avic-mqtt-paho-c-worker PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
install(TARGETS avic-mqtt-paho-c-worker RUNTIME DESTINATION bin)
