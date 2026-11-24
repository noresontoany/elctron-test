<script setup lang="ts">
import { computed } from 'vue'
import { Plus, Circle, Wrench, CheckCircle2 } from '@lucide/vue'
import { type OrderView, type OrderStatus } from '@/entities/order'
import { OrderCard } from '@/entities/order'

const props = defineProps<{
  orders: OrderView[]
  busy: boolean
  loading: boolean
  canCreate?: boolean
  canAdvance?: (order: OrderView) => boolean
}>()
const emit = defineEmits<{ create: []; edit: [order: OrderView]; advance: [order: OrderView] }>()
const columns = computed(() =>
  [
    {
      id: 'queued' as OrderStatus,
      title: 'В очереди',
      subtitle: 'Всё начинается здесь',
      icon: Circle,
    },
    { id: 'repair' as OrderStatus, title: 'В работе', subtitle: 'В хороших руках', icon: Wrench },
    {
      id: 'ready' as OrderStatus,
      title: 'Готово к выдаче',
      subtitle: 'Можно снова в путь',
      icon: CheckCircle2,
    },
  ].map((column) => ({
    ...column,
    orders: props.orders.filter((order) => order.status === column.id),
  })),
)
</script>

<template>
  <div class="kanban-board" :aria-busy="loading">
    <section v-for="column in columns" :key="column.id" class="kanban-column" :class="column.id">
      <header class="column-header">
        <div class="column-title">
          <component :is="column.icon" :size="16" />
          <h2>{{ column.title }}</h2>
          <span class="column-count">{{ column.orders.length }}</span>
        </div>
        <button
          v-if="canCreate !== false && column.id === 'queued'"
          aria-label="Добавить заказ в очередь"
          class="column-add"
          @click="emit('create')"
        >
          <Plus :size="17" />
        </button>
      </header>
      <p class="column-subtitle">{{ column.subtitle }}</p>
      <div v-if="loading" class="loading-card">Загружаем заказы…</div>
      <template v-else>
        <OrderCard
          v-for="order in column.orders"
          :key="order.id"
          :order="order"
          :busy="busy"
          :action-allowed="canAdvance?.(order) ?? true"
          @edit="emit('edit', $event)"
          @advance="emit('advance', $event)"
        />
        <div v-if="!column.orders.length" class="column-empty">Пока нет заказов</div>
        <button
          v-if="canCreate !== false && column.id === 'queued'"
          class="add-order-placeholder"
          @click="emit('create')"
        >
          <Plus :size="15" /> Новый заказ
        </button>
      </template>
    </section>
  </div>
</template>

<style scoped>
.kanban-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 17px;
  align-items: start;
}
.kanban-column {
  min-width: 0;
  padding: 14px 10px 11px;
  background: #f0f2ec;
  border: 1px solid #e6e9e0;
  border-radius: 10px;
}
.kanban-column.repair {
  background: #f1f2e9;
  border-color: #e8e9dd;
}
.kanban-column.ready {
  background: #edf2e9;
  border-color: #e1e8da;
}
.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0 3px;
}
.column-title {
  display: flex;
  align-items: center;
  gap: 7px;
}
.column-title svg {
  color: #8c9782;
}
.repair .column-title svg {
  color: #b39961;
}
.ready .column-title svg {
  color: #729962;
}
.column-title h2 {
  font-size: 11px;
  font-weight: 600;
  margin: 0;
}
.column-count {
  font-size: 9px;
  border: 1px solid #dce2d2;
  border-radius: 4px;
  min-width: 18px;
  text-align: center;
  color: #8c967f;
}
.column-add {
  color: #a2ac95;
}
.column-subtitle {
  margin: 6px 3px 16px 26px;
  font-size: 8px;
  color: #929b86;
}
.add-order-placeholder {
  width: 100%;
  height: 34px;
  border: 1px dashed #d5ddc9;
  color: #96a087;
  border-radius: 6px;
  font-size: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.add-order-placeholder:hover {
  background: #e5ebdb;
}
.column-empty,
.loading-card {
  padding: 40px 10px;
  text-align: center;
  font-size: 11px;
  color: #98a28c;
}
@media (max-width: 1200px) {
  .kanban-board {
    gap: 10px;
  }
}
@media (max-width: 980px) {
  .kanban-board {
    grid-template-columns: 1fr;
  }
  .kanban-column {
    padding: 14px;
  }
}

@media (min-width: 981px) {
  .column-title h2 {
    font-size: 12px;
  }
  .column-subtitle {
    font-size: 9px;
  }
}
</style>
