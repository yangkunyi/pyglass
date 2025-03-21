<template>
  <q-layout view="hHh lpr lFf">
    <q-header>
      <q-tabs dense align="left" class="bg-black text-white shadow-2">
        <q-route-tab
          name="view_image"
          label="View"
          exact
          :to="{ name: 'view_dm4' }"
        />
        <q-route-tab name="rdf" label="RDF" :to="{ name: 'rdf' }" exact />
        <!-- <q-route-tab name="ebsd" label="EBSD" to="/" exact /> -->
        <!-- <q-route-tab name="acom" label="ACOM" to="/ACOM" exact /> -->
        <q-route-tab name="sim" label="SIM" to="/SIM" exact />
        <q-route-tab name="xem" label="ACOM VIEWER" to="/XEM" exact />
      </q-tabs>
    </q-header>

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
  name: "MainLayout",
});
</script>
