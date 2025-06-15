#!/usr/bin/env bash

TODAY=$(date -u +%Y%m%d)

MODEL_NAME="BRAINS"
MODEL_URL="https://dl.photoprism.app/tensorflow/brains.zip?$TODAY"
MODEL_PATH="assets/brains"
MODEL_ZIP="/tmp/photoprism/brains.zip"
MODEL_HASH="af5e6a2e7c791e52e2a336173e425e7b605a5d1x  $MODEL_ZIP"
MODEL_VERSION="$MODEL_PATH/version.txt"
MODEL_BACKUP="storage/backup/brains-$TODAY"

echo "Installing $MODEL_NAME model for TensorFlow..."

# Create directories and check for success
mkdir -p /tmp/photoprism || { echo "Failed to create /tmp/photoprism"; exit 1; }
mkdir -p storage/backup || { echo "Failed to create storage/backup"; exit 1; }

# Check for update
if [[ -f ${MODEL_ZIP} ]] && [[ $(sha1sum ${MODEL_ZIP}) == "${MODEL_HASH}" ]]; then
  if [[ -f ${MODEL_VERSION} ]]; then
    echo "Already up to date."
    exit
  fi
else
  # Download model
  echo "Downloading latest BRAINS model from $MODEL_URL..."
  wget --inet4-only -c "${MODEL_URL}" -O ${MODEL_ZIP}

  TMP_HASH=$(sha1sum ${MODEL_ZIP})

  echo "${TMP_HASH}"
fi

# Create backup
if [[ -e ${MODEL_PATH} ]]; then
  echo "Creating backup of existing directory: $MODEL_BACKUP"
  rm -rf "${MODEL_BACKUP}"
  mv ${MODEL_PATH} "${MODEL_BACKUP}"
fi

# Unzip model
unzip ${MODEL_ZIP} -d assets
echo "$MODEL_NAME $TODAY $MODEL_HASH" > ${MODEL_VERSION}

# Create subdirectories for different model types
mkdir -p ${MODEL_PATH}/object
mkdir -p ${MODEL_PATH}/aesthetic
mkdir -p ${MODEL_PATH}/scene

echo "Latest $MODEL_NAME neural network models installed."
echo "BRAINS is now ready to enhance your photo analysis!"
