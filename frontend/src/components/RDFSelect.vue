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
  isDrawingEnabled: {
    type: Boolean,
    default: true, // 默认启用绘制功能
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
  let isDragging = false;
  let color = null;

  generateAndUpdateMask();

  stage.value.on("mousedown", (e) => {
    if (!props.isDrawingEnabled) return; // 如果禁用绘制功能，则直接返回
    const pos = stage.value.getPointerPosition();
    if (e.evt.shiftKey) {
      const shape = selectionLayer.value.getIntersection(pos);
      if (shape) {
        shape.remove();
        generateAndUpdateMask();
      }
    } else {
      // Normal drawing
      selectionLayer.value.removeChildren();
      isDrawing = true;
      color = getRandomColor();
      selection = new Konva.Rect({
        x: pos.x,
        y: pos.y,
        width: 0,
        height: 0,
        stroke: color,
        strokeWidth: 2,
        fill: color + "33",
      });
      selectionLayer.value.add(selection);
    }
  });

  stage.value.on("mousemove", (e) => {
    if (!props.isDrawingEnabled || !isDrawing) return; // 如果禁用绘制功能，则直接返回
    isDragging = true;
    const pos = stage.value.getPointerPosition();
    selection.width(pos.x - selection.x());
    selection.height(pos.y - selection.y());
    selectionLayer.value.batchDraw();
  });

  stage.value.on("mouseup", (e) => {
    if (!props.isDrawingEnabled || !isDrawing) return; // 如果禁用绘制功能，则直接返回
    if (!selection) return;
    if (!isDragging) {
      const pos = stage.value.getPointerPosition();
      console.log("click", pos);
      handlePixelClick(pos);
      selection.remove();
    }
    selectionLayer.value.batchDraw();
    generateAndUpdateMask();
    isDrawing = false;
    isDragging = false;
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

const handlePixelClick = (pos) => {
  if (!props.isDrawingEnabled) return; // 如果禁用绘制功能，则直接返回
  const color = getRandomColor();
  const selection = new Konva.Circle({
    x: pos.x,
    y: pos.y,
    radius: 3,
    fill: color,
    stroke: color,
  });
  selectionLayer.value.add(selection);
  selectionLayer.value.batchDraw();
};

const generateAndUpdateMask = () => {
  if (!props.isDrawingEnabled) return; // 如果禁用绘制功能，则直接返回
  const newMask = generateBinaryMask();
  props.socket.emit(props.mask_update_event, {
    mask: newMask,
    all_selections: selectionLayer.value.getChildren(),
    width: selectionLayer.value.getWidth(),
    height: selectionLayer.value.getHeight(),
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
  if (!props.isDrawingEnabled) return; // 如果禁用绘制功能，则直接返回
  if (selectionLayer.value) {
    selectionLayer.value.removeChildren();
    selectionLayer.value.draw();
    generateAndUpdateMask();
  }
};

const getRandomColor = () => {
  const letters = "0123456789ABCDEF";
  let color = "#";
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
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
