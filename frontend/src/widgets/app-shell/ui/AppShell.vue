<script setup lang="ts">
import { computed } from 'vue'
import { currentSession } from '@/entities/session'
import { UserSwitcher } from '@/features/switch-user'
import { useOnline } from '@vueuse/core'
import { syncConnected, syncError } from '@/entities/order'
import { useRoute } from '#imports'
import {
  Aperture,
  LayoutDashboard,
  Archive,
  Workflow,
  ArrowUpRight,
  ChevronDown,
  Bike,
  ExternalLink,
} from '@lucide/vue'
const online = useOnline()
const route = useRoute()
const isArchitecture = computed(() => route.path === '/architecture')
const date = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'long',
  weekday: 'short',
}).format(new Date())
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <NuxtLink to="/" class="brand"
        ><span class="brand-mark"><Aperture :size="27" /></span
        ><span>spoke<span class="brand-period">.</span></span></NuxtLink
      >
      <div class="workspace-switch">
        <span class="workspace-icon"><Bike :size="19" /></span>
        <div>
          <strong>{{
            currentSession?.workspace === 'lab' ? 'Тестовая мастерская' : 'Веломастерская'
          }}</strong><span>Рабочее пространство</span>
        </div>
        <ChevronDown :size="14" />
      </div>
      <p class="nav-label">МАСТЕРСКАЯ</p>
      <nav aria-label="Основная навигация">
        <NuxtLink to="/" :class="{ active: route.path === '/' }"
          ><LayoutDashboard :size="18" />Заказы<span class="nav-dot"
        /></NuxtLink>
        <NuxtLink to="/team" :class="{ active: route.path === '/team' }"
          ><Bike :size="18" />Команда и загрузка</NuxtLink
        >
        <NuxtLink to="/archive" :class="{ active: route.path === '/archive' }"
          ><Archive :size="18" />Архив заказов</NuxtLink
        >
      </nav>
      <p class="nav-label second-label">УЧЕБНЫЙ ПРОЕКТ</p>
      <nav>
        <NuxtLink to="/architecture" :class="{ active: isArchitecture }"
          ><Workflow :size="18" />Как это устроено<ArrowUpRight
            :size="14"
            class="nav-arrow" /></NuxtLink
        ><a href="/api/docs" target="_blank" rel="noreferrer"
          ><ExternalLink :size="18" />Документация API</a
        >
      </nav>
      <div class="sidebar-bottom">
        <div class="demo-note">
          <span class="tiny-label">СОЗДАНО ДЛЯ ЭКСПЕРИМЕНТОВ</span>
          <p>Хороший день,<br />чтобы что-нибудь починить.</p>
          <div class="mini-wheel"><Aperture :size="48" stroke-width="1" /></div>
        </div>
        <div class="profile">
          <UserSwitcher />
        </div>
      </div>
    </aside>
    <div class="main-shell">
      <header class="topbar">
        <div>
          <span class="breadcrumb-root">Мастерская</span><span class="breadcrumb-divider">/</span
          ><span>{{
            isArchitecture
              ? 'Архитектура'
              : route.path === '/team'
                ? 'Команда'
                : route.path === '/archive'
                  ? 'Архив'
                  : 'Заказы'
          }}</span>
        </div>
        <div class="topbar-right">
          <span
            class="sync-status"
            :class="{ connected: online && syncConnected, disconnected: !online || syncError }"
            role="status"
            ><span />{{
              !online || syncError
                ? 'Нет связи'
                : syncConnected
                  ? 'Синхронизировано'
                  : 'Подключение…'
            }}</span
          ><span class="demo-pill">Демо</span><span class="today">{{ date }}</span>
        </div>
      </header>
      <main class="main-content"><slot /></main>
      <footer class="app-footer">
        <span>spoke. <span class="footer-muted">Меньше рутины. Больше движения.</span></span
        ><NuxtLink to="/architecture">Учебный проект <ArrowUpRight :size="12" /></NuxtLink>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 238px;
  flex-shrink: 0;
  background: #f0f3ec;
  border-right: 1px solid var(--border);
  padding: 30px 19px 0;
  display: flex;
  flex-direction: column;
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 20;
  overflow-y: auto;
}
.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 35px;
  font-weight: 750;
  letter-spacing: -1.8px;
  padding: 0 9px;
  width: fit-content;
}
.brand-mark {
  background: #264a3c;
  color: #dceabd;
  border-radius: 10px;
  width: 37px;
  height: 37px;
  display: grid;
  place-items: center;
}
.brand-period {
  color: #789561;
}
.workspace-switch {
  margin: 32px 0 30px;
  padding: 12px 9px;
  border: 1px solid #dce3d5;
  border-radius: 9px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8faf5;
}
.workspace-icon {
  width: 30px;
  height: 32px;
  border-radius: 6px;
  display: grid;
  place-items: center;
  background: #e7eddf;
}
.workspace-switch strong {
  font-size: 12px;
  display: block;
  font-weight: 600;
}
.workspace-switch div > span {
  display: block;
  font-size: 9px;
  margin-top: 3px;
  color: #838b7e;
}
.workspace-switch > svg {
  margin-left: auto;
}
.nav-label {
  padding: 0 12px;
  font-size: 9px;
  letter-spacing: 1.6px;
  font-weight: 600;
  color: #89917f;
  margin-bottom: 12px;
}
.sidebar nav {
  display: grid;
  gap: 6px;
}
.sidebar nav a {
  height: 43px;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0 12px;
  color: #76806e;
  font-size: 12px;
  border-radius: 7px;
}
.sidebar nav a:hover {
  background: #e7ecdf;
}
.sidebar nav a.active {
  background: #e0e8d5;
  color: #355039;
  font-weight: 600;
}
.nav-dot {
  width: 6px;
  height: 6px;
  background: #638153;
  border-radius: 50%;
  margin-left: auto;
}
.nav-arrow {
  margin-left: auto;
}
.second-label {
  margin-top: 32px;
}
.sidebar-bottom {
  margin-top: auto;
}
.demo-note {
  margin: 25px 3px;
  background: #e7eddd;
  border: 1px solid #dce4d0;
  padding: 17px 13px;
  border-radius: 10px;
  position: relative;
  overflow: hidden;
}
.tiny-label {
  font-size: 7px;
  letter-spacing: 1px;
  color: #7b8b67;
  font-weight: 700;
}
.demo-note p {
  font-size: 12px;
  font-weight: 500;
  line-height: 1.7;
  padding: 8px 0 6px;
}
.mini-wheel {
  position: absolute;
  right: -9px;
  bottom: -10px;
  color: #b9c8a6;
}
.profile {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 19px 3px;
  border-top: 1px solid #dce3d5;
}
.profile-avatar {
  display: grid;
  place-items: center;
  width: 33px;
  height: 33px;
  border-radius: 50%;
  background: #d7e0ca;
  font-size: 12px;
}
.profile strong {
  font-size: 12px;
  display: block;
}
.profile div > span {
  color: #8a9281;
  font-size: 9px;
  display: block;
  margin-top: 3px;
}
.online-dot {
  margin-left: auto;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6c9461;
}
.main-shell {
  margin-left: 238px;
  min-width: 0;
  width: calc(100% - 238px);
  display: flex;
  flex-direction: column;
}
.topbar {
  height: 72px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 38px;
  border-bottom: 1px solid var(--border);
  font-size: 11px;
  background: #fbfcf8;
}
.breadcrumb-root {
  color: #8a9387;
}
.breadcrumb-divider {
  color: #c3c9bd;
  margin: 0 15px;
}
.topbar-right {
  display: flex;
  gap: 20px;
  align-items: center;
}
.demo-pill {
  font-size: 10px;
  color: #697e58;
  background: #edf2e6;
  border: 1px solid #e0e8d5;
  border-radius: 20px;
  padding: 5px 10px;
}
.today {
  font-size: 10px;
  color: #858e80;
}
.main-content {
  padding: 38px 38px 26px;
  flex: 1;
  max-width: 1700px;
  width: 100%;
  margin: 0 auto;
}
.app-footer {
  padding: 17px 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #839375;
  font-size: 9px;
}
.footer-muted {
  margin-left: 7px;
  font-size: 8px;
  color: #a6ae9e;
}
.app-footer a {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #a2ab97;
  font-size: 8px;
}
@media (max-height: 800px) {
  .demo-note {
    display: none;
  }
}
@media (min-width: 1500px) {
  .main-content {
    padding: 42px 48px;
  }
}
@media (max-width: 1200px) {
  .sidebar {
    width: 205px;
    padding-left: 12px;
    padding-right: 12px;
  }
  .main-shell {
    margin-left: 205px;
    width: calc(100% - 205px);
  }
  .main-content {
    padding: 28px 23px;
  }
  .topbar {
    padding: 0 23px;
  }
}
@media (max-width: 980px) {
  .sidebar {
    width: 180px;
  }
  .main-shell {
    margin-left: 180px;
    width: calc(100% - 180px);
  }
  .workspace-switch {
    padding: 9px 5px;
  }
  .workspace-switch div > span {
    font-size: 8px;
  }
  .workspace-switch strong {
    font-size: 10px;
  }
  .workspace-switch > svg {
    display: none;
  }
}
@media (max-width: 640px) {
  .app-shell {
    display: block;
  }
  .sidebar {
    position: static;
    width: 100%;
    padding: 14px 18px;
    border-right: none;
    border-bottom: 1px solid var(--border);
    display: block;
  }
  .brand {
    font-size: 26px;
    padding: 0;
  }
  .brand-mark {
    width: 30px;
    height: 30px;
  }
  .brand-mark svg {
    width: 22px;
  }
  .workspace-switch,
  .nav-label,
  .demo-note,
  .sidebar nav:nth-of-type(2) {
    display: none;
  }
  .profile {
    padding: 12px 0 0;
    margin-top: 14px;
  }
  .sidebar nav {
    display: flex;
    margin-top: 14px;
    gap: 8px;
  }
  .sidebar nav a {
    height: 34px;
    font-size: 11px;
    padding: 0 10px;
  }
  .nav-dot {
    display: none;
  }
  .main-shell {
    margin-left: 0;
    width: 100%;
  }
  .topbar {
    height: 50px;
    padding: 0 20px;
  }
  .topbar-right .today {
    display: none;
  }
  .topbar-right {
    gap: 0;
  }
  .demo-pill {
    font-size: 8px;
  }
  .main-content {
    padding: 26px 18px;
  }
  .app-footer {
    padding: 15px 20px;
    gap: 10px;
  }
  .footer-muted {
    display: none;
  }
}

.sync-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  color: #98a38a;
  white-space: nowrap;
}
.sync-status > span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #a9b29e;
}
.sync-status.connected > span {
  background: #80a166;
  box-shadow: 0 0 0 3px #eaf1e2;
}
.sync-status.disconnected {
  color: #b17c4c;
}
.sync-status.disconnected > span {
  background: #b17c4c;
}
@media (max-width: 640px) {
  .topbar-right {
    gap: 10px;
  }
  .sync-status {
    font-size: 8px;
  }
}
</style>
