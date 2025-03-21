<template>
  <q-page class="q-pa-md">
    <q-btn class="full-width q-mb-md" color="primary" @click="openFile">
      <span v-if="selectedFile">Selected File: {{ selectedFile }}</span>
      <span v-else>Import CIF</span>
    </q-btn>
    <div class="row" style="height: 80vh">
      <div class="col-2 col-lg-2" style="height: 100%; overflow-y: auto">
        <q-card class="full-height column">
          <!-- Your existing input fields for settings -->
          <q-input
            v-model.number="resolution"
            type="number"
            filled
            label="Resolution"
          />
          <q-select
            filled
            v-model="crystal_system"
            :options="options"
            label="Crystal System"
          />
          <q-btn
            no-caps
            class="full-width q-mb-md"
            color="primary"
            @click="generate_grid"
            >Generate Sample Grid
          </q-btn>
          <q-input
            v-model.number="accelerating_voltage"
            type="number"
            filled
            label="Accelerating Voltage"
            suffix="KV"
          />
          <!-- <q-splitter /> -->
          <q-input
            v-model.number="min_intensity"
            type="number"
            filled
            label="Minimal Visible Intensity"
          />
          <q-input
            v-model.number="image_size"
            type="number"
            filled
            label="Image Size"
          />
          <q-input
            v-model.number="pixel_size"
            type="number"
            filled
            label="Pixel Size"
            suffix="A^-1"
          />
          <q-input
            v-model.number="max_excitation_error"
            type="number"
            filled
            label="Max Excitation Error"
          />

          <q-btn
            no-caps
            class="full-width q-mb-md"
            color="primary"
            @click="simulate"
            >Simulate
          </q-btn>
          <q-btn
            no-caps
            class="full-width q-mb-md"
            color="primary"
            @click="saveFile"
            >Save Simulation
          </q-btn>
          <q-btn
            no-caps
            class="full-width q-mb-md"
            color="primary"
            @click="loadFile"
            >Load Simulation
          </q-btn>
          <q-btn
            no-caps
            class="full-width q-mb-md"
            color="primary"
            @click="doMatching"
            >Index
          </q-btn>
          <q-btn
            no-caps
            class="full-width q-mb-md"
            color="primary"
            @click="saveResult"
            >Save Result
          </q-btn>
        </q-card>
      </div>
      <div class="col-5" style="height: 100%">
        <div ref="gridChartContainer" style="height: 100%"></div>
      </div>
      <div class="col-5" style="height: 100%">
        <!-- 添加滑块控制 -->
        <q-card class="q-mb-sm">
          <q-slider
            v-model="symbolSizeFactor"
            :min="0.1"
            :max="10"
            :step="0.1"
            label-always
            class="q-pa-md"
          >
            <template v-slot:label>
              Size Scale: {{ symbolSizeFactor.toFixed(1) }}
            </template>
          </q-slider>
        </q-card>
        <div
          ref="simulationChartContainer"
          style="height: calc(100% - 72px)"
        ></div>
      </div>

      <!-- Container for the chart -->
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue";
import { socketSim } from "boot/socketio";
import { useQuasar } from "quasar";
import * as echarts from "echarts";

const symbolSizeFactor = ref(2);
const selectedFile = ref(null);
const $q = useQuasar();
const socket = socketSim;
const accelerating_voltage = ref(300);
const min_intensity = ref(0.001);
const image_size = ref(128);
const pixel_size = ref(0.0338);
const resolution = ref(10);
const options = [
  { label: "Cubic", value: "cubic" },
  { label: "hexagonal", value: "hexagonal" },
  { label: "trigonal", value: "trigonal" },
  { label: "tetragonal", value: "tetragonal" },
  { label: "orthorhombic", value: "orthorhombic" },
  { label: "monoclinic", value: "monoclinic" },
  { label: "triclinic", value: "triclinic" },
];
const crystal_system = ref(null);
const gridChartContainer = ref(null);
const simulationChartContainer = ref(null);
const max_excitation_error = ref(0.07);
const simulationData = ref(null);

let gridChart = null;
let simulationChart = null;

const loadFile = async () => {
  const filePaths = await window.myAPI.openFileDialog();
  if (filePaths && filePaths.length > 0) {
    selectedFile.value = filePaths[0];
    console.log(selectedFile.value);
    $q.loading.show();
    socket.emit("load_simulation", selectedFile.value);
  } else {
    selectedFile.value = null;
  }
};

const doMatching = () => {
  socket.emit("do_matching");
  $q.loading.show();
};

const saveResult = async () => {
  const filePaths = await window.myAPI.saveFileDialog();
  if (filePaths && filePaths.length > 0) {
    selectedFile.value = filePaths;
    console.log(selectedFile.value);
    $q.loading.show();
    socket.emit("save_result", selectedFile.value);
  } else {
    selectedFile.value = null;
  }
};

const openFile = async () => {
  const filePaths = await window.myAPI.openFileDialog();
  if (filePaths && filePaths.length > 0) {
    selectedFile.value = filePaths[0];
    console.log(selectedFile.value);
    $q.loading.show();
    socket.emit("load_structure", selectedFile.value);
  } else {
    selectedFile.value = null;
  }
};

const saveFile = async () => {
  const filePaths = await window.myAPI.saveFileDialog();
  if (filePaths && filePaths.length > 0) {
    selectedFile.value = filePaths;
    console.log(selectedFile.value);
    $q.loading.show();
    socket.emit("save_simulation", selectedFile.value);
  } else {
    selectedFile.value = null;
  }
};

