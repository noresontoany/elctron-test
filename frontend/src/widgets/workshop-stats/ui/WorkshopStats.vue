<script setup lang="ts">
import { computed } from 'vue'
import { Layers3, Wrench, CircleCheck, Wallet } from '@lucide/vue'
import { money, type Order } from '@/entities/order'
const props = defineProps<{ orders: Order[] }>()
const metrics = computed(() => [
  {
    label: 'Активные заказы',
    value: props.orders.filter((o) => o.status !== 'delivered').length,
    note: 'Всё под контролем',
    icon: Layers3,
  },
  {
    label: 'Сейчас в работе',
    value: props.orders.filter((o) => o.status === 'repair').length,
    note: 'Мастерская в движении',
    icon: Wrench,
  },
  {
    label: 'Ждут владельцев',
    value: props.orders.filter((o) => o.status === 'ready').length,
    note: 'Готовы к новым маршрутам',
    icon: CircleCheck,
  },
  {
    label: 'Стоимость работ',
    value: money(
      props.orders.filter((o) => o.status !== 'delivered').reduce((sum, o) => sum + o.estimate, 0),
    ),
    note: 'По активным заказам',
    icon: Wallet,
  },
])
</script>
<template>
  <div class="stats-grid">
    <div v-for="metric in metrics" :key="metric.label" class="stat-card">
      <div class="stat-label">{{ metric.label }}<component :is="metric.icon" :size="17" /></div>
      <div class="stat-value">{{ metric.value }}</div>
      <div class="stat-note">{{ metric.note }}</div>
    </div>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 15px;
  margin-bottom: 31px;
}
.stat-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fff;
  padding: 18px 19px 15px;
  box-shadow: 0 2px 2px #22352302;
}
.stat-label {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  font-size: 10px;
  color: #798571;
}
.stat-label svg {
  color: #8c9a80;
}
.stat-value {
  font-size: 30px;
  font-weight: 500;
  letter-spacing: -0.8px;
  margin-top: 11px;
  line-height: 1.25;
}
.stat-note {
  font-size: 9px;
  color: #98a08e;
  margin-top: 6px;
}
@media (max-width: 1200px) {
  .stat-card {
    padding: 16px 13px;
  }
}
@media (max-width: 980px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 640px) {
  .stats-grid {
    gap: 10px;
    margin-bottom: 22px;
  }
  .stat-value {
    font-size: 27px;
  }
  .stat-label {
    font-size: 9px;
  }
  .stat-note {
    font-size: 8px;
  }
}
</style>
