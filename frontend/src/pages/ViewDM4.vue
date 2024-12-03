<template>
  <q-page class="q-pa-md">
    <q-btn class="full-width q-mb-md" color="secondary" @click="openFile">
      <span v-if="selectedFile">Selected File: {{ selectedFile }}</span>
      <span v-else>Open File</span>
    </q-btn>
    <div class="row q-col-gutter-md" style="height: 80vh">
      <!-- Left sidebar for sliders -->
      <div class="col-3" style="height: 100%; overflow-y: auto">
        <q-list bordered separator class="full-height">
          <!-- Left Image Sliders -->
          <div class="text-h6">Left Image</div>
          <q-item>
            <q-item-section>
              <q-item-label overline>Gamma</q-item-label>
              <q-slider
                v-model="leftGamma"
                :min="0.1"
                :max="2.5"
                :step="0.05"
                @update:model-value="ajustLeftImage"
              />
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label overline>Contrast</q-item-label>
              <q-slider
                v-model="leftContrast"
                :min="0"
                :max="5"
                :step="0.1"
                @update:model-value="ajustLeftImage"
              />
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label overline>Brightness</q-item-label>
              <q-slider
                v-model="leftBrightness"
                :min="0"
                :max="1"
                :step="0.01"
                @update:model-value="ajustLeftImage"
              />
            </q-item-section>
          </q-item>

          <!-- Right Image Sliders -->
          <div class="text-h6">Right Image</div>
          <q-item>
            <q-item-section>
              <q-item-label overline>Image Index</q-item-label>
              <q-slider
                v-model="rightImageIndex"
                :min="0"
                :max="indexRange"
                @update:model-value="changeRightImage"
              />
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label overline>Gamma</q-item-label>
              <q-slider
                v-model="rightGamma"
                :min="0.1"
                :max="2.5"
                :step="0.05"
                @update:model-value="ajustRightImage"
              />
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label overline>Contrast</q-item-label>
              <q-slider
                v-model="rightContrast"
                :min="0"
                :max="5"
                :step="0.1"
                @update:model-value="ajustRightImage"
              />
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label overline>Brightness</q-item-label>
              <q-slider
                v-model="rightBrightness"
                :min="0"
                :max="1"
                :step="0.01"
                @update:model-value="ajustRightImage"
              />
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label overline>Log Scale</q-item-label>
              <q-toggle
                v-model="log_scale"
                @update:model-value="ajustRightImage"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </div>

      <!-- Right part for image display -->
      <div class="col-9" style="height: 80vh">
        <div class="flex row">
          <q-card class="full-height flex flex-center col-6">
            <ImageSelect
              :mask_update_event="update_bin_mask"
              :image_base64_str="LeftimageData"
              :socket="socket"
            />
          </q-card>
          <q-card class="full-height flex flex-center col-6">
            <ImageSelect
              :mask_update_event="update_virtual_mask"
              :image_base64_str="RightimageData"
              :socket="socket"
            />
          </q-card>
        </div>
        <div class="q-mt-md">
          <q-scroll-area style="height: calc(80vh - 250px)">
            <div class="row">
              <div
                v-for="(image, index) in imageSeries"
                :key="index"
                class="q-mb-md col-4"
              >
                <q-img
                  :src="`data:image/png;base64,${image}`"
                  style="max-width: 100%; max-height: 100%"
                />
              </div>
            </div>
          </q-scroll-area>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { socketViewer, socketRDF } from "boot/socketio";
import { useQuasar } from "quasar";
import ImageSelect from "components/ImageSelect.vue";

// 定义响应式数据
const selectedFile = ref(null);
const $q = useQuasar();
const LeftimageData = ref(null);
const RightimageData = ref(null);
const leftGamma = ref(1);
const leftContrast = ref(1);
const leftBrightness = ref(0);
const rightGamma = ref(1);
const rightContrast = ref(1);
const rightBrightness = ref(0);
const rightImageIndex = ref(0);
const indexRange = ref(0);
const update_bin_mask = "update_bin_mask";
const update_virtual_mask = "update_virtual_mask";
const socket = socketViewer;
const log_scale = ref(false);
const imageSeries = ref([]);

const openFile = async () => {
  const filePaths = await window.myAPI.openFileDialog();
  if (filePaths && filePaths.length > 0) {
    selectedFile.value = filePaths[0];
    console.log(selectedFile.value);
    $q.loading.show();
    socket.emit("upload_dm4", selectedFile.value);
  } else {
    selectedFile.value = null;
  }
};

const ajustLeftImage = () => {
  socket.emit("update_adjust_params", {
    gamma: leftGamma.value,
    contrast: leftContrast.value,
    brightness: leftBrightness.value,
    log_scale: log_scale.value,
    side: "left",
  });
  socket.emit("request_image", { side: "left" });
};

const ajustRightImage = () => {
  socket.emit("update_adjust_params", {
    gamma: rightGamma.value,
    contrast: rightContrast.value,
    brightness: rightBrightness.value,
    log_scale: log_scale.value,
    side: "right",
  });
  socket.emit("request_image", { side: "right" });
};

const changeRightImage = () => {
  socket.emit("set_index", {
    index: rightImageIndex.value,
  });
};

onMounted(() => {
  socket.on("right_image_response", (data) => {
    if (data.error) {
      console.error(data.error);
    } else {
      console.log("Image Response Received");
      RightimageData.value = data.image_data;
    }
  });
  socket.on("left_image_response", (data) => {
    if (data.error) {
      console.error(data.error);
    } else {
      console.log("Image Response Received");
      LeftimageData.value = data.image_data;
    }
  });

  socket.on("file_name_response", (data) => {
    console.log(data);
    if (data.success) {
      $q.loading.hide();
      $q.notify({
        message: "DM4 Successfully Loaded",
        color: "primary",
        icon: "cloud_done",
        position: "center",
        timeout: 1000,
      });
      indexRange.value = data.index_range - 1;
      socket.emit("set_index", rightImageIndex.value);
      socketRDF.emit("load_image_rdf", true);
    }
  });

  socket.on("image_series_response", (data) => {
    if (data.error) {
      console.error(data.error);
    } else {
      console.log("Image Series Response Received");
      imageSeries.value = data.image_series;
    }
  });
});
</script>

<style scoped>
.stage-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.stage-container {
  width: 100%;
  height: 100%;
}
.q-gallery {
  display: flex;
  flex-direction: row;
  overflow-x: auto;
}

.q-gallery-slide {
  padding: 10px;
}
</style>
