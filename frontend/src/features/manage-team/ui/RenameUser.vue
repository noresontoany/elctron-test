<script setup lang="ts">
import { shallowRef, watch } from 'vue'
import type { UserDto } from '@/entities/workforce'
import { Input } from '@/shared/ui/input'
import { Button } from '@/shared/ui/button'
import { useTeamMutations } from '../model/useTeamMutations'
const props = defineProps<{ user: UserDto }>()
const name = shallowRef(props.user.name)
const editing = shallowRef(false)
const snapshot = shallowRef({ ...props.user })
watch(
  () => props.user,
  (user) => {
    if (!editing.value) name.value = user.name
  },
)
const { busy, error, rename } = useTeamMutations()
function start() {
  snapshot.value = { ...props.user }
  name.value = props.user.name
  editing.value = true
}
async function save() {
  if (await rename(snapshot.value, name.value)) editing.value = false
}
</script>
<template>
  <form v-if="editing" class="rename-form" @submit.prevent="save">
    <Input
      v-model="name"
      :aria-label="`Новое имя: ${user.name}`"
      required
      minlength="2"
      maxlength="60"
      :disabled="busy"
    />
    <Button type="submit" variant="outline" :disabled="busy">Сохранить</Button>
    <Button type="button" variant="ghost" :disabled="busy" @click="editing = false">Отмена</Button>
    <span v-if="error" role="alert" class="error-message">{{ error }}</span>
  </form>
  <button v-else class="rename-trigger" :aria-label="`Переименовать ${user.name}`" @click="start">
    {{ user.name }} <span>Изменить имя ↗</span>
  </button>
</template>
<style scoped>
.rename-trigger {
  text-align: left;
  cursor: pointer;
  font-size: 12px;
}
.rename-trigger span {
  display: block;
  color: #93a082;
  font-size: 10px;
  margin-top: 4px;
}
.rename-form {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-width: 390px;
}
.rename-form input {
  width: 140px;
  font-size: 12px;
}
.rename-form button {
  font-size: 10px;
  padding: 6px 9px;
}
.error-message {
  width: 100%;
  font-size: 11px;
}
</style>
