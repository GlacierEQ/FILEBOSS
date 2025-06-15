<template>
  <div class="p-tab p-tab-brains">
    <v-container v-if="results && results.available" fluid class="pa-0">
      <!-- Loading Spinner -->
      <v-progress-circular
        v-if="loading"
        indeterminate
        color="primary"
        class="ma-4"
      ></v-progress-circular>

      <!-- Aesthetic Score -->
      <v-card class="mb-4">
        <v-card-title class="primary--text">
          <v-icon left>mdi-star</v-icon>
          {{ $gettext('Aesthetic Analysis') }}
        </v-card-title>

        <v-card-text>
          <div class="mb-3">
            <v-row>
              <v-col cols="12" md="6">
                <div class="aesthetic-score-wrapper">
                  <div class="aesthetic-score">
                    {{ results.aesthetic.score.toFixed(1) }}
                  </div>
                  <div class="aesthetic-score-label">
                    {{ $gettext('Overall Score') }}
                  </div>
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-title>{{ $gettext('Composition') }}</v-list-item-title>
                    <v-rating
                      :value="results.aesthetic.composition / 2"
                      color="amber"
                      background-color="grey darken-1"
                      empty-icon="mdi-circle-outline"
                      half-increments
                      dense
                      readonly
                    ></v-rating>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-title>{{ $gettext('Contrast') }}</v-list-item-title>
                    <v-rating
                      :value="results.aesthetic.contrast / 2"
                      color="amber"
                      background-color="grey darken-1"
                      empty-icon="mdi-circle-outline"
                      half-increments
                      dense
                      readonly
                    ></v-rating>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-title>{{ $gettext('Exposure') }}</v-list-item-title>
                    <v-rating
                      :value="results.aesthetic.exposure / 2"
                      color="amber"
                      background-color="grey darken-1"
                      empty-icon="mdi-circle-outline"
                      half-increments
                      dense
                      readonly
                    ></v-rating>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-title>{{ $gettext('Color Harmony') }}</v-list-item-title>
                    <v-rating
                      :value="results.aesthetic.color_harmony / 2"
                      color="amber"
                      background-color="grey darken-1"
                      empty-icon="mdi-circle-outline"
                      half-increments
                      dense
                      readonly
                    ></v-rating>
                  </v-list-item-content>
                </v-list-item>
              </v-col>
            </v-row>
          </div>
        </v-card-text>
      </v-card>

      <!-- Scene Analysis -->
      <v-card class="mb-4">
        <v-card-title class="primary--text">
          <v-icon left>mdi-image-filter-hdr</v-icon>
          {{ $gettext('Scene Analysis') }}
        </v-card-title>

        <v-card-text>
          <v-row>
            <v-col cols="12" sm="6" md="3">
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title class="subtitle-2">{{ $gettext('Scene Type') }}</v-list-item-title>
                  <v-list-item-subtitle>{{ results.scene.scene_type }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-col>

            <v-col cols="12" sm="6" md="3">
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title class="subtitle-2">{{ $gettext('Setting') }}</v-list-item-title>
                  <v-list-item-subtitle>{{ results.scene.indoor_outdoor }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-col>

            <v-col cols="12" sm="6" md="3">
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title class="subtitle-2">{{ $gettext('Time of Day') }}</v-list-item-title>
                  <v-list-item-subtitle>{{ results.scene.time_of_day }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-col>

            <v-col cols="12" sm="6" md="3">
              <v-list-item>
                <v-list-item-content>
                  <v-list-item-title class="subtitle-2">{{ $gettext('Weather') }}</v-list-item-title>
                  <v-list-item-subtitle>{{ results.scene.weather || 'Unknown' }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-col>
          </v-row>

          <v-divider class="my-4"></v-divider>
          
          <!-- Keywords -->
          <div v-if="results.scene.keywords && results.scene.keywords.length">
            <h3 class="subtitle-1 mb-2">{{ $gettext('Keywords') }}</h3>
            <v-chip-group>
              <v-chip 
                v-for="(keyword, i) in results.scene.keywords" 
                :key="i"
                small
                class="ma-1"
                @click="search('keyword:' + keyword)"
              >
                {{ keyword }}
              </v-chip>
            </v-chip-group>
          </div>

          <!-- Emotions -->
          <div v-if="results.scene.emotions && Object.keys(results.scene.emotions).length" class="mt-4">
            <h3 class="subtitle-1 mb-2">{{ $gettext('Emotional Tone') }}</h3>
            <v-row>
              <v-col 
                v-for="(value, emotion) in results.scene.emotions" 
                :key="emotion"
                cols="6"
                sm="4"
                md="3"
                lg="2"
              >
                <v-tooltip bottom>
                  <template v-slot:activator="{ on, attrs }">
                    <div v-bind="attrs" v-on="on">
                      <v-progress-linear
                        :value="value * 100"
                        height="20"
                        rounded
                        :color="getEmotionColor(emotion)"
                      >
                        <span style="color: white">{{ emotion }}</span>
                      </v-progress-linear>
                    </div>
                  </template>
                  <span>{{ emotion }}: {{ (value * 100).toFixed(1) }}%</span>
                </v-tooltip>
              </v-col>
            </v-row>
          </div>
        </v-card-text>
      </v-card>

      <!-- Object Detection -->
      <v-card>
        <v-card-title class="primary--text">
          <v-icon left>mdi-shape</v-icon>
          {{ $gettext('Object Detection') }}
        </v-card-title>

        <v-card-text v-if="results.objects && results.objects.length">
          <div class="object-container">
            <div class="photo-preview" :style="{ position: 'relative' }">
              <img 
                :src="photo.thumbnailUrl('fit_720')" 
                class="object-detection-image" 
                alt="Preview"
              >
              <div
                v-for="(object, i) in results.objects"
                :key="i"
                class="object-box"
                :style="{
                  left: `${object.x}px`,
                  top: `${object.y}px`,
                  width: `${object.width}px`,
                  height: `${object.height}px`,
                  borderColor: getObjectColor(object.label)
                }"
              >
                <div class="object-label" :style="{ backgroundColor: getObjectColor(object.label) }">
                  {{ object.label }} ({{ (object.confidence * 100).toFixed(0) }}%)
                </div>
              </div>
            </div>
          </div>

          <div class="mt-4">
            <v-chip-group>
              <v-chip 
                v-for="(object, i) in uniqueObjects" 
                :key="i"
                small
                class="ma-1"
                :color="getObjectColor(object)"
                text-color="white"
                @click="search('object:' + object)"
              >
                {{ object }}
              </v-chip>
            </v-chip-group>
          </div>
        </v-card-text>
        <v-card-text v-else>
          {{ $gettext('No objects detected') }}
        </v-card-text>
      </v-card>

      <div class="text-center text-caption mt-3 grey--text">
        {{ $gettext('Processed') }}: {{ formatDate(results.processed_at) }}
      </div>
    </v-container>
    
    <v-container v-else-if="!loading" fluid class="pa-0">
      <v-alert
        type="info"
        outlined
      >
        {{ $gettext('No BRAINS analysis available for this photo') }}
        <div class="mt-2">
          <v-btn 
            small 
            color="primary" 
            @click="analyzePhoto"
            :loading="processing"
          >
            {{ $gettext('Analyze Now') }}
          </v-btn>
        </div>
      </v-alert>
    </v-container>
  </div>
</template>

<script>
export default {
  name: 'PhotoBrainsPanel',
  
  props: {
    photo: Object,
    uid: String,
  },
  
  data() {
    return {
      loading: false,
      processing: false,
      results: null,
      emotionColors: {
        happy: 'green',
        peaceful: 'blue',
        awe: 'purple',
        sad: 'blue-grey',
        angry: 'red',
        fearful: 'orange',
        neutral: 'grey',
      },
      objectColors: {
        person: '#FF5722',
        car: '#2196F3',
        building: '#9C27B0',
        tree: '#4CAF50',
        default: '#FFC107',
      },
    };
  },
  
  computed: {
    uniqueObjects() {
      if (!this.results || !this.results.objects) return [];
      
      // Extract unique object labels
      const uniqueLabels = [];
      const seen = new Set();
      
      for (const obj of this.results.objects) {
        if (!seen.has(obj.label)) {
          seen.add(obj.label);
          uniqueLabels.push(obj.label);
        }
      }
      
      return uniqueLabels;
    },
  },
  
  watch: {
    uid: {
      handler: function(newVal) {
        if (newVal) {
          this.fetchResults();
        } else {
          this.results = null;
        }
      },
      immediate: true,
    },
  },
  
  methods: {
    fetchResults() {
      if (!this.uid) return;
      
      this.loading = true;
      
      this.$api.get(`brains/${this.uid}`).then(response => {
        this.results = response.data;
      }).catch(error => {
        console.error('Error fetching BRAINS results:', error);
        this.results = null;
      }).finally(() => {
        this.loading = false;
      });
    },
    
    analyzePhoto() {
      if (!this.uid) return;
      
      this.processing = true;
      
      this.$api.post('brains/analyze', {
        photo_id: this.uid,
        type: 'all',
      }).then(() => {
        this.$notify.success(this.$gettext('Analysis started'));
        
        // Poll for results after a delay
        setTimeout(() => {
          this.fetchResults();
          this.processing = false;
        }, 5000);
      }).catch(error => {
        console.error('Error starting analysis:', error);
        this.$notify.error(this.$gettext('Analysis failed'));
        this.processing = false;
      });
    },
    
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString();
    },
    
    search(query) {
      this.$router.push({ path: '/library/browse', query: { q: query }});
    },
    
    getEmotionColor(emotion) {
      return this.emotionColors[emotion.toLowerCase()] || 'grey';
    },
    
    getObjectColor(label) {
      return this.objectColors[label.toLowerCase()] || this.objectColors.default;
    },
  },
};
</script>

<style lang="scss" scoped>
.p-tab-brains {
  padding: 16px;
  
  .aesthetic-score-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
  }
  
  .aesthetic-score {
    font-size: 72px;
    font-weight: 300;
    line-height: 1;
    color: var(--v-primary-base);
  }
  
  .aesthetic-score-label {
    font-size: 14px;
    color: var(--v-accent-base);
    margin-top: 8px;
  }
  
  .object-container {
    position: relative;
    width: 100%;
    overflow: hidden;
    
    .object-detection-image {
      max-width: 100%;
      height: auto;
    }
    
    .object-box {
      position: absolute;
      border: 2px solid;
      border-radius: 4px;
      
      .object-label {
        position: absolute;
        top: -20px;
        left: -2px;
        padding: 0 4px;
        border-radius: 4px 4px 0 0;
        color: white;
        font-size: 10px;
        white-space: nowrap;
      }
    }
  }
}
</style>
