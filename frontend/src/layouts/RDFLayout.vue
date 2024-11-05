<template>
  <q-layout view="hHh lpr lFf">
    <q-tabs dense align="left">
      <q-route-tab label="Elements Selection" :to="{ name: 'table' }" exact />
      <q-route-tab name="2" label="Calculate RDF" :to="{ name: '2' }" exact />
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
  name: "RDFLayout",
});
</script>
