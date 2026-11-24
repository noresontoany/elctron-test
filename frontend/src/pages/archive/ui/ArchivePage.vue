<script setup lang="ts">
import { useWorkshopData } from '@/features/workshop-data'
import { computed } from 'vue'
import { Archive, ArrowUpRight } from '@lucide/vue'
import { money, shortId } from '@/entities/order'
const { orders, isLoading } = useWorkshopData()
const delivered = computed(() => orders.value.filter((order) => order.status === 'delivered'))
</script>
<template>
  <section class="page-heading">
    <div>
      <div class="eyebrow">СНОВА В ПУТИ</div>
      <h1>Архив заказов<span class="heading-dot">.</span></h1>
      <p>Готовые велосипеды уже у владельцев. История остаётся здесь.</p>
    </div>
    <span class="archive-icon"><Archive :size="30" /></span>
  </section>
  <div class="archive-table-wrap">
    <table class="archive-table">
      <thead>
        <tr>
          <th>Заказ</th>
          <th>Велосипед / клиент</th>
          <th>Мастер</th>
          <th>Стоимость</th>
          <th>Выдан</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="order in delivered" :key="order.id">
          <td>
            <span class="order-number">{{ shortId(order.id) }}</span><strong>{{
              order.title
            }}</strong>
          </td>
          <td>
            {{ order.bike }}<span>{{ order.customerName }}</span>
          </td>
          <td>{{ order.assignee }}</td>
          <td>{{ money(order.estimate) }}</td>
          <td>{{ order.updatedAt.toLocaleDateString('ru-RU') }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!delivered.length" class="archive-empty">
      {{ isLoading ? 'Загружаем историю…' : 'Выданные заказы появятся здесь.' }}
    </p>
  </div>
  <NuxtLink to="/" class="back-link">Вернуться в мастерскую<ArrowUpRight :size="15" /></NuxtLink>
</template>

<style scoped>
.archive-icon {
  color: #9cb18c;
}
.archive-table-wrap {
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow-x: auto;
  background: #fff;
}
.archive-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  text-align: left;
}
.archive-table th {
  background: #f1f4ec;
  padding: 15px 20px;
  font-size: 10px;
  font-weight: 500;
  color: #8b9780;
}
.archive-table td {
  padding: 20px;
  border-top: 1px solid var(--border);
}
.archive-table td span {
  display: block;
  margin-top: 4px;
  color: #9aa28f;
  font-size: 10px;
}
.archive-table td strong {
  display: block;
  margin-top: 5px;
  font-weight: 500;
}
.archive-empty {
  text-align: center;
  padding: 40px;
  color: #8c9980;
}
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-top: 25px;
  font-size: 12px;
  color: #7e916b;
}
</style>
