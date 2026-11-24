<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUpRight, Bike, MoveRight, Check, Zap } from '@lucide/vue'
import { Button } from '@/shared/ui/button'
import { money, shortId, type OrderView } from '../model/order'

const props = defineProps<{ order: OrderView; busy: boolean; actionAllowed?: boolean }>()
const emit = defineEmits<{ edit: [order: OrderView]; advance: [order: OrderView] }>()
const initials = computed(() =>
  props.order.assignee === 'Не назначен' ? '—' : props.order.assignee.slice(0, 1),
)
const action = computed(
  () =>
    ({
      queued: 'Взять в работу',
      repair: 'Завершить ремонт',
      ready: 'Выдать велосипед',
      delivered: '',
    })[props.order.status],
)
</script>

<template>
  <article class="order-card" :data-order-id="order.id">
    <div class="card-topline">
      <span class="order-number">{{ shortId(order.id) }}</span><span
        v-if="order.priority === 'urgent'"
        class="urgent-badge"
        ><Zap :size="11" /> Срочно</span
      ><button
        class="open-order"
        :aria-label="`Открыть: ${order.title}`"
        @click="emit('edit', order)"
      >
        <ArrowUpRight :size="17" />
      </button>
    </div>
    <button class="card-title" @click="emit('edit', order)">{{ order.title }}</button>
    <div class="team-name">{{ order.teamName }}</div>
    <div class="bike-name"><Bike :size="15" />{{ order.bike }}</div>
    <p class="card-description">{{ order.description || 'Комментарий пока не добавлен.' }}</p>
    <div class="card-customer">
      <span>{{ order.customerName }}</span><strong>{{ money(order.estimate) }}</strong>
    </div>
    <div class="card-bottom">
      <span class="assignee"
        ><span
          class="avatar"
          :class="{
            maria: order.assignee === 'Мария',
            unassigned: order.assignee === 'Не назначен',
          }"
          >{{ initials }}</span
        >{{ order.assignee }}</span
      ><Button
        v-if="action"
        variant="ghost"
        class="advance-button"
        :disabled="busy || actionAllowed === false"
        :title="
          actionAllowed === false ? 'Действие доступно назначенному мастеру бригады' : undefined
        "
        @click="emit('advance', order)"
        >{{ action }}<Check v-if="order.status === 'ready'" :size="14" /><MoveRight
          v-else
          :size="14"
      /></Button>
    </div>
  </article>
</template>

<style scoped>
.team-name {
  font-size: 9px;
  color: #8e9b80;
  margin: 7px 0;
}
.order-card {
  background: #fff;
  border: 1px solid #e0e5d8;
  border-radius: 8px;
  padding: 14px 13px 0;
  margin-bottom: 10px;
  box-shadow: 0 3px 4px #303e2203;
  transition:
    box-shadow 0.15s,
    border-color 0.15s;
}
.order-card:hover {
  border-color: #bccbb0;
  box-shadow: 0 4px 12px #263d1d08;
}
.card-topline {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 19px;
  margin-bottom: 9px;
}
.urgent-badge {
  font-size: 8px;
  border-radius: 4px;
  background: #fbf0e6;
  color: #b78d5b;
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 5px;
}
.open-order {
  margin-left: auto;
  color: #a5ae9a;
  opacity: 0.7;
}
.open-order:hover {
  opacity: 1;
  color: #33563f;
}
.card-title {
  display: block;
  font-size: 12px;
  line-height: 1.5;
  font-weight: 600;
  text-align: left;
  overflow-wrap: anywhere;
}
.bike-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  color: #8c9681;
  margin: 7px 0 12px;
}
.bike-name svg {
  color: #9aa88c;
}
.card-description {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 31px;
  font-size: 9px;
  line-height: 1.75;
  color: #919a86;
  margin: 0 0 15px;
}
.card-customer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  font-size: 9px;
  padding-bottom: 13px;
}
.card-customer > span {
  color: #8a947f;
}
.card-customer strong {
  font-weight: 600;
  color: #526749;
  white-space: nowrap;
}
.card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 3px;
  min-height: 43px;
  border-top: 1px solid #eff1e9;
}
.assignee {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 8px;
  color: #8c967f;
  white-space: nowrap;
}
.avatar {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #e9eede;
  color: #85996b;
  display: grid;
  place-items: center;
  font-size: 8px;
}
.avatar.maria {
  background: #f2e9de;
  color: #b29d7e;
}
.avatar.unassigned {
  background: #f0f1ec;
  color: #a7ad9d;
}
.advance-button {
  font-size: 8px;
  font-weight: 500;
  height: 25px;
  padding: 0 3px;
  gap: 4px;
  color: #789265;
}
.advance-button svg {
  width: 11px;
}
@media (min-width: 1500px) {
  .card-title {
    font-size: 14px;
  }
  .card-description,
  .bike-name,
  .card-customer {
    font-size: 11px;
  }
  .advance-button,
  .assignee {
    font-size: 10px;
  }
  .order-card {
    padding: 18px 17px 0;
  }
  .card-bottom {
    min-height: 49px;
  }
}
@media (max-width: 1200px) {
  .card-bottom {
    flex-wrap: wrap;
    padding: 8px 0;
    row-gap: 6px;
  }
  .card-bottom .advance-button {
    margin-left: auto;
  }
}
@media (max-width: 980px) {
  .order-card {
    padding: 15px 15px 0;
  }
  .card-title {
    font-size: 14px;
  }
  .card-description,
  .bike-name,
  .card-customer {
    font-size: 11px;
  }
  .card-bottom {
    flex-wrap: nowrap;
  }
  .assignee,
  .advance-button {
    font-size: 10px;
  }
}
@media (max-width: 640px) {
  .card-title {
    font-size: 14px;
  }
  .card-description {
    min-height: 0;
  }
}

@media (min-width: 981px) {
  .card-title {
    font-size: 13px;
  }
  .card-description,
  .bike-name,
  .card-customer {
    font-size: 11px;
  }
  .assignee,
  .advance-button {
    font-size: 10px;
  }
  .urgent-badge {
    font-size: 9px;
  }
  .card-bottom {
    min-height: 45px;
  }
}
</style>
