# PhotoPrism Dockerfile with BRAINS integration
FROM photoprism/photoprism:latest

# Install BRAINS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    libtensorflow2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Environment variables for BRAINS
ENV PHOTOPRISM_EXPERIMENTAL=true \
    PHOTOPRISM_BRAINS=true \
    PHOTOPRISM_BRAINS_OBJECT_DETECTION=true \
    PHOTOPRISM_BRAINS_AESTHETIC_SCORING=true \
    PHOTOPRISM_BRAINS_SCENE_UNDERSTANDING=true

# Create directory for BRAINS models
RUN mkdir -p /photoprism/assets/brains

# Download BRAINS models during build process
COPY scripts/download-brains.sh /photoprism/scripts/download-brains.sh
RUN chmod +x /photoprism/scripts/download-brains.sh && \
    cd /photoprism && \
    ./scripts/download-brains.sh

# Add healthcheck with BRAINS support
HEALTHCHECK --interval=60s --timeout=15s --start-period=90s --retries=3 \
    CMD wget -q --spider http://localhost:2342/api/v1/brains/status || exit 1
