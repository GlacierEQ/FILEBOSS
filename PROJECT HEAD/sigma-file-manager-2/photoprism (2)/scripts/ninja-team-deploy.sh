#!/bin/bash
set -e

# Ninja Team Deploy - Advanced Recursive Deployment System
# This orchestrates a team of build agents for optimized deployment

# Configuration
NINJA_TEAM_CONFIG="${NINJA_TEAM_CONFIG:-config/ninja-team.yml}"
DEPLOYMENT_LEVELS=${DEPLOYMENT_LEVELS:-3}
TEAM_SIZE=${TEAM_SIZE:-4}
BUILD_MODE=${BUILD_MODE:-parallel}
LOG_FILE="ninja-team-deploy_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to parse YAML config
parse_yaml() {
  local yaml_file=$1
  local prefix=$2
  local s='[[:space:]]*'
  local w='[a-zA-Z0-9_]*'
  local fs=$(echo @|tr @ '\034')
  
  sed -ne "s|^\($s\):|\1|" \
      -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
      -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p" "$yaml_file" |
  awk -F$fs '{
    indent = length($1)/2;
    vname[indent] = $2;
    for (i in vname) {if (i > indent) {delete vname[i]}}
    if (length($3) > 0) {
      vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
      printf("%s%s=%s\n", "'$prefix'", vn$2, $3);
    }
  }'
}

# Function to validate environment
validate_environment() {
  log "Validating ninja team environment..."
  
  # Check if Docker is installed
  if ! command -v docker &> /dev/null; then
    log "ERROR: Docker not found. Please install Docker first."
    exit 1
  fi
  
  # Check if Ninja build system is installed
  if ! command -v ninja &> /dev/null; then
    log "ERROR: Ninja build system not found. Please install Ninja first."
    exit 1
  fi
  
  # Check if the team config exists
  if [ ! -f "$NINJA_TEAM_CONFIG" ]; then
    log "ERROR: Ninja team configuration file not found at $NINJA_TEAM_CONFIG"
    exit 1
  fi
  
  # Validate team size
  if [ "$TEAM_SIZE" -lt 1 ] || [ "$TEAM_SIZE" -gt 16 ]; then
    log "ERROR: Invalid team size. Must be between 1 and 16."
    exit 1
  }
  
  log "Environment validation complete."
}

# Function to initialize the ninja team
initialize_team() {
  log "Initializing ninja build team with $TEAM_SIZE members..."
  
  # Load team configuration
  eval $(parse_yaml "$NINJA_TEAM_CONFIG" "config_")
  
  # Create build directories
  for i in $(seq 1 $TEAM_SIZE); do
    mkdir -p "build/ninja-$i"
    log "Initialized ninja $i build environment"
  done
  
  # Generate ninja build files for each team member
  for i in $(seq 1 $TEAM_SIZE); do
    generate_ninja_build_file $i
  done
  
  log "Ninja team initialization complete."
}

# Function to generate specialized ninja build files
generate_ninja_build_file() {
  local ninja_id=$1
  local specialization=""
  
  case $(($ninja_id % 4)) in
    0) specialization="frontend" ;;
    1) specialization="backend" ;;
    2) specialization="database" ;;
    3) specialization="ai" ;;
  esac
  
  log "Generating build file for ninja $ninja_id (specialization: $specialization)..."
  
  # Create specialized build file
  cat > "build/ninja-$ninja_id/build.ninja" <<EOF
# Ninja build file for team member $ninja_id ($specialization)
builddir = build/ninja-$ninja_id
ninja_required_version = 1.8.2

# Import common rules
include ../common.ninja

# Specialized targets for $specialization
build \$builddir/specialized: phony
  pool = console
  description = Building specialized components for $specialization

build \$builddir/deploy: custom_deploy
  inputs = \$builddir/specialized
  description = Deploying $specialization components

# Default target
default \$builddir/deploy
EOF

  log "Build file for ninja $ninja_id created."
}

# Function to execute recursive deployment
recursive_deploy() {
  local level=$1
  local parent=$2
  
  if [ "$level" -gt "$DEPLOYMENT_LEVELS" ]; then
    log "Reached maximum recursion level"
    return
  fi
  
  log "Starting recursive deployment level $level (parent: $parent)..."
  
  # Determine which team members to deploy at this level
  local team_members=$(get_team_members_for_level $level $parent)
  
  # Execute deployment for each team member
  for member in $team_members; do
    deploy_team_member $member $level || {
      log "ERROR: Deployment failed for ninja $member at level $level. Aborting."
      return 1
    } &
    
    if [ "$BUILD_MODE" = "sequential" ]; then
      wait
    fi
  done
  
  # Wait for parallel builds to complete
  if [ "$BUILD_MODE" = "parallel" ]; then
    wait
  fi
  
  log "Recursive deployment level $level complete."
  
  # Launch next level recursively if not at max level
  if [ "$level" -lt "$DEPLOYMENT_LEVELS" ]; then
    recursive_deploy $(($level + 1)) "$team_members" || return 1
  fi
}

