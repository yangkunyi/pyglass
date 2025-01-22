<template>
  <q-page class="q-pa-md">
    <div class="row">
      <div class="col-2" style="height: 100%; overflow-y: auto">
        <q-card class="full-height column">
          <q-btn class="full-width q-mb-md" color="primary" @click="openData">
            <span v-if="selectedData">Selected Data: {{ selectedData }}</span>
            <span v-else>Import Data</span>
          </q-btn>
          <q-btn
            class="full-width q-mb-md"
            color="primary"
            @click="openResults"
          >
            <span v-if="selectedResults"
              >Selected Results: {{ selectedResults }}</span
            >
            <span v-else>Import Results</span>
          </q-btn>
          <q-btn
            class="full-width q-mb-md"
            color="primary"
            @click="openSimulations"
          >
            <span v-if="selectedSimulations"
              >Selected Simulations: {{ selectedSimulations }}</span
            >
            <span v-else>Import Simulations</span>
          </q-btn>
          <q-select
            filled
            v-model="symmetry"
            :options="symmetry_options"
            label="Symmetry"
          />
          <q-select
            filled
            v-model="direction"
            :options="direction_options"
            label="Projection Direction"
          />
          <q-input
            v-model.number="threshold"
            type="number"
            filled
            label="Threshold"
          />
          <q-list bordered separator class="full-height">
            <!-- Left Image Sliders -->
            <q-item>
              <q-item-section>
                <q-item-label overline>Gamma</q-item-label>
                <q-slider
                  v-model="Gamma"
                  :min="0.1"
                  :max="2.5"
                  :step="0.05"
                  @update:model-value="ajustImage"
                />
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section>
                <q-item-label overline>Contrast</q-item-label>
                <q-slider
                  v-model="Contrast"
                  :min="0"
                  :max="5"
                  :step="0.1"
                  @update:model-value="ajustImage"
                />
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section>
                <q-item-label overline>Brightness</q-item-label>
                <q-slider
                  v-model="Brightness"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  @update:model-value="ajustImage"
                />
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section>
                <q-item-label overline>Log Scale</q-item-label>
                <q-toggle
                  v-model="log_scale"
                  @update:model-value="ajustImage"
                />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>
      <div class="col-10 q-pa-md" style="height: 100%">
        <div class="column justify-center">
          <div class="col-6">
            <IPFSelect
              :mask_update_event="update_virtual_mask"
              :image_base64_str="IPFBase64"
              :socket="socket"
            />
          </div>

          <div class="col-6">
            <div class="row">
              <div class="col-6 col-lg-4">
                <q-img
                  :src="ImageBase64"
                  v-if="ImageBase64"
                  alt="Legend Image"
                  style="max-width: 100%; height: auto"
                />
              </div>
              <div class="col-4 col-lg-4">
                <img
                  :src="legendBase64"
                  v-if="legendBase64"
                  alt="Legend Image"
                  style="max-width: 100%; height: auto"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, watchPostEffect } from "vue";
import { useQuasar } from "quasar";
import { socketXem } from "boot/socketio";
import IPFSelect from "components/IPFSelect.vue";

const Gamma = ref(1);
const Contrast = ref(1);
const Brightness = ref(0);
const log_scale = ref(false);

const ajustImage = () => {
  socket.emit("update_adjust_params", {
    gamma: Gamma.value,
    contrast: Contrast.value,
    brightness: Brightness.value,
    log_scale: log_scale.value,
  });
  socket.emit("request_image", {});
};

const update_virtual_mask = "update_virtual_mask";
const selectedResults = ref(null);
const selectedSimulations = ref(null);
const selectedData = ref(null);
const legendBase64 = ref(null);
const ImageBase64 = ref(null);
const $q = useQuasar();
const socket = socketXem;
const direction = ref(null);
const direction_options = [
  { label: "X", value: "x" },
  { label: "Y", value: "y" },
  { label: "Z", value: "z" },
];
const symmetry = ref(null);
const symmetry_options = [
  { label: "Oh", value: "Oh" },
  { label: "Th", value: "Th" },
  { label: "D6h", value: "D6h" },
  { label: "C6h", value: "C6h" },
  { label: "D4h", value: "D4h" },
  { label: "C4h", value: "C4h" },
  { label: "D3d", value: "D3d" },
  { label: "S6", value: "S6" },
  { label: "D2h", value: "D2h" },
  { label: "C2h", value: "C2h" },
  { label: "Ci", value: "Ci" },
];
const threshold = ref(0.0125);
const IPFBase64 = ref(null);

const openFile = async (fileRef, type) => {
  const filePaths = await window.myAPI.openFileDialog();
  if (filePaths && filePaths.length > 0) {
    fileRef.value = filePaths[0]; // 只取第一个文件路径
    console.log(`${type} selected:`, fileRef.value);
    $q.loading.show();
    const eventMap = {
      results: "load_results",
      simulations: "load_simulations",
      data: "load_data",
    };
    const eventName = eventMap[type];
    socket.emit(eventName, { filePath: fileRef.value, type }); // 传递文件路径和类型标识
  } else {
    fileRef.value = null;
  }
};

const openResults = async () => {
  openFile(selectedResults, "results");
};

const openSimulations = async () => {
  openFile(selectedSimulations, "simulations");
};

const openData = async () => {
  openFile(selectedSimulations, "data");
};

onMounted(() => {
  socket.on("load_data_success", (data) => {
    if (data.success) {
      $q.loading.hide();
      $q.notify({
        message: "Crystal Loaded",
        color: "primary",
        icon: "cloud_done",
        position: "center",
        timeout: 1000,
      });
    }
  });
  socket.on("load_results_success", (data) => {
    $q.loading.hide();
    $q.notify({
      message: "Grid Generated",
      color: "primary",
      icon: "cloud_done",
      position: "center",
      timeout: 1000,
    });
  });

  socket.on("load_simulations_success", (data) => {
    $q.loading.hide();
    $q.notify({
      message: "Simulation Success",
      color: "primary",
      icon: "cloud_done",
      position: "center",
      timeout: 1000,
    });
  });

  socket.on("update_legend", (data) => {
    legendBase64.value = `data:image/png;base64,${data.image_data}`;
  });

  socket.on("get_ipf_success", (data) => {
    IPFBase64.value = data.image_data;
  });

  socket.on("toverp", (data) => {
    if (data.error) {
      console.error(data.error);
    } else {
      console.log("Image Response Received");
      ImageBase64.value = `data:image/png;base64,${data.image_data}`;
    }
  });
});

watch(symmetry, (newSymmetry, oldSymmetry) => {
  if (newSymmetry !== oldSymmetry) {
    // 发送 symmetry 变化事件
    socket.emit("set_symmetry", { symmetry: newSymmetry });
  }
});

watch(
  [direction, threshold],
  ([newDirection, newThreshold], [oldDirection, oldThreshold]) => {
    // 当 direction 或 threshold 变化时...
    socket.emit("get_ipf", {
      direction: newDirection,
      threshold: newThreshold,
    });
  }
);
</script>
