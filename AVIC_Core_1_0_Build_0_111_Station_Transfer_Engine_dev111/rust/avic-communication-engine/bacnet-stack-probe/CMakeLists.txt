cmake_minimum_required(VERSION 3.20)
project(avic_bacnet_stack_probe VERSION 0.1.0 LANGUAGES C)

include(FetchContent)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Build only the protocol library needed by AVIC. Keep optional data links
# disabled until their own worker/serial/security acceptance plans are ready.
set(BACNET_STACK_BUILD_APPS OFF CACHE BOOL "Disable upstream demo applications" FORCE)
# The upstream project defaults BAC_ROUTING=ON, but the AVIC probe is a
# standalone BACnet/IP endpoint, not a BACnet router. Enabling routing aliases
# datalink_get_my_address to Routed_Device_Get_My_Address, which is not linked
# by this single-datalink probe.
set(BAC_ROUTING OFF CACHE BOOL "Disable router-only address provider in endpoint worker" FORCE)
set(BACDL_BIP ON CACHE BOOL "Enable BACnet/IP" FORCE)
set(BACDL_BIP6 OFF CACHE BOOL "Disable BACnet/IPv6 in first POC" FORCE)
set(BACDL_MSTP OFF CACHE BOOL "Enable MS/TP only in a later serial POC" FORCE)
set(BACDL_BSC OFF CACHE BOOL "Enable BACnet/SC only after TLS/certificate design" FORCE)
set(BACDL_ZIGBEE OFF CACHE BOOL "Disable Zigbee datalink" FORCE)
set(BACDL_ETHERNET OFF CACHE BOOL "Disable raw Ethernet datalink" FORCE)
set(BACDL_ARCNET OFF CACHE BOOL "Disable ARCNET datalink" FORCE)

FetchContent_Declare(
  bacnet_stack
  GIT_REPOSITORY https://github.com/bacnet-stack/bacnet-stack.git
  GIT_TAG 45f9831996f1a17504a790da91a4113f2974595c
  GIT_SHALLOW FALSE
)
FetchContent_MakeAvailable(bacnet_stack)

add_executable(avic-bacnet-stack-probe src/main.c)
target_link_libraries(avic-bacnet-stack-probe PRIVATE bacnet-stack)
# The pinned upstream stack uses getenv() in its platform layer. Suppress
# only MSVC's CRT deprecation diagnostic for this third-party header/API;
# keep /W4 /WX enabled for AVIC-owned probe code.
if(MSVC)
  target_compile_definitions(avic-bacnet-stack-probe PRIVATE _CRT_SECURE_NO_WARNINGS)
endif()

enable_testing()
add_test(NAME avic_bacnet_stack_version_probe COMMAND avic-bacnet-stack-probe)

if(MSVC)
  target_compile_options(avic-bacnet-stack-probe PRIVATE /W4 /WX)
else()
  target_compile_options(avic-bacnet-stack-probe PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
