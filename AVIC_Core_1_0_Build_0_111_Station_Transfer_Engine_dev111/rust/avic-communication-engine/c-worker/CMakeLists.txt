cmake_minimum_required(VERSION 3.20)
project(avic_modbus_c_worker VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
  pkg_check_modules(LIBMODBUS QUIET IMPORTED_TARGET libmodbus)
  pkg_check_modules(JANSSON QUIET IMPORTED_TARGET jansson)
endif()

if(NOT TARGET PkgConfig::LIBMODBUS)
  find_path(LIBMODBUS_INCLUDE_DIR modbus.h REQUIRED)
  find_library(LIBMODBUS_LIBRARY NAMES modbus libmodbus REQUIRED)
  add_library(libmodbus_external UNKNOWN IMPORTED)
  set_target_properties(libmodbus_external PROPERTIES
    IMPORTED_LOCATION "${LIBMODBUS_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${LIBMODBUS_INCLUDE_DIR}")
  set(LIBMODBUS_TARGET libmodbus_external)
else()
  set(LIBMODBUS_TARGET PkgConfig::LIBMODBUS)
endif()

if(NOT TARGET PkgConfig::JANSSON)
  find_path(JANSSON_INCLUDE_DIR jansson.h REQUIRED)
  find_library(JANSSON_LIBRARY NAMES jansson REQUIRED)
  add_library(jansson_external UNKNOWN IMPORTED)
  set_target_properties(jansson_external PROPERTIES
    IMPORTED_LOCATION "${JANSSON_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${JANSSON_INCLUDE_DIR}")
  set(JANSSON_TARGET jansson_external)
else()
  set(JANSSON_TARGET PkgConfig::JANSSON)
endif()

add_executable(avic-modbus-c-worker src/main.c)
target_link_libraries(avic-modbus-c-worker PRIVATE ${LIBMODBUS_TARGET} ${JANSSON_TARGET})
if(WIN32)
  target_link_libraries(avic-modbus-c-worker PRIVATE Rpcrt4)
  # Ship a self-contained worker: DriverManager intentionally launches workers
  # with a restricted environment, so do not depend on MSYS2/UCRT DLL search paths.
  if(MINGW)
    target_link_options(avic-modbus-c-worker PRIVATE -static -static-libgcc)
  endif()
else()
  find_library(UUID_LIBRARY NAMES uuid REQUIRED)
  target_link_libraries(avic-modbus-c-worker PRIVATE ${UUID_LIBRARY})
endif()

if(MSVC)
  target_compile_options(avic-modbus-c-worker PRIVATE /W4 /WX)
else()
  target_compile_options(avic-modbus-c-worker PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()

install(TARGETS avic-modbus-c-worker RUNTIME DESTINATION bin)
