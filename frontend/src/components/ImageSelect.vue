<template>
  <div class="image-adjustment-container">
    <div ref="container" class="canvas-container"></div>
    <q-btn label="Reset Selection" @click="resetSelection" />
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps, watch } from "vue";
import Konva from "konva";

const props = defineProps({
  mask_update_event: {
    type: String,
    required: true,
  },
  image_base64_str: {
    type: String,
    required: true,
  },
  socket: {
    type: Object,
    required: true,
  },
});

const container = ref(null);
const selectionLayer = ref(null);
const imageLayer = ref(null);
const konvaImage = ref(null);
const stage = ref(null);

onMounted(() => {
  const containerEl = container.value;
  const width = containerEl.clientWidth;
  const height = containerEl.clientHeight;

  stage.value = new Konva.Stage({
    container: container.value,
    width: width,
    height: width,
    background: "red",
  });

  imageLayer.value = new Konva.Layer();
  selectionLayer.value = new Konva.Layer();
  stage.value.add(imageLayer.value);
  stage.value.add(selectionLayer.value);

  let selection = null;
  let isDrawing = false;

  stage.value.on("mousedown", (e) => {
    isDrawing = true;
    const pos = stage.value.getPointerPosition();
    selection = new Konva.Rect({
      x: pos.x,
      y: pos.y,
      width: 0,
      height: 0,
      stroke: "red",
      strokeWidth: 2,
      fill: "rgba(255, 0, 0, 0.2)",
    });
    selectionLayer.value.add(selection);
  });

  stage.value.on("mousemove", (e) => {
    if (!isDrawing) return;
    const pos = stage.value.getPointerPosition();
    selection.width(pos.x - selection.x());
    selection.height(pos.y - selection.y());
    selectionLayer.value.batchDraw();
  });

  stage.value.on("mouseup", (e) => {
    isDrawing = false;
    if (!selection) return;
    selectionLayer.value.batchDraw();
    generateAndUpdateMask();
  });

  const handleResize = () => {
    if (konvaImage.value) {
      const newWidth = containerEl.clientWidth;
      const newHeight = containerEl.clientHeight;
      stage.value.width(newWidth);
      stage.value.height(newWidth);
      konvaImage.value.x(0);
      konvaImage.value.y(0);
      konvaImage.value.height(newWidth - 1);
      konvaImage.value.width(newWidth - 1);
      stage.value.draw();
      konvaImage.value.cache();
    }
  };

  const loadImage = (imageBase64Str) => {
    const imageObj = new Image();
    imageObj.src = `data:image/png;base64,${imageBase64Str}`;

    imageObj.onload = () => {
      konvaImage.value = new Konva.Image({
        image: imageObj,
      });
      imageLayer.value.removeChildren();
      imageLayer.value.add(konvaImage.value);
      handleResize();
      imageLayer.value.draw();
    };
  };

  watch(
    () => props.image_base64_str,
    (newImageBase64Str) => {
      loadImage(newImageBase64Str);
    }
  );

  window.addEventListener("resize", handleResize);

  loadImage(props.image_base64_str);
});

const generateAndUpdateMask = () => {
  const newMask = generateBinaryMask();
  props.socket.emit(props.mask_update_event, {
    mask: newMask,
  });
};

const generateBinaryMask = () => {
  const width = selectionLayer.value.getWidth();
  const height = selectionLayer.value.getHeight();
  const mask = Array.from({ length: height }, () => Array(width).fill(0));

  selectionLayer.value.getChildren().forEach((selection) => {
    const x = Math.floor(selection.x());
    const y = Math.floor(selection.y());
    const w = Math.floor(selection.width());
    const h = Math.floor(selection.height());

    for (let i = y; i < y + h; i++) {
      for (let j = x; j < x + w; j++) {
        if (i < height && j < width) {
          mask[i][j] = 1;
        }
      }
    }
  });

  return mask;
};

const resetSelection = () => {
  if (selectionLayer.value) {
    selectionLayer.value.removeChildren();
    selectionLayer.value.draw();
    generateAndUpdateMask();
  }
};

defineExpose({
  resetSelection,
});
</script>

<style scoped>
.image-adjustment-container {
  display: flex;
  flex-direction: column;
  height: auto;
  /* border: 1px solid #ffffff; */
}

.canvas-container {
  height: 512px;
  width: 512px;
  /* display: flex; */
  justify-content: center;
  align-items: center;
  border: 1px solid #ffffff;
}

.sliders-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
}
</style>
