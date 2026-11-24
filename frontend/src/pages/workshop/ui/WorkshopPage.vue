<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { Plus, Search, SlidersHorizontal, Radio, ArrowUpRight } from '@lucide/vue'
import { syncError, type Order } from '@/entities/order'
import { useWorkshopData } from '@/features/workshop-data'
import { useDirectory } from '@/entities/workforce'
import { currentSession } from '@/entities/session'
import { OrderEditor, useOrderMutations } from '@/features/manage-order'
import { OrderBoard } from '@/widgets/order-board'
import { WorkshopStats } from '@/widgets/workshop-stats'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'

const { orders, myOrders, isLoading } = useWorkshopData()
const { users, members } = useDirectory()
const isManager = currentSession.value?.user.role === 'manager'
const view = shallowRef(isManager ? 'all' : 'mine')
const visibleOrders = computed(() => (view.value === 'mine' ? myOrders.value : orders.value))
const { busy, error, move, deliver, claim } = useOrderMutations()
const search = shallowRef('')
const filter = shallowRef('all')
const editorOpen = shallowRef(false)
const selectedOrder = shallowRef<Order>()
const activeOrders = computed(() => visibleOrders.value.filter((o) => o.status !== 'delivered'))
const filteredOrders = computed(() =>
  activeOrders.value.filter((order) => {
    const text = `${order.title} ${order.bike} ${order.customerName}`.toLocaleLowerCase('ru')
    return (
      text.includes(search.value.trim().toLocaleLowerCase('ru')) &&
      (filter.value === 'all' ||
        (filter.value === 'urgent' && order.priority === 'urgent') ||
        order.assigneeId === filter.value ||
        (filter.value === 'unassigned' && order.assigneeId === null))
    )
  }),
)
function canAdvance(order: Order) {
  if (isManager) return true
  const userId = currentSession.value!.user.id
  const belongs = members.value.some((m) => m.userId === userId && m.teamId === order.teamId)
  return (
    belongs &&
    (order.assigneeId === userId || (order.status === 'queued' && order.assigneeId === null))
  )
}
function openEditor(order?: Order) {
  selectedOrder.value = order ? { ...order } : undefined
  editorOpen.value = true
}
async function advance(order: Order) {
  if (order.status === 'ready') await deliver(order)
  else if (order.status === 'queued' && !isManager) await claim(order)
  else await move(order, order.status === 'queued' ? 'repair' : 'ready')
}
</script>

<template>
  <section class="page-heading">
    <div>
      <div class="eyebrow">КАЖДЫЙ ВЕЛОСИПЕД — НОВАЯ ИСТОРИЯ</div>
      <h1>Заказы мастерской<span class="heading-dot">.</span></h1>
      <p>От первого скрипа до следующей поездки. Весь ремонт — здесь.</p>
    </div>
    <Button v-if="isManager" class="new-order-button" @click="openEditor()"
      ><Plus :size="17" />Новый заказ</Button
    >
  </section>
  <WorkshopStats :orders="orders" />
  <div class="board-toolbar">
    <div class="view-tabs">
      <button :aria-pressed="view === 'all'" @click="view = 'all'">Все заказы</button>
      <button :aria-pressed="view === 'mine'" @click="view = 'mine'">
        Моя очередь <span>{{ myOrders.filter((o) => o.status !== 'delivered').length }}</span>
      </button>
    </div>
    <div class="toolbar-controls">
      <div class="search-input">
        <Search :size="16" /><Input
          v-model="search"
          aria-label="Поиск заказов"
          placeholder="Найти заказ, велосипед, клиента…"
        />
      </div>
      <div class="filter-control">
        <SlidersHorizontal :size="15" /><select v-model="filter" aria-label="Фильтр заказов">
          <option value="all">Все заказы</option>
          <option value="urgent">Срочные</option>
          <option v-for="user in users" :key="user.id" :value="user.id">
            Мастер: {{ user.name }}
          </option>
          <option value="unassigned">Без мастера</option>
        </select>
      </div>
    </div>
  </div>
  <p v-if="syncError" role="status" class="error-message board-error">
    {{ syncError }} Изменения могут быть недоступны.
  </p>
  <p v-if="error" role="alert" class="error-message board-error">{{ error }}</p>
  <p v-if="view === 'mine'" class="queue-explanation">
    Заказы всех ваших бригад. Состав команды изменится — очередь обновится автоматически.
  </p>
  <OrderBoard
    :orders="filteredOrders"
    :busy="busy"
    :loading="isLoading"
    :can-create="isManager"
    :can-advance="canAdvance"
    @create="openEditor()"
    @edit="openEditor"
    @advance="advance"
  />
  <div class="live-tip">
    <span class="live-tip-icon"><Radio :size="19" /></span>
    <div>
      <strong>Одна мастерская. Общий ритм.</strong>
      <p>Откройте вторую вкладку — изменения в заказах появятся у всех автоматически.</p>
    </div>
    <NuxtLink to="/architecture">Как это работает<ArrowUpRight :size="15" /></NuxtLink>
  </div>
  <OrderEditor v-if="editorOpen" :order="selectedOrder" @close="editorOpen = false" />
