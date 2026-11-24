<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { UserPlus, X, Users } from '@lucide/vue'
import { useDirectory, type TeamDto } from '@/entities/workforce'
import { currentSession } from '@/entities/session'
import { Button } from '@/shared/ui/button'
import { useTeamMutations } from '../model/useTeamMutations'
const props = defineProps<{ team: TeamDto }>()
const { users, members } = useDirectory()
const roster = computed(() => members.value.filter((m) => m.teamId === props.team.id))
const available = computed(() =>
  users.value.filter((u) => !roster.value.some((m) => m.userId === u.id)),
)
const selected = shallowRef('')
const role = shallowRef('mechanic')
watch(
  available,
  (rows) => {
    if (!rows.some((u) => u.id === selected.value)) selected.value = rows[0]?.id ?? ''
  },
  { immediate: true },
)
const isManager = currentSession.value?.user.role === 'manager'
const { busy, error, add, remove } = useTeamMutations()
</script>
<template>
  <section class="team-card" :data-team-id="team.id">
    <header>
      <span class="team-icon"><Users :size="20" /></span>
      <div>
        <h2>{{ team.name }}</h2>
        <p>{{ roster.length }} в команде · общая очередь</p>
      </div>
    </header>
    <ul>
      <li v-for="member in roster" :key="member.id">
        <span class="avatar">{{ member.name.slice(0, 1) }}</span>
        <div>
          <strong>{{ member.name }}</strong><small>{{
            member.role === 'lead' ? 'Бригадир' : 'Мастер'
          }}</small>
        </div>
        <Button
          v-if="isManager"
          variant="ghost"
          size="icon"
          :aria-label="`Убрать ${member.name} из ${team.name}`"
          :disabled="busy"
          @click="remove(team.id, member.userId, member.id)"
          ><X :size="15"
        /></Button>
      </li>
    </ul>
    <p v-if="!roster.length" class="empty">В бригаде пока никого нет</p>
    <form v-if="isManager && available.length" @submit.prevent="add(team.id, selected, role)">
      <select v-model="selected" :aria-label="`Добавить в ${team.name}`" :disabled="busy">
        <option v-for="user in available" :key="user.id" :value="user.id">{{ user.name }}</option>
      </select>
      <select v-model="role" aria-label="Роль в бригаде" :disabled="busy">
        <option value="mechanic">Мастер</option>
        <option value="lead">Бригадир</option>
      </select>
      <Button
        type="submit"
        size="icon"
        :aria-label="`Добавить участника: ${team.name}`"
        :disabled="busy || !selected"
        ><UserPlus :size="16"
      /></Button>
    </form>
    <p v-if="error" role="alert" class="error-message">{{ error }}</p>
  </section>
</template>
<style scoped>
.team-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  padding: 22px;
}
header {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 18px;
}
.team-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  background: #edf2e6;
  color: #69834f;
  border-radius: 10px;
}
h2 {
  font-size: 15px;
  font-weight: 600;
}
header p {
  font-size: 11px;
  color: #8c9880;
  margin-top: 4px;
}
ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
li {
  display: flex;
  gap: 11px;
  align-items: center;
  padding: 12px 0;
  border-top: 1px solid #eef0e9;
}
li button {
  margin-left: auto;
}
.avatar {
  width: 32px;
  height: 32px;
  background: #f0f2eb;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 12px;
  color: #768663;
}
strong {
  font-size: 12px;
  font-weight: 500;
}
small {
  display: block;
  color: #9aa38f;
  font-size: 10px;
  margin-top: 3px;
}
form {
  display: flex;
  gap: 6px;
  margin-top: 18px;
}
select {
  min-width: 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: white;
  padding: 8px;
  font-size: 11px;
}
select:first-child {
  flex: 1;
}
.error-message {
  margin-top: 12px;
  font-size: 11px;
}
.empty {
  font-size: 12px;
  color: #89937e;
  padding: 16px 0;
}
</style>
