<template>
  <div>
    <img :src="imageSrc" alt="Random Image" v-if="imageSrc" />
    <button @click="requestImage">Request Image</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { socket } from "boot/socketio";

const imageSrc = ref(null);

function requestImage() {
  socket.emit("request_image", 0);
}

onMounted(() => {
  socket.on("image_response", (data) => {
    if (data.error) {
      console.error(data.error);
    } else {
      imageSrc.value = `data:image/jpeg;base64,${data.image_data}`;
    }
  });
});
</script>