</template>

<style scoped>
.view-tabs {
  display: flex;
  gap: 6px;
}
.view-tabs button {
  padding: 9px 12px;
  border-radius: 7px;
  font-size: 12px;
  cursor: pointer;
}
.view-tabs button[aria-pressed='true'] {
  background: #e8efdf;
  color: #42663a;
  font-weight: 600;
}
.view-tabs span {
  margin-left: 5px;
  font-size: 10px;
}
.queue-explanation {
  font-size: 12px;
  color: #7b8870;
  margin-bottom: 18px;
}

.new-order-button {
  height: 38px;
  font-size: 11px;
  border-radius: 7px;
  padding: 0 15px;
  box-shadow: 0 3px 5px #2548330a;
}
.board-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 23px;
  min-height: 52px;
  padding-bottom: 13px;
}
.board-tab {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  position: relative;
}
.board-tab:after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -25px;
  width: 100%;
  height: 2px;
  background: #496a43;
}
.board-tab > span {
  background: #e9eee2;
  color: #6d805c;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
}
.toolbar-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}
.search-input {
  position: relative;
}
.search-input > svg {
  position: absolute;
  top: 10px;
  left: 11px;
  color: #9ca590;
}
.search-input input {
  padding-left: 34px;
  width: 265px;
  height: 35px;
  font-size: 10px;
  background: #fff;
  border-color: #e0e5d9;
  border-radius: 6px;
  box-shadow: none;
}
.filter-control {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 0 9px;
  height: 35px;
  border: 1px solid #e0e5d9;
  background: #fff;
  border-radius: 6px;
  color: #74806a;
}
.filter-control select {
  border: none;
  background: transparent;
  font-size: 10px;
  padding-right: 4px;
  outline-offset: 2px;
  max-width: 140px;
}
.live-tip {
  margin-top: 25px;
  border: 1px solid #dfe7d5;
  background: #f1f5eb;
  border-radius: 9px;
  padding: 15px 19px;
  display: flex;
  gap: 14px;
  align-items: center;
}
.live-tip-icon {
  color: #8ca370;
}
.live-tip strong {
  font-size: 10px;
  font-weight: 600;
  color: #678052;
}
.live-tip p {
  margin: 4px 0 0;
  font-size: 9px;
  color: #94a084;
  line-height: 1.5;
}
.live-tip a {
  margin-left: auto;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 9px;
  color: #82966a;
}
@media (max-width: 1200px) {
  .search-input input {
    width: 225px;
  }
}
@media (max-width: 980px) {
  .board-toolbar {
    flex-wrap: wrap;
    padding-bottom: 15px;
  }
  .board-tab:after {
    display: none;
  }
  .toolbar-controls {
    width: 100%;
  }
  .search-input {
    flex: 1;
  }
  .search-input input {
    width: 100%;
  }
  .live-tip a {
    display: none;
  }
}
@media (max-width: 640px) {
  .new-order-button {
    width: 100%;
  }
  .toolbar-controls {
    gap: 7px;
  }
  .filter-control {
    padding: 0 6px;
  }
  .filter-control select {
    width: 84px;
  }
  .search-input input {
    font-size: 9px;
  }
  .live-tip {
    padding: 14px;
    gap: 10px;
  }
  .live-tip p {
    font-size: 9px;
  }
}
</style>
