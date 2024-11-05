<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md" style="height: 80vh">
      <!-- Left sidebar for sliders -->
      <div class="col-3" style="height: 100%; overflow-y: auto">
        <q-list bordered separator class="full-height">
          <!-- Image Index Slider -->
          <q-item>
            <q-item-section>
              <q-item-label overline>Image Index</q-item-label>
              <q-slider v-model="imageIndex" :min="0" :max="indexRange" @update:model-value="changeImage" />
            </q-item-section>
          </q-item>

          <!-- Gamma Slider -->
          <q-item>
            <q-item-section>
              <q-item-label overline>Gamma</q-item-label>
              <q-slider v-model="gamma" :min="0.1" :max="2.5" :step="0.05" @update:model-value="ajustImage" />
            </q-item-section>
          </q-item>

          <!-- Contrast Slider -->
          <q-item>
            <q-item-section>
              <q-item-label overline>Contrast</q-item-label>
              <q-slider v-model="contrast" :min="0" :max="5" :step="0.1" @update:model-value="ajustImage" />
            </q-item-section>
          </q-item>

          <!-- Brightness Slider -->
          <q-item>
            <q-item-section>
              <q-item-label overline>Brightness</q-item-label>
              <q-slider v-model="brightness" :min="0" :max="1" :step="0.01" @update:model-value="ajustImage" />
            </q-item-section>
          </q-item>
        </q-list>
      </div>

      <!-- Right part for image display -->
      <div class="col-4" style="height: 100%">
        <q-card v-show="imageData" class="full-height flex flex-center">
          <h3 class="q-mb-sm">Before central correction</h3>
          <q-card-section>
            <div ref="stageContainer" class="stage-container"></div>
          </q-card-section>
        </q-card>
        <q-card v-show="!imageData" class="full-height flex flex-center">
          <q-card-section class="text-center"> No image loaded </q-card-section>
        </q-card>
      </div>

      <div class="col-4" style="height: 100%">
        <q-card v-show="imageCenterData" class="full-height flex flex-center">
          <h3 class="q-mb-sm">After central correction</h3>
          <q-card-section>
            <div ref="stageContainer2" class="stage-container"></div>
          </q-card-section>
        </q-card>
        <q-card v-show="!imageCenterData" class="full-height flex flex-center">
          <q-card-section class="text-center"> No image loaded </q-card-section>
        </q-card>
      </div>

    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useQuasar } from "quasar";
import Konva from "konva";
import { socketCenCal } from 'boot/socketio'

const socket = socketCenCal;
// 定义响应式数据
const selectedFile = ref(null);
const $q = useQuasar();
const imageData = ref(null);
const imageCenterData = ref(null)
const imageShape = ref(null);
const gamma = ref(1);
const contrast = ref(1);
const brightness = ref(0);
const imageIndex = ref(0);
const indexRange = ref(0);

const stageContainer = ref(null);
const stageContainer2 = ref(null);
const layer1 = ref(null);
const layer2 = ref(null);

const ajustImage = () => {
  socket.emit("update_adjust_params", {
    gamma: gamma.value,
    contrast: contrast.value,
    brightness: brightness.value,
  });
  socket.emit("request_image", imageIndex.value);
  socket.emit("request_calibrated_image", {  // 请求校准后的图片
    index: imageIndex.value,
    threshold: 0.5,
  });
};

const changeImage = () => {
  socket.emit("request_image", imageIndex.value);
  socket.emit("request_calibrated_image", {  // 请求校准后的图片
    index: imageIndex.value,
    threshold: 0.5,
  });
};

// 定义绘制图像的函数
const drawImage = (base64Image, layer) => {
  const img = new Image();
  img.src = "data:image/png;base64," + base64Image;

  img.onload = () => {
    const konvaImage = new Konva.Image({
      image: img,
      width: layer.getStage().width(),  // 使用整个画布宽度
      height: layer.getStage().height(),
      x: 0,
      y: 0,
    });

    layer.destroyChildren();  // 清除图层上的旧内容
    layer.add(konvaImage);  // 添加新图片
    layer.batchDraw();  // 更新画布
  };

  img.onerror = (error) => {
    console.error("Failed to load image:", error);
  };
};


onMounted(() => {
  // 初始化第一张图片的 Stage 和 Layer
  const stage1 = new Konva.Stage({
    container: stageContainer.value,
    width: 512,
    height: 512,
  });

  layer1.value = new Konva.Layer();
  stage1.add(layer1.value);

  // 初始化第二张图片的 Stage 和 Layer
  const stage2 = new Konva.Stage({
    container: stageContainer2.value,
    width: 512,
    height: 512,
  });

  layer2.value = new Konva.Layer();
  stage2.add(layer2.value);

  // 获取之前上传过的图片索引范围
  socket.emit("get_range");
  socket.on("get_range_response", (data) => {
    if (data.error) {
      console.error(data.error);
    } else {
      indexRange.value = data.index_range - 1;
    }
  });

  // 监听服务器的图片响应
  socket.on("image_response", (data) => {
    if (data.error) {
      console.error(data.error);
      return;
    }
    if (data.id2 === "after") {
      imageCenterData.value = data.image_data;
      drawImage(imageCenterData.value, layer2.value); // 绘制第二张图片
    } else {
      imageData.value = data.image_data;
      imageShape.value = data.shape;
      drawImage(imageData.value, layer1.value); // 绘制第一张图片
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
  width: 60%;
  height: 100%;
}
</style>
