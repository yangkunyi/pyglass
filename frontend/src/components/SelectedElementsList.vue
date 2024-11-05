<template>
  <div class="q-pa-md">
    <div class="row q-col-gutter-md">
      <div class="col-4">
        <q-scroll-area style="height: 300px">
          <q-list v-if="localSelectedElements.length > 0" bordered separator>
            <q-item-label header>Selected Elements</q-item-label>
            <q-item
              v-for="(element, index) in localSelectedElements"
              :key="element.symbol"
            >
              <q-item-section>
                <q-item-label>{{ element.symbol }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-input
                  v-model.number="element.quantity"
                  type="number"
                  min="0"
                  @update:model-value="updateQuantity(index, $event)"
                  style="width: 100px"
                  dense
                />
              </q-item-section>
            </q-item>
          </q-list>
          <div v-else>
            <p>No elements selected.</p>
          </div>
        </q-scroll-area>
        <q-btn
          label="Save"
          color="primary"
          @click="saveElements"
          class="q-mt-md"
          v-if="localSelectedElements.length > 0"
        />
      </div>

      <!-- 显示计算结果的表格 -->
      <div class="col-8">
        <q-table
          :rows="elementsWithPercentage"
          :columns="columns"
          row-key="symbol"
          rows-per-page-options="0"
          virtual-scroll
          style="height: 300px"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { socketRDF } from "boot/socketio";

const socket = socketRDF
const props = defineProps({
  selectedElements: {
    type: Array,
    required: true,
  },
});

const localSelectedElements = ref([...props.selectedElements]);
const elementsWithPercentage = ref([]);

const columns = [
  { name: "symbol", label: "Element", field: "symbol", align: "left" },
  { name: "quantity", label: "Quantity", field: "quantity", align: "center" },
  {
    name: "percentage",
    label: "Percentage",
    field: "percentage",
    align: "center",
  },
];

const updateQuantity = (index, newQuantity) => {
  localSelectedElements.value[index].quantity = newQuantity;
};

const saveElements = () => {
  const totalQuantity = localSelectedElements.value.reduce(
    (sum, element) => sum + element.quantity,
    0
  );
  elementsWithPercentage.value = localSelectedElements.value.map((element) => ({
    ...element,
    percentage: element.quantity / totalQuantity,
  }));

  const selectedFields = elementsWithPercentage.value.map((element) => ({
    atomicNumber: element.atomicNumber,
    symbol: element.symbol,
    percentage: element.percentage,
  }));
  socket.emit("select_elements", selectedFields);
  console.log("Elements with percentage:", elementsWithPercentage.value);
};

// 监听 selectedElements 的变化，更新本地副本
watch(
  () => props.selectedElements,
  (newSelectedElements) => {
    localSelectedElements.value = [...newSelectedElements];
  },
  { deep: true }
);
</script>

<style scoped>
.compact-list {
  padding: 0;
}

.compact-item {
  padding: 4px 8px;
}
</style>
