<script setup lang="ts">
import { computed } from 'vue'
import { currentSession, switchUser } from '@/entities/session'
import { useDirectory } from '@/entities/workforce'
const { users } = useDirectory()
const current = computed(() => users.value.find((u) => u.id === currentSession.value?.user.id))
function change(event: Event) {
  switchUser((event.target as HTMLSelectElement).value)
}
</script>
<template>
  <div class="user-switcher">
    <label for="demo-user">Демо-пользователь · эта вкладка</label>
    <select id="demo-user" :value="currentSession?.user.id" @change="change">
      <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
    </select>
    <span
      >{{ current?.role === 'manager' ? 'Руководитель' : 'Мастер' }} · можно открыть вторую
      вкладку</span
    >
  </div>
</template>
<style scoped>
.user-switcher {
  display: grid;
  gap: 7px;
  width: 100%;
}
label {
  font-size: 9px;
  color: #87947c;
}
select {
  width: 100%;
  border: 1px solid #dfe5d7;
  background: #fff;
  border-radius: 6px;
  padding: 8px;
  font-size: 12px;
}
span {
  font-size: 9px;
  line-height: 1.5;
  color: #7c8b71;
}
</style>
