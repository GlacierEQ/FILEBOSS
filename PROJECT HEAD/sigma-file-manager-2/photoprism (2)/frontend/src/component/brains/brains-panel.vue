<template>
  <div class="brains-panel">
    <v-card flat class="pa-2">
      <v-card-title primary-title>
        <div>
          <h3 class="headline mb-0">BRAINS Neural System</h3>
          <div class="pt-3">Advanced AI-powered photo analysis</div>
        </div>
      </v-card-title>
      
      <v-card-text>
        <v-alert
          v-if="!config.brains"
          type="warning"
          outlined
          prominent
          class="mt-4"
        >
          BRAINS is currently disabled. Enable it in your configuration to use advanced neural analysis.
        </v-alert>
        
        <v-alert
          v-if="config.brains && !modelsDownloaded"
          type="info"
          outlined
          prominent
          class="mt-4"
        >
          BRAINS models are not downloaded yet. Click the button below to download them.
        </v-alert>
        
        <v-row v-if="config.brains && modelsDownloaded" class="mt-4">
          <v-col cols="12" md="4">
            <v-card outlined>
              <v-card-title>Object Detection</v-card-title>
              <v-card-text>
                <v-switch
                  v-model="capabilities.object_detection"
                  :label="capabilities.object_detection ? 'Enabled' : 'Disabled'"
                  :disabled="!config.brains"
                  @change="saveCapabilities"
                ></v-switch>
                <div class="pt-2">
                  Recognizes objects in photos with higher precision than standard detection.
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          
          <v-col cols="12" md="4">
            <v-card outlined>
              <v-card-title>Aesthetic Analysis</v-card-title>
              <v-card-text>
                <v-switch
                  v-model="capabilities.aesthetic_scoring"
                  :label="capabilities.aesthetic_scoring ? 'Enabled' : 'Disabled'"
                  :disabled="!config.brains"
                  @change="saveCapabilities"
                ></v-switch>
                <div class="pt-2">
                  Scores photos based on composition, exposure, color harmony, and more.
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          
          <v-col cols="12" md="4">
            <v-card outlined>
              <v-card-title>Scene Understanding</v-card-title>
              <v-card-text>
                <v-switch
                  v-model="capabilities.scene_understanding"
                  :label="capabilities.scene_understanding ? 'Enabled' : 'Disabled'"
                  :disabled="!config.brains"
                  @change="saveCapabilities"
                ></v-switch>
                <div class="pt-2">
                  Analyzes scenes for context, mood, and deeper semantic meaning.
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card outlined class="brains-actions">
              <v-card-title>BRAINS Actions</v-card-title>
              <v-card-text>
                <v-btn
                  color="primary"
                  :loading="loading.download"
                  :disabled="loading.download || !config.brains"
                  @click="downloadModels"
                >
                  <v-icon left>mdi-download</v-icon>
                  Download Models
                </v-btn>
                
                <v-btn
                  color="info"
                  class="ml-4"
                  :loading="loading.analyze"
                  :disabled="loading.analyze || !config.brains || !modelsDownloaded"
                  @click="showAnalyzeDialog"
                >
                  <v-icon left>mdi-brain</v-icon>
                  Analyze Photos
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <!-- Analysis Dialog -->
    <v-dialog v-model="dialogs.analyze" max-width="600px">
      <v-card>
        <v-card-title>BRAINS Photo Analysis</v-card-title>
        <v-card-text>
          <v-select
            v-model="analyzeOptions.type"
            :items="analyzeTypes"
            label="Analysis Type"
          ></v-select>
          
          <v-select
            v-model="analyzeOptions.scope"
            :items="analyzeScopes"
            label="Scope"
          ></v-select>
          
          <v-checkbox
            v-model="analyzeOptions.force"
            label="Re-analyze already processed photos"
          ></v-checkbox>
          
          <v-alert
            v-if="analyzeOptions.scope === 'all'"
            type="warning"
            outlined
            text
          >
            This will analyze all photos in your library and may take a long time.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="grey darken-1"
            text
            @click="dialogs.analyze = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            :disabled="loading.analyze"
            @click="analyzePhotos"
          >
            Start Analysis
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
export default {
  name: 'BrainsPanel',
  data() {
    return {
      loading: {
        download: false,
        analyze: false,
      },
      dialogs: {
        analyze: false,
      },
      capabilities: {
        object_detection: true,
        aesthetic_scoring: true,
        scene_understanding: true,
      },
      modelsDownloaded: false,
      analyzeOptions: {
        type: 'all',
        scope: 'recent',
        force: false,
      },
      analyzeTypes: [
        { text: 'All Capabilities', value: 'all' },
        { text: 'Object Detection Only', value: 'object' },
        { text: 'Aesthetic Scoring Only', value: 'aesthetic' },
        { text: 'Scene Understanding Only', value: 'scene' },
      ],
      analyzeScopes: [
        { text: 'Recent Photos (last 100)', value: 'recent' },
        { text: 'Selected Photos', value: 'selected' },
        { text: 'All Photos', value: 'all' },
      ],
    };
  },
  
  computed: {
    config() {
      return this.$config.values;
    },
  },
  
  created() {
    this.loadStatus();
  },
  
  methods: {
    loadStatus() {
      this.$api.get('brains/status').then((response) => {
        if (response && response.data) {
          this.modelsDownloaded = response.data.models_downloaded;
          this.capabilities = response.data.capabilities;
        }
      }).catch((error) => {
        this.$notify.error('Failed to load BRAINS status');
        console.error(error);
      });
    },
    
    downloadModels() {
      this.loading.download = true;
      
      this.$api.post('brains/download').then(() => {
        this.modelsDownloaded = true;
        this.$notify.success('BRAINS models downloaded successfully');
      }).catch((error) => {
        this.$notify.error('Failed to download BRAINS models');
        console.error(error);
      }).finally(() => {
        this.loading.download = false;
      });
    },
    
    saveCapabilities() {
      this.$api.post('brains/capabilities', this.capabilities).then(() => {
        this.$notify.success('BRAINS capabilities updated');
      }).catch((error) => {
        this.$notify.error('Failed to update BRAINS capabilities');
        console.error(error);
      });
    },
    
    showAnalyzeDialog() {
      this.dialogs.analyze = true;
    },
    
    analyzePhotos() {
      this.loading.analyze = true;
      this.dialogs.analyze = false;
      
      const params = {
        type: this.analyzeOptions.type,
        scope: this.analyzeOptions.scope,
        force: this.analyzeOptions.force,
      };
      
      this.$api.post('brains/analyze', params).then(() => {
        this.$notify.success('BRAINS analysis started');
      }).catch((error) => {
        this.$notify.error('Failed to start BRAINS analysis');
        console.error(error);
      }).finally(() => {
        this.loading.analyze = false;
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.brains-panel {
  max-width: 1200px;
  margin: 0 auto;
}

.brains-actions {
  background-color: rgba(0, 0, 0, 0.01);
}

@media (max-width: 600px) {
  .brains-actions .v-card__text {
    display: flex;
    flex-direction: column;
    
    .v-btn {
      margin-left: 0 !important;
      margin-top: 12px;
    }
  }
}
</style>
