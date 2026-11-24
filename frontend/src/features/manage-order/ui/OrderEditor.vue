<script setup lang="ts">
import { computed, reactive, shallowRef, watch } from 'vue'
import { Bike, Trash2, LoaderCircle } from '@lucide/vue'
import { shortId, type Order, type OrderForm } from '@/entities/order'
import { useDirectory } from '@/entities/workforce'
import { currentSession } from '@/entities/session'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/shared/ui/dialog'
import { useOrderMutations } from '../model/useOrderMutations'

const props = defineProps<{ order?: Order }>()
const emit = defineEmits<{ close: [] }>()
const { teams, members } = useDirectory()
const isManager = currentSession.value?.user.role === 'manager'
const form = reactive<OrderForm>({
  title: props.order?.title ?? '',
  bike: props.order?.bike ?? '',
  customerName: props.order?.customerName ?? '',
  description: props.order?.description ?? '',
  teamId: props.order?.teamId ?? teams.value[0]?.id ?? '',
  assigneeId: props.order?.assigneeId ?? null,
  priority: props.order?.priority ?? 'normal',
  estimate: props.order?.estimate ?? 0,
})
watch(
  teams,
  (rows) => {
    if (!form.teamId && rows[0]) form.teamId = rows[0].id
  },
  { immediate: true },
)
const eligibleMembers = computed(() =>
  members.value.filter((member) => member.teamId === form.teamId),
)
const readOnly = computed(
  () =>
    props.order?.status === 'delivered' ||
    (!isManager &&
      (props.order?.assigneeId !== currentSession.value?.user.id ||
        !members.value.some(
          (m) => m.userId === currentSession.value?.user.id && m.teamId === props.order?.teamId,
        ))),
)
const missingAssignee = computed(
  () => form.assigneeId && !eligibleMembers.value.some((m) => m.userId === form.assigneeId),
)
const { busy, error, create, update, remove } = useOrderMutations()
const confirmingDelete = shallowRef(false)
async function submit() {
  const saved = props.order ? await update(props.order, form) : await create(form)
  if (saved) emit('close')
}
async function deleteOrder() {
  if (props.order && (await remove(props.order))) emit('close')
}
</script>

