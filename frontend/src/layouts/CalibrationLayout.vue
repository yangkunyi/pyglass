<template>
  <q-layout view="hHh lpr lFf">
    <q-tabs dense align="left">
      <q-route-tab label="Center Calibration" :to="{ name: 'center_calibration' }" exact />
      <q-route-tab label="Elipse Calibration" :to="{ name: 'elipse_calibration' }" exact />
    </q-tabs>
    <q-page-container>
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from "vue";

defineOptions({
  name: "CalibrationLayout",
});
</script>
