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
          <!-- Image Index Slider -->
          <q-item>
            <q-item-section>
              <q-item-label overline>Image Index</q-item-label>
              <q-slider
                v-model="imageIndex"
                :min="0"
                :max="indexRange"
                @update:model-value="changeImage"
              />
            </q-item-section>
          </q-item>

          <!-- Gamma Slider -->
          <q-item>
            <q-item-section>
              <q-item-label overline>Gamma</q-item-label>
              <q-slider
                v-model="gamma"
                :min="0.1"
                :max="2.5"
                :step="0.05"
                @update:model-value="ajustImage"
              />
            </q-item-section>
          </q-item>

          <!-- Contrast Slider -->
          <q-item>
            <q-item-section>
              <q-item-label overline>Contrast</q-item-label>
              <q-slider
                v-model="contrast"
                :min="0"
                :max="5"
                :step="0.1"
                @update:model-value="ajustImage"
              />
            </q-item-section>
          </q-item>

          <!-- Brightness Slider -->
          <q-item>
            <q-item-section>
              <q-item-label overline>Brightness</q-item-label>
              <q-slider
                v-model="brightness"
                :min="0"
                :max="1"
                :step="0.01"
                @update:model-value="ajustImage"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </div>

      <!-- Right part for image display -->
      <div class="col-9" style="height: 100%">
        <q-card v-show="imageData" class="full-height flex flex-center">
          <q-card-section>
            <div ref="stageContainer" class="stage-container"></div>
          </q-card-section>
        </q-card>
        <q-card v-show="!imageData" class="full-height flex flex-center">
          <q-card-section class="text-center"> No image loaded </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { socket } from "boot/socketio";
import { useQuasar } from "quasar";
import Konva from "konva";

// 定义响应式数据
const selectedFile = ref(null);
const $q = useQuasar();
const imageData = ref(null);
const imageShape = ref(null);
const gamma = ref(1);
const contrast = ref(1);
const brightness = ref(0);
const imageIndex = ref(0);
const indexRange = ref(0);

const stageContainer = ref(null);
const stage = ref(null);
const layer = ref(null);

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

const ajustImage = () => {
  socket.emit("update_adjust_params", {
    gamma: gamma.value,
    contrast: contrast.value,
    brightness: brightness.value,
  });
  socket.emit("request_image", imageIndex.value);
};

const changeImage = () => {
  socket.emit("request_image", imageIndex.value);
};

// 定义绘制图像的函数
const drawImage = () => {
  const img = new Image();
  img.src = "data:image/png;base64," + imageData.value;

  img.onload = () => {
    const konvaImage = new Konva.Image({
      image: img,
      width: stage.value.width(),
      height: stage.value.height(),
    });

    // 清除之前的图像
    layer.value.destroyChildren();
    layer.value.add(konvaImage);
    layer.value.batchDraw();
  };
};

onMounted(() => {
  stage.value = new Konva.Stage({
    container: stageContainer.value,
    width: 512,
    height: 512,
  });

  layer.value = new Konva.Layer();
  stage.value.add(layer.value);

  socket.on("image_response", (data) => {
    if (data.error) {
      console.error(data.error);
    } else {
      console.log("Image Response Received");
      imageData.value = data.image_data;
      imageShape.value = data.shape;
      drawImage();
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
      socket.emit("request_image", imageIndex.value);
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
</style>
