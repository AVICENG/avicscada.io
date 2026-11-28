cmake_minimum_required(VERSION 3.20)
project(avic_paho_mqtt_c_probe VERSION 0.1.0 LANGUAGES C)

include(FetchContent)
include(CTest)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Pinned upstream Eclipse Paho MQTT C. Static async client only for the
# first native integration gate; TLS is enabled in the production Worker gate.
set(PAHO_BUILD_SHARED OFF CACHE BOOL "" FORCE)
set(PAHO_BUILD_STATIC ON CACHE BOOL "" FORCE)
set(PAHO_BUILD_SAMPLES OFF CACHE BOOL "" FORCE)
set(PAHO_BUILD_DOCUMENTATION OFF CACHE BOOL "" FORCE)
set(PAHO_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
set(PAHO_ENABLE_CPACK OFF CACHE BOOL "" FORCE)
set(PAHO_WITH_SSL OFF CACHE BOOL "" FORCE)

FetchContent_Declare(paho_mqtt_c
  GIT_REPOSITORY https://github.com/eclipse-paho/paho.mqtt.c.git
  GIT_TAG v1.3.16
  GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(paho_mqtt_c)

add_executable(avic-paho-mqtt-c-probe src/main.c)
target_link_libraries(avic-paho-mqtt-c-probe PRIVATE paho-mqtt3a-static)

if(MSVC)
  target_compile_options(avic-paho-mqtt-c-probe PRIVATE /W4 /WX)
else()
  target_compile_options(avic-paho-mqtt-c-probe PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()

if(BUILD_TESTING)
  add_test(NAME avic_paho_mqtt_c_async_lifecycle
           COMMAND avic-paho-mqtt-c-probe --self-test)
endif()
