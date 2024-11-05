<template>
  <div class="q-pa-md row">
    <!-- Left sidebar with controls -->
    <div class="col-3 q-pr-md">
      <q-card class="sidebar">
        <q-card-section>
          <h6 class="q-mt-lg q-mb-sm">Image Adjustments</h6>
          <div class="q-mt-md">
            <q-badge color="info">
              Brightness: {{ brightness.toFixed(2) }} (-1 to 1)
            </q-badge>
            <q-slider
              v-model="brightness"
              :min="-1"
              :max="1"
              :step="0.01"
              color="info"
            />
          </div>
          <div class="q-mt-md">
            <q-badge color="warning">
              Gamma: {{ gamma.toFixed(2) }} (0.1 to 2.5)
            </q-badge>
            <q-slider
              v-model="gamma"
              :min="0.1"
              :max="2.5"
              :step="0.05"
              color="warning"
            />
          </div>
          <div class="q-mt-md">
            <q-badge color="purple">
              Contrast: {{ contrast.toFixed(2) }} (0 to 5)
            </q-badge>
            <q-slider
              v-model="contrast"
              :min="0"
              :max="5"
              :step="0.1"
              color="purple"
            />
          </div>

          <q-separator />

          <h6 class="q-my-sm">RDF Parameters</h6>
          <q-input
            v-model="qPerPixel"
            type="number"
            label="q per pixel (A^-1)"
            :step="0.001"
            :min="0"
          />
          <div class="q-mt-md">
            <q-badge color="primary">
              Start Index: {{ startIndex }} (0 to {{ length }})
            </q-badge>
            <q-slider
              v-model="startIndex"
              :min="0"
              :max="length"
              color="primary"
            />
          </div>
          <div class="q-mt-md">
            <q-badge color="secondary">
              End Index: {{ endIndex }} (0 to {{ length }})
            </q-badge>
            <q-slider
              v-model="endIndex"
              :min="0"
              :max="length"
              color="secondary"
            />
          </div>
          <div class="q-mt-md">
            <q-badge color="accent">
              Fit Threshold: {{ fitThreshold }}% (0 to 100)
            </q-badge>
            <q-slider
              v-model="fitThreshold"
              :min="0"
              :max="100"
              color="accent"
            />
          </div>
          <div class="q-mt-md">
            <q-badge color="positive"> r_min: {{ rMin }} (0 to 20) </q-badge>
            <q-slider
              v-model="rMin"
              :min="0"
              :max="20"
              :step="0.1"
              color="positive"
            />
          </div>
          <div class="q-mt-md">
            <q-badge color="negative"> r_max: {{ rMax }} (0 to 20) </q-badge>
            <q-slider
              v-model="rMax"
              :min="0"
              :max="20"
              :step="0.1"
              color="negative"
            />
          </div>
          <!-- New controls for brightness, gamma, and contrast -->
        </q-card-section>
      </q-card>
    </div>

    <!-- Right part for image displays and charts -->
    <div class="col-9">
      <!-- Image display section -->
      <div class="row q-col-gutter-md q-mb-md justify-center items-center">
        <!-- Left image -->
        <div class="col-3">
          <q-card class="full-width">
            <q-card-section class="full-height flex flex-center">
              <img
                v-if="leftImageSrc"
                :src="leftImageSrc"
                alt="Left Image"
                style="max-width: 100%; max-height: 100%; object-fit: contain"
              />
              <div v-else class="text-center">No left image loaded</div>
            </q-card-section>
          </q-card>
        </div>
        <!-- Right image -->
        <div class="col-9">
          <q-card class="full-width">
            <q-card-section class="full-height flex flex-center">
              <img
                v-if="rightImageSrc"
                :src="rightImageSrc"
                alt="Right Image"
                style="max-width: 100%; max-height: 100%; object-fit: contain"
              />
              <div v-else class="text-center">No right image loaded</div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Scroll area for chart displays -->
      <q-scroll-area style="height: calc(80vh - 250px)" class="custom-div">
        <q-card
          v-for="(chart, index) in charts"
          :key="index"
          class="chart-card q-mb-md"
        >
          <q-card-section>
            <div class="text-h6">{{ chart.title }}</div>
          </q-card-section>
          <q-card-section class="full-width">
            <div
              :ref="
                (el) => {
                  if (el) chartRefs[index] = el;
                }
              "
              class="chart-container"
            ></div>
          </q-card-section>
        </q-card>
      </q-scroll-area>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { socketRDF } from "boot/socketio";
import * as echarts from "echarts";

const socket=socketRDF

// New refs for image adjustments
const brightness = ref(0);
const gamma = ref(1);
const contrast = ref(1);

const length = 256; // Replace with actual length value

const qPerPixel = ref(0.036);
const startIndex = ref(0);
const endIndex = ref(100);
const fitThreshold = ref(90);
const rMin = ref(0);
const rMax = ref(10);

const chartRefs = ref([]);
const charts = [
  { title: "Diffraction Profile", xAxis: "q (A^-1)", yAxis: "Counts" },
  { title: "Scattering Factor", xAxis: "q (A^-1)", yAxis: "Scattering Factor" },
  { title: "Intensity and Background", xAxis: "q (A^-1)", yAxis: "Intensity" },
  {
    title: "Structure Factor and Fitted Curve",
    xAxis: "q (A^-1)",
    yAxis: "Structure Factor",
  },
  {
    title: "Modified Structure Factor",
    xAxis: "q (A^-1)",
    yAxis: "Modified Structure Factor",
  },
  { title: "ePDF", xAxis: "r (A)", yAxis: "PDF" },
];

