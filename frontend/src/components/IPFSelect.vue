<template>
  <div class="image-adjustment-container">
    <div ref="container" class="canvas-container"></div>
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

  generateAndUpdateMask();

  stage.value.on("mousedown", (e) => {
    const pos = stage.value.getPointerPosition();
    if (e.evt.shiftKey) {
      const shape = selectionLayer.value.getIntersection(pos);
      if (shape) {
        shape.remove();
        generateAndUpdateMask();
      }
    } else {
      // Clear previous selections
      selectionLayer.value.removeChildren();
      // Add new selection
      handlePixelClick(pos);
    }
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
  generateAndUpdateMask();
};

const generateAndUpdateMask = () => {
  const newMask = generateBinaryMask();
  props.socket.emit(props.mask_update_event, {
    // mask: newMask,
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

    if (y < height && x < width) {
      mask[y][x] = 1;
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

const getRandomColor = () => {
  const letters = "F";
  let color = "#";
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return "#000000";
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
}

.canvas-container {
  height: 512px;
  width: 512px;
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