const simulate = () => {
  socket.emit("simulate", {
    accelerating_voltage: accelerating_voltage.value,
    min_intensity: min_intensity.value,
    image_size: image_size.value,
    pixel_size: pixel_size.value,
    max_excitation_error: max_excitation_error.value,
  });
  $q.loading.show();
};

const generate_grid = () => {
  socket.emit("generate_grid", {
    resolution: resolution.value,
    crystal_system: crystal_system.value,
  });
  $q.loading.show();
};

const handleGridPointClick = (index) => {
  console.log("Clicked scatter point index:", index);
  createSimulationChart(simulationData.value, index);
};

const createGridChart = (data) => {
  if (gridChart) {
    gridChart.dispose();
  }

  gridChart = echarts.init(gridChartContainer.value);

  const gridData = [];
  if (data.grid_x && data.grid_y) {
    for (let i = 0; i < data.grid_x.length; i++) {
      gridData.push([data.grid_x[i], data.grid_y[i]]);
    }

    const option = {
      backgroundColor: "white",
      xAxis: {
        scale: true, // Enable scaling
      },
      yAxis: {
        scale: true,
      },
      series: [
        {
          symbolSize: 5,
          data: gridData,
          type: "scatter",
        },
      ],
      aspectRatio: 1, // Ensure x and y have same length
    };
    gridChart.setOption(option);
    gridChart.on("click", (params) => {
      console.log("Clicked scatter point index:", params.dataIndex);
      if (params.seriesType === "scatter") {
        handleGridPointClick(params.dataIndex);
      }
    });
  }
};

watch(symbolSizeFactor, () => {
  if (simulationChart) {
    const option = simulationChart.getOption();
    if (option.series && option.series.length > 0) {
      option.series[0].symbolSize = function (val) {
        return Math.sqrt(val[2]) * symbolSizeFactor.value;
      };
      simulationChart.setOption(option);
    }
  }
});

const createSimulationChart = (data, index) => {
  if (simulationChart) {
    simulationChart.dispose();
  }
  simulationChart = echarts.init(simulationChartContainer.value);

  const gridData = [];
  let maxIntensity = 0;

  if (data.coords && data.intensities && index != null) {
    const coordsSet = data.coords[index];
    const intensity = data.intensities[index];

    for (let i = 0; i < coordsSet.length; i++) {
      gridData.push([coordsSet[i][0], coordsSet[i][1], intensity[i]]);
      maxIntensity = Math.max(maxIntensity, intensity[i]);
    }

    const option = {
      backgroundColor: "white",
      xAxis: {
        scale: true,
      },
      yAxis: {
        scale: true,
      },
      tooltip: {
        trigger: "item",
        formatter: function (params) {
          const x = params.value[0];
          const y = params.value[1];
          const intensity = params.value[2];
          const distance = Math.sqrt(x * x + y * y); // Distance to origin
          const proportionalIntensity = (
            (intensity / maxIntensity) *
            100
          ).toFixed(4);
          return `Distance: ${distance.toFixed(
            3
          )}<br>Intensity: ${proportionalIntensity}%`;
        },
      },
      series: [
        {
          type: "scatter",
          data: gridData,
          symbolSize: function (val) {
            return Math.sqrt(val[2]) * symbolSizeFactor.value;
          },
          emphasis: {
            focus: "series",
          },
        },
      ],
      aspectRatio: 1, // Ensure x and y have same length
    };
    simulationChart.setOption(option);
  }
};

onMounted(() => {
  socket.on("load_structure_success", (data) => {
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
  socket.on("generate_grid_success", (data) => {
    $q.loading.hide();
    $q.notify({
      message: "Grid Generated",
      color: "primary",
      icon: "cloud_done",
      position: "center",
      timeout: 1000,
    });
    createGridChart(data);
  });

  socket.on("simulate_success", (data) => {
    $q.loading.hide();
    $q.notify({
      message: "Simulation Success",
      color: "primary",
      icon: "cloud_done",
      position: "center",
      timeout: 1000,
    });
    simulationData.value = data;
    createSimulationChart(data, 0);
  });
  socket.on("save_simulate_success", (data) => {
    $q.loading.hide();
    $q.notify({
      message: "Save Simulation Success",
      color: "primary",
      icon: "cloud_done",
      position: "center",
      timeout: 1000,
    });
    simulationData.value = data;
    createSimulationChart(data, 0);
  });
  socket.on("do_matching_success", (data) => {
    $q.loading.hide();
    $q.notify({
      message: "Matching Success",
      color: "primary",
      icon: "cloud_done",
      position: "center",
      timeout: 1000,
    });
  });
  socket.on("save_result_success", (data) => {
    $q.loading.hide();
    $q.notify({
      message: "Result Saved",
      color: "primary",
      icon: "cloud_done",
      position: "center",
      timeout: 1000,
    });
  });
  socket.on("load_simulation_success", (data) => {
    $q.loading.hide();
    $q.notify({
      message: "Simulation Loaded",
      color: "primary",
      icon: "cloud_done",
      position: "center",
      timeout: 1000,
    });
    simulationData.value = data;
    createSimulationChart(data, 0);
  });
});

onUnmounted(() => {
  if (gridChart) {
    gridChart.dispose();
  }
  if (simulationChart) {
    simulationChart.dispose();
  }
});
</script>