# Get team members for a specific recursion level
get_team_members_for_level() {
  local level=$1
  local parent=$2
  
  # Algorithm to distribute team members across recursion levels
  if [ "$level" -eq 1 ]; then
    echo "$(seq 1 $TEAM_SIZE)"
  else
    # Distribute team members based on parent and level
    local members=""
    for p in $parent; do
      members="$members $((($p * 7) % $TEAM_SIZE + 1))"
    done
    echo "$members" | tr ' ' '\n' | sort -nu | tr '\n' ' '
  fi
}

# Deploy a specific team member
deploy_team_member() {
  local member=$1
  local level=$2
  
  log "Deploying team member $member at level $level..."
  
  # Run the ninja build for this team member
  (cd "build/ninja-$member" && ninja -v) || {
    log "ERROR: Deployment failed for ninja $member"
    return 1
  }
  
  log "Deployment for ninja $member at level $level completed successfully."
  return 0
}

# Function to create common build configuration
create_common_build_config() {
  log "Creating common build configuration..."
  
  cat > "build/common.ninja" <<EOF
# Common build rules for ninja team

# Variables
go_tags = brains
ldflags = -X main.version=\$(shell git describe --always)-\$(shell date -u +%y%m%d)

# Rules
rule go_build
  command = go build -tags="\$go_tags" -ldflags="\$ldflags" -o \$out \$in
  description = Building Go binary \$out

rule download_models
  command = ./scripts/download-brains.sh && ./scripts/download-facenet.sh && ./scripts/download-nasnet.sh
  description = Downloading AI models

rule docker_build
  command = docker compose -f docker/docker-compose.prod.yml build --pull \$service
  description = Building Docker image for \$service

rule custom_deploy
  command = ./scripts/ninja/deploy-ninja.sh \$specialization
  description = Deploying with ninja team

rule test
  command = go test -v ./...
  description = Running tests
EOF

  log "Common build configuration created."
}

# Function to monitor deployment status
monitor_deployment() {
  log "Starting deployment monitor..."
  
  local start_time=$(date +%s)
  local status_file="build/deployment-status.json"
  
  cat > "$status_file" <<EOF
{
  "status": "in_progress",
  "started_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "team_size": $TEAM_SIZE,
  "recursion_levels": $DEPLOYMENT_LEVELS
}
EOF
  
  # Start deployment in background
  recursive_deploy 1 "0" || {
    log "ERROR: Recursive deployment failed. See logs for details."
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    cat > "$status_file" <<EOF
{
  "status": "failed",
  "started_at": "$(date -u -d @$start_time +"%Y-%m-%dT%H:%M:%SZ")",
  "failed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "duration_seconds": $duration,
  "team_size": $TEAM_SIZE,
  "recursion_levels": $DEPLOYMENT_LEVELS
}
EOF
    return 1
  } &
  local deploy_pid=$!
  
  # Monitor progress
  while kill -0 $deploy_pid 2>/dev/null; do
    local elapsed=$(($(date +%s) - start_time))
    log "Deployment in progress... (${elapsed}s elapsed)"
    sleep 10
  done
  
  # Check if deployment completed successfully
  wait $deploy_pid
  local deploy_status=$?
  
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  
  if [ $deploy_status -eq 0 ]; then
    log "Deployment completed successfully in ${duration}s"
    cat > "$status_file" <<EOF
{
  "status": "success",
  "started_at": "$(date -u -d @$start_time +"%Y-%m-%dT%H:%M:%SZ")",
  "completed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "duration_seconds": $duration,
  "team_size": $TEAM_SIZE,
  "recursion_levels": $DEPLOYMENT_LEVELS
}
EOF
  else
    log "Deployment failed after ${duration}s"
    cat > "$status_file" <<EOF
{
  "status": "failed",
  "started_at": "$(date -u -d @$start_time +"%Y-%m-%dT%H:%M:%SZ")",
  "failed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "duration_seconds": $duration,
  "team_size": $TEAM_SIZE,
  "recursion_levels": $DEPLOYMENT_LEVELS
}
EOF
    return 1
  fi
}

# Main execution
main() {
  log "Starting Ninja Team deployment system..."
  validate_environment
  initialize_team
  create_common_build_config
  monitor_deployment
  log "Ninja Team deployment process completed."
}

main "$@"