const chartData = ref({
  s: [],
  radial_mean: [],
  scattering_factor: [],
  scattering_factor_sq: [],
  phi: [],
  y_fit: [],
  ind_s: [],
  ind_modified_phi: [],
  r_ranges: [],
  pdf: [],
});

const sidebarChartData = computed(() => ({
  qPerPixel: qPerPixel.value,
  startIndex: startIndex.value,
  endIndex: endIndex.value,
  fitThreshold: fitThreshold.value / 100,
  rMin: rMin.value,
  rMax: rMax.value,
}));

const sidebarImageAdjustments = computed(() => ({
  brightness: brightness.value,
  gamma: gamma.value,
  contrast: contrast.value,
  startIndex: startIndex.value,
  endIndex: endIndex.value,
}));

// New refs for image sources
const leftImageSrc = ref(null);
const rightImageSrc = ref(null);

watch(sidebarImageAdjustments, (newData) => {
  socket.emit("update_adjust_params", newData);
  socket.emit("request_img_with_range", newData);
  socket.emit("request_polar_img_with_range", newData);
});

// Watch for changes in sidebar data
watch(sidebarChartData, (newData) => {
  socket.emit("update_rdf_params", newData);
  updateCharts();
});

function updateCharts() {
  charts.forEach((chart, index) => {
    if (!chartRefs.value[index]) return;

    const echartsInstance =
      echarts.getInstanceByDom(chartRefs.value[index]) ||
      echarts.init(chartRefs.value[index]);

    let option = {
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "value",
        name: chart.xAxis,
        nameLocation: "middle",
        nameGap: 30,
        axisLabel: { show: true },
      },
      yAxis: {
        type: "value",
        name: chart.yAxis,
        nameLocation: "middle",
        nameGap: 30,
        axisLabel: { show: true },
      },
      grid: {
        left: "10%",
        right: "5%",
        top: "5%",
        bottom: "15%",
        containLabel: true,
      },
      series: [],
    };

    const commonSeriesOptions = {
      type: "line",
      smooth: true,
      showSymbol: false, // This will hide the data points
      lineStyle: {
        width: 2, // Adjust the line width as needed
      },
    };

    switch (index) {
      case 0: // Diffraction Profile
        option.series.push({
          ...commonSeriesOptions,
          data: chartData.value.s.map((s, i) => [
            s,
            chartData.value.radial_mean[i],
          ]),
        });
        break;
      case 1: // Scattering Factor
        option.series.push({
          ...commonSeriesOptions,
          data: chartData.value.s.map((s, i) => [
            s,
            chartData.value.scattering_factor[i],
          ]),
        });
        break;
      case 2: // Intensity and Background
        option.series.push(
          {
            ...commonSeriesOptions,
            name: "Intensity",
            data: chartData.value.s.map((s, i) => [
              s,
              chartData.value.radial_mean[i],
            ]),
          },
          {
            ...commonSeriesOptions,
            name: "Background",
            data: chartData.value.s.map((s, i) => [
              s,
              chartData.value.background[i],
            ]),
          }
        );
        break;
      case 3: // Structure Factor and Fitted Curve
        option.series.push(
          {
            ...commonSeriesOptions,
            name: "Structure Factor",
            data: chartData.value.s.map((s, i) => [s, chartData.value.phi[i]]),
          },
          {
            ...commonSeriesOptions,
            name: "Fitted Curve",
            data: chartData.value.s.map((s, i) => [
              s,
              chartData.value.y_fit[i],
            ]),
          }
        );
        break;
      case 4: // Modified Structure Factor
        option.series.push({
          ...commonSeriesOptions,
          data: chartData.value.ind_s.map((s, i) => [
            s,
            chartData.value.ind_modified_phi[i],
          ]),
        });
        break;
      case 5: // ePDF
        option.series.push({
          ...commonSeriesOptions,
          data: chartData.value.r_ranges.map((r, i) => [
            r,
            chartData.value.pdf[i],
          ]),
        });
        break;
    }

    echartsInstance.setOption(option);
    echartsInstance.resize();
  });
}

onMounted(() => {
  updateCharts();

  socket.on("rdf_result_response", (data) => {
    console.log(data);
    chartData.value = data;
    updateCharts();
  });

  socket.on("image_response", (data) => {
    if (data.id === "rdf_left") {
      leftImageSrc.value = `data:image/jpeg;base64,${data.image_data}`;
    } else if (data.id === "rdf_right") {
      rightImageSrc.value = `data:image/jpeg;base64,${data.image_data}`;
    }
    console.log("image_received");
  });

  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
});

function handleResize() {
  charts.forEach((_, index) => {
    if (chartRefs.value[index]) {
      const instance = echarts.getInstanceByDom(chartRefs.value[index]);
      if (instance) {
        instance.resize();
      }
    }
  });
}
</script>

<style scoped>
.custom-div {
  border: 2px solid #333;
  border-radius: 8px;
  padding: 16px;
}

.sidebar {
  height: 80vh;
}

.image-card {
  height: 200px;
}

.image-placeholder {
  background-color: #e0e0e0;
  height: 120px;
  border-radius: 4px;
}

.q-badge {
  margin-bottom: 8px;
}

.chart-card {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.chart-card .full-width {
  width: 100%;
  padding: 0;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.chart-card .q-card-section:last-child {
  width: 100%;
  display: flex;
  justify-content: center;
}

.full-width {
  width: 100%;
}

.full-height {
  height: 250px;
}
</style>
