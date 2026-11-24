<script setup lang="ts">
import { computed } from 'vue'
import { useDirectory } from '@/entities/workforce'
import { currentSession } from '@/entities/session'
import { money } from '@/entities/order'
import { useWorkshopData } from '@/features/workshop-data'
import { TeamMembers, RenameUser } from '@/features/manage-team'
const { users, teams, isLoading } = useDirectory()
const { workload } = useWorkshopData()
const isManager = currentSession.value?.user.role === 'manager'
const rows = computed(() =>
  users.value.map((user) => {
    const groups = workload.value.filter((row) => row.userId === user.id)
    return {
      user,
      total: groups.reduce((sum, g) => sum + g.total, 0),
      amount: groups.reduce((sum, g) => sum + g.amount, 0),
      urgent: groups.filter((g) => g.priority === 'urgent').reduce((sum, g) => sum + g.total, 0),
    }
  }),
)
const unassigned = computed(() =>
  workload.value.filter((row) => row.userId === null).reduce((sum, g) => sum + g.total, 0),
)
</script>
<template>
  <section class="page-heading">
    <div>
      <div class="eyebrow">ХОРОШАЯ РАБОТА НАЧИНАЕТСЯ С КОМАНДЫ</div>
      <h1>Люди и бригады<span class="heading-dot">.</span></h1>
      <p>Одна команда может работать в нескольких бригадах. У каждой — своя очередь.</p>
    </div>
  </section>
  <div class="demo-instruction">
    <strong>Попробуйте в двух вкладках</strong>
    <p>
      Во второй выберите Марию и откройте «Мою очередь». Здесь добавьте её в «Сервис и ТО» — заказы
      этой бригады появятся у неё сами.
    </p>
  </div>
  <p v-if="isLoading">Загружаем команду…</p>
  <div class="teams-grid"><TeamMembers v-for="team in teams" :key="team.id" :team="team" /></div>
  <p class="membership-note">
    При выходе из бригады мастер теряет право менять её заказы. Старые назначения сохраняются;
    руководитель может передать незавершённую работу другому участнику. Роль бригадира пока служит
    отметкой в составе команды.
  </p>
  <section class="workload-panel">
    <header>
      <div>
        <h2>Загрузка мастеров</h2>
        <p>Все незакрытые заказы · сумма по текущей оценке</p>
      </div>
      <span>{{ unassigned }} без мастера</span>
    </header>
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Участник</th>
            <th>В работе и очереди</th>
            <th>Срочные</th>
            <th>Стоимость</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.user.id" :data-user-id="row.user.id">
            <td>
              <RenameUser v-if="isManager" :user="row.user" /><span v-else>{{ row.user.name }}</span
              ><small>{{ row.user.role === 'manager' ? 'Руководитель' : 'Мастер' }}</small>
            </td>
            <td data-testid="workload-count">
              <strong>{{ row.total }}</strong>
            </td>
            <td>
              <span :class="{ 'urgent-count': row.urgent > 0 }">{{ row.urgent }}</span>
            </td>
            <td>{{ money(row.amount) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
  <div class="relationship-note">
    <span>Пользователь</span><b>→</b><span>Участие в бригаде</span><b>→</b><span>Бригада</span
    ><b>→</b><span>Заказы</span>
  </div>
</template>
<style scoped>
.demo-instruction {
  background: #eff4e7;
  border: 1px solid #dee8d0;
  border-radius: 10px;
  padding: 17px 20px;
  margin-bottom: 24px;
  font-size: 12px;
  color: #607a4d;
}
.demo-instruction strong {
  font-weight: 600;
}
.demo-instruction p {
  margin-top: 7px;
  line-height: 1.7;
  color: #80916e;
}
.teams-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}
.membership-note {
  font-size: 11px;
  color: #8c987f;
  line-height: 1.8;
  margin: 15px 0 28px;
  max-width: 820px;
}
.workload-panel {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.workload-panel header {
  display: flex;
  gap: 16px;
  justify-content: space-between;
  align-items: center;
  padding: 22px;
}
.workload-panel h2 {
  font-size: 15px;
  font-weight: 600;
}
.workload-panel header p {
  font-size: 11px;
  color: #98a18f;
  margin-top: 5px;
}
.workload-panel header > span {
  font-size: 11px;
  color: #8b977e;
}
.table-scroll {
  overflow: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
th {
  font-size: 10px;
  font-weight: 500;
  color: #99a38e;
  padding: 12px 22px;
  background: #fafbf7;
}
td {
  padding: 16px 22px;
  border-top: 1px solid #eef0e9;
  font-size: 12px;
}
td small {
  display: block;
  font-size: 9px;
  color: #a0aa97;
  margin-top: 6px;
}
td strong {
  font-weight: 600;
}
.urgent-count {
  background: #fff1df;
  color: #b58238;
  border-radius: 5px;
  padding: 4px 7px;
}
.relationship-note {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  font-size: 10px;
  color: #94a185;
  margin-top: 25px;
}
.relationship-note span {
  padding: 7px 10px;
  background: #eff2e9;
  border-radius: 5px;
}
.relationship-note b {
  padding: 7px 0;
  font-weight: 400;
}
@media (max-width: 760px) {
  .teams-grid {
    grid-template-columns: 1fr;
  }
  th,
  td {
    padding: 12px;
  }
  table {
    min-width: 540px;
  }
  .workload-panel header {
    padding: 18px;
  }
}
</style>
