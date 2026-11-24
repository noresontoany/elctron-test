<script setup lang="ts">
import { onMounted, shallowRef } from 'vue'
import { AppShell } from '@/widgets/app-shell'
import { connectSession } from '@/entities/session'
import { Button } from '@/shared/ui/button'
const ready = shallowRef(false)
const error = shallowRef('')
async function connect() {
  error.value = ''
  try {
    await connectSession()
    ready.value = true
  } catch {
    error.value = 'Не удалось подключиться к мастерской. Проверьте, запущены ли контейнеры.'
  }
}
onMounted(connect)
</script>
<template>
  <AppShell v-if="ready"><NuxtPage /></AppShell>
  <div v-else class="boot-state">
    <h1>Открываем мастерскую<span class="heading-dot">.</span></h1>
    <p>{{ error || 'Подключаем рабочее пространство…' }}</p>
    <Button v-if="error" @click="connect">Попробовать снова</Button>
  </div>
</template>
