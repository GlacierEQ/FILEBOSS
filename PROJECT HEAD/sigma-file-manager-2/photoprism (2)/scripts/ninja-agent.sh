#!/bin/bash
set -e

# Ninja Agent - Individual Build Agent in the Ninja Team
# Handles specialized tasks as part of the recursive deployment process

# Configuration
AGENT_ID=${AGENT_ID:-1}
SPECIALIZATION=${SPECIALIZATION:-general}
NINJA_TEAM_CONFIG="${NINJA_TEAM_CONFIG:-config/ninja-team.yml}"
BUILD_DIR="build/ninja-$AGENT_ID"
LOG_FILE="$BUILD_DIR/agent-$AGENT_ID.log"

# Function to log messages
log() {
  echo "[Agent-$AGENT_ID] [$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
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

# Function to initialize agent
initialize_agent() {
  log "Initializing agent $AGENT_ID with specialization: $SPECIALIZATION"
  
  mkdir -p "$BUILD_DIR"
  
  # Load configuration
  eval $(parse_yaml "$NINJA_TEAM_CONFIG" "config_")
  
  # Generate working files
  cat > "$BUILD_DIR/agent-info.json" <<EOF
{
  "id": $AGENT_ID,
  "specialization": "$SPECIALIZATION",
  "status": "initialized",
  "initialized_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
  
  log "Agent initialized successfully"
}

# Function to execute agent tasks
execute_tasks() {
  log "Executing tasks for specialization: $SPECIALIZATION"
  
  # Update status
  sed -i 's/"status": "initialized"/"status": "executing"/g' "$BUILD_DIR/agent-info.json"
  
  # Get tasks from config
  local tasks_key="config_specializations_${SPECIALIZATION}_tasks"
  local tasks_array=$(eval echo \${!tasks_key[@]})
  
  if [ -z "$tasks_array" ]; then
    log "No tasks defined for specialization $SPECIALIZATION"
    return 0
  fi
  
  # Execute each task
  local task_count=0
  for task_key in $tasks_array; do
    task_count=$((task_count + 1))
    local task_value=$(eval echo \${$task_key})
    
    log "Executing task $task_count: $task_value"
    eval "$task_value" || {
      log "Task failed: $task_value"
      sed -i 's/"status": "executing"/"status": "failed"/g' "$BUILD_DIR/agent-info.json"
      echo "ERROR: Task '$task_value' failed for agent $AGENT_ID" >> "$LOG_FILE"
      return 1
    }
  done
  
  # Update status
  sed -i 's/"status": "executing"/"status": "completed"/g' "$BUILD_DIR/agent-info.json"
  
  log "All tasks completed successfully"
}

# Function to collect artifacts
collect_artifacts() {
  log "Collecting artifacts for specialization: $SPECIALIZATION"
  
  # Get artifacts from config
  local artifacts_key="config_specializations_${SPECIALIZATION}_artifacts"
  local artifacts_array=$(eval echo \${!artifacts_key[@]})
  
  if [ -z "$artifacts_array" ]; then
    log "No artifacts defined for specialization $SPECIALIZATION"
    return 0
  fi
  
  # Create artifacts directory
  mkdir -p "$BUILD_DIR/artifacts"
  
  # Collect each artifact
  local artifact_count=0
  for artifact_key in $artifacts_array; do
    artifact_count=$((artifact_count + 1))
    local artifact_path=$(eval echo \${$artifact_key})
    
    log "Collecting artifact $artifact_count: $artifact_path"
    
    if [ -e "$artifact_path" ]; then
      # Copy artifact to artifacts directory
      cp -r "$artifact_path" "$BUILD_DIR/artifacts/"
      log "Artifact collected: $artifact_path"
    else
      log "Warning: Artifact not found: $artifact_path"
      echo "WARNING: Artifact '$artifact_path' not found for agent $AGENT_ID" >> "$LOG_FILE"
    fi
  done
  
  log "All artifacts collected"
}

# Function to coordinate with other agents
coordinate_with_team() {
  log "Coordinating with other team members..."
  
  # Create coordination file
  echo "$AGENT_ID:$SPECIALIZATION:completed" > "$BUILD_DIR/coordination.txt"
  
  # Wait for dependencies if any
  local deps_key="config_specializations_${SPECIALIZATION}_dependencies"
  local deps_array=$(eval echo \${!deps_key[@]})
  
  if [ -n "$deps_array" ]; then
    log "Waiting for dependencies: $deps_array"
    
    for dep_key in $deps_array; do
      local dep_value=$(eval echo \${$dep_key})
      log "Waiting for dependency: $dep_value"
      
      # Find agent with this specialization
      local dep_agent=""
      for i in $(seq 1 $(eval echo \${config_team_size})); do
        if [ -f "build/ninja-$i/agent-info.json" ] && grep -q "\"specialization\": \"$dep_value\"" "build/ninja-$i/agent-info.json"; then
          dep_agent=$i
          break
        fi
      done
      
      if [ -z "$dep_agent" ]; then
        log "Warning: No agent found with specialization $dep_value"
        echo "WARNING: No agent found with specialization '$dep_value' for agent $AGENT_ID" >> "$LOG_FILE"
        continue
      fi
      
      # Wait for dependency to complete
      while ! grep -q "$dep_agent:$dep_value:completed" "build/ninja-$dep_agent/coordination.txt" 2>/dev/null; do
        log "Waiting for dependency $dep_value (agent $dep_agent)..."
        sleep 5
      done
      
      log "Dependency $dep_value satisfied by agent $dep_agent"
    done
  fi
  
  log "Coordination complete"
}

# Main execution
main() {
  log "Starting ninja agent $AGENT_ID with specialization $SPECIALIZATION"
  initialize_agent
  coordinate_with_team
  execute_tasks
  collect_artifacts
  log "Ninja agent $AGENT_ID completed"
}

main "$@"
