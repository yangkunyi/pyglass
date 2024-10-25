<template>
  <router-view />
</template>

<script setup>
import { useQuasar } from "quasar";
// 定义响应式数据
const $q = useQuasar();
$q.dark.set(true);

defineOptions({
  name: "App",
});
</script>
