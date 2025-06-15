cmake_minimum_required(VERSION 3.16)
project(PhotoPrism VERSION 0.1.0 LANGUAGES C CXX Go)

# Options
option(BUILD_TESTING "Build tests" ON)
option(USE_NINJA "Use Ninja build system" ON)
option(ENABLE_BRAINS "Enable AI brains functionality" ON)
option(ENABLE_TENSORFLOW "Enable TensorFlow integration" ON)
option(BUILD_PRODUCTION "Build for production" OFF)
option(ENABLE_SANITIZERS "Enable sanitizers in debug builds" OFF)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set Go environment
set(GO_ROOT $ENV{GOPATH})
if(NOT GO_ROOT)
    set(GO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.go")
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# Find required packages
find_package(Git REQUIRED)
find_package(Threads REQUIRED)

# Define build paths
set(BUILD_OUTPUT_PATH ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Get version from Git
execute_process(
    COMMAND git describe --always
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    OUTPUT_VARIABLE GIT_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Set build date
string(TIMESTAMP BUILD_DATE "%y%m%d" UTC)
set(BUILD_ID "${BUILD_DATE}-${GIT_VERSION}")

# Configure build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Build type" FORCE)
endif()

# Create build configuration
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/BuildConfig.h.in
    ${CMAKE_BINARY_DIR}/generated/BuildConfig.h
)

# Add subdirectories
add_subdirectory(internal)
add_subdirectory(pkg)
if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()

# Custom targets
add_custom_target(download_models
    COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/scripts/download-brains.sh
    COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/scripts/download-facenet.sh
    COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/scripts/download-nasnet.sh
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Downloading AI models"
)

add_custom_target(frontend
    COMMAND npm ci --no-update-notifier --no-audit
    COMMAND npm run build
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/frontend
    COMMENT "Building frontend"
)

add_custom_target(docker_build
    COMMAND docker compose build --pull
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Building Docker containers"
)

# Main target
add_custom_target(photoprism ALL
    DEPENDS download_models frontend
    COMMAND go build -tags="${BUILD_TAGS}" -ldflags "-X main.version=${BUILD_ID}" -o ${BUILD_OUTPUT_PATH}/photoprism ${CMAKE_CURRENT_SOURCE_DIR}/cmd/photoprism/photoprism.go
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Building PhotoPrism"
)

# Install targets
install(
    DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/assets/
    DESTINATION assets
    PATTERN ".buildignore" EXCLUDE
)

install(
    PROGRAMS ${BUILD_OUTPUT_PATH}/photoprism
    DESTINATION bin
)

# Print build configuration
message(STATUS "PhotoPrism Build Configuration:")
message(STATUS "  Version: ${BUILD_ID}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Enable Brains: ${ENABLE_BRAINS}")
message(STATUS "  Enable TensorFlow: ${ENABLE_TENSORFLOW}")
message(STATUS "  Build Testing: ${BUILD_TESTING}")