<template>
  <Dialog
    :open="true"
    @update:open="
      (value) => {
        if (!value && !busy) emit('close')
      }
    "
  >
    <DialogContent
      class="editor-dialog"
      @interact-outside="
        (event) => {
          if (busy) event.preventDefault()
        }
      "
      @escape-key-down="
        (event) => {
          if (busy) event.preventDefault()
        }
      "
    >
      <DialogHeader>
        <div class="dialog-icon"><Bike :size="22" /></div>
        <DialogTitle>{{ order ? 'Детали заказа' : 'Новый заказ' }}</DialogTitle>
        <DialogDescription>{{
          order ? `${shortId(order.id)} · В мастерской` : 'Примем велосипед и запланируем работу.'
        }}</DialogDescription>
      </DialogHeader>
      <form class="order-form" @submit.prevent="submit">
        <fieldset :disabled="busy || readOnly" class="form-fields">
          <div class="field">
            <Label for="title">Что нужно сделать</Label
            ><Input
              id="title"
              v-model="form.title"
              placeholder="Например, полное ТО"
              required
              minlength="3"
              maxlength="120"
            />
          </div>
          <div class="form-row">
            <div class="field">
              <Label for="bike">Велосипед</Label
              ><Input
                id="bike"
                v-model="form.bike"
                placeholder="Марка и модель"
                required
                minlength="2"
                maxlength="100"
              />
            </div>
            <div class="field">
              <Label for="customer">Клиент</Label
              ><Input
                id="customer"
                v-model="form.customerName"
                placeholder="Имя и фамилия"
                required
                minlength="2"
                maxlength="80"
              />
            </div>
          </div>
          <div class="field">
            <Label for="description">Комментарий мастеру</Label
            ><Textarea
              id="description"
              v-model="form.description"
              placeholder="Симптомы, детали, пожелания…"
              maxlength="2000"
            />
          </div>
          <div class="field">
            <Label for="team">Бригада</Label>
            <select
              id="team"
              v-model="form.teamId"
              class="native-select"
              required
              :disabled="!isManager"
              @change="form.assigneeId = null"
            >
              <option v-for="team in teams" :key="team.id" :value="team.id">{{ team.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="field">
              <Label for="assignee">Мастер</Label>
              <select
                id="assignee"
                v-model="form.assigneeId"
                class="native-select"
                :disabled="!isManager"
              >
                <option :value="null">Не назначен</option>
                <option v-if="missingAssignee" :value="form.assigneeId" disabled>
                  Мастер вышел из бригады
                </option>
                <option v-for="member in eligibleMembers" :key="member.id" :value="member.userId">
                  {{ member.name }}
                </option>
              </select>
            </div>
            <div class="field">
              <Label for="estimate">Стоимость, ₽</Label
              ><Input
                id="estimate"
                v-model.number="form.estimate"
                type="number"
                required
                min="0"
                max="1000000"
                step="1"
              />
            </div>
          </div>
          <label class="priority-toggle"
            ><input
              v-model="form.priority"
              type="checkbox"
              true-value="urgent"
              false-value="normal"
            />
            Срочный заказ <span>В первую очередь</span></label
          >
        </fieldset>
        <p v-if="error" role="alert" class="error-message">{{ error }}</p>
        <div v-if="confirmingDelete" class="delete-confirm">
          <p>Удалить заказ без возможности восстановления?</p>
          <Button type="button" variant="destructive" :disabled="busy" @click="deleteOrder"
            >Да, удалить</Button
          ><Button type="button" variant="ghost" @click="confirmingDelete = false">Отмена</Button>
        </div>
        <div class="dialog-footer">
          <Button
            v-if="isManager && order?.status === 'queued'"
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Удалить заказ"
            :disabled="busy"
            @click="confirmingDelete = true"
            ><Trash2 :size="17"
          /></Button>
          <span class="flex-spacer" />
          <Button type="button" variant="outline" :disabled="busy" @click="emit('close')">{{
            readOnly ? 'Закрыть' : 'Отмена'
          }}</Button>
          <Button v-if="!readOnly" type="submit" :disabled="busy"
            ><LoaderCircle v-if="busy" class="animate-spin" :size="16" />{{
              busy ? 'Сохраняем…' : order ? 'Сохранить' : 'Создать заказ'
            }}</Button
          >
        </div>
      </form>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.dialog-icon {
  width: 41px;
  height: 41px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: #edf2e5;
  color: #6f8b56;
  margin-bottom: 9px;
}
.order-form,
.form-fields {
  display: grid;
  gap: 20px;
  min-width: 0;
}
.form-fields {
  border: 0;
  padding: 0;
  margin: 0;
}
.field {
  display: grid;
  gap: 8px;
  min-width: 0;
}
.field label {
  font-size: 11px;
  font-weight: 500;
}
.field input,
.field textarea {
  font-size: 12px;
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.native-select {
  border: 1px solid var(--border);
  background: #fff;
  height: 36px;
  border-radius: 7px;
  padding: 0 10px;
  font-size: 12px;
  width: 100%;
}
.priority-toggle {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 12px;
}
.priority-toggle input {
  accent-color: #617d4c;
}
.priority-toggle span {
  margin-left: auto;
  color: #939e87;
  font-size: 10px;
}
.dialog-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  border-top: 1px solid var(--border);
  padding-top: 17px;
}
.dialog-footer button {
  font-size: 12px;
}
.flex-spacer {
  flex: 1;
}
.delete-confirm {
  background: #fcf0ea;
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
}
.delete-confirm p {
  margin-bottom: 10px;
}
.delete-confirm button {
  margin-right: 7px;
}
@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>
