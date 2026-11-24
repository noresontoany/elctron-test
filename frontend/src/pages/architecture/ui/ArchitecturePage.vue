<script setup lang="ts">
import { lastTxid } from '@/entities/order'
import { ArrowDown, ArrowRight, Database, Workflow, ShieldCheck, Code2 } from '@lucide/vue'
</script>
<template>
  <section class="page-heading">
    <div>
      <div class="eyebrow">ПОД КАПОТОМ</div>
      <h1>Простой интерфейс.<br />Интересная архитектура<span class="heading-dot">.</span></h1>
      <p>Два пути данных: запись через API, чтение через поток изменений.</p>
    </div>
    <Workflow :size="44" stroke-width="1" />
  </section>
  <div class="architecture-grid">
    <section class="architecture-diagram">
      <span class="eyebrow">БРАУЗЕР</span>
      <div class="diagram-node">
        <Code2 :size="23" />
        <div>
          <strong>Nuxt 4 · shadcn-vue</strong><span>Vue Composition API · TypeScript · FSD</span>
        </div>
      </div>
      <ArrowDown class="diagram-arrow" />
      <div class="diagram-node accent-node">
        <Database :size="23" />
        <div>
          <strong>TanStack DB</strong
          ><span>4 коллекции · live joins · агрегаты · optimistic writes</span>
        </div>
      </div>
      <div class="diagram-branches">
        <span>↑ SharedWorker · изменения</span><span>↓ команды + txid ↑</span>
      </div>
      <div class="diagram-pair">
        <div class="diagram-node">
          <ShieldCheck :size="20" />
          <div><strong>Electric Proxy</strong><span>Сессия · фильтр мастерской</span></div>
        </div>
        <div class="diagram-node">
          <Code2 :size="20" />
          <div><strong>FastAPI</strong><span>DTO → Action → Task → Repository</span></div>
        </div>
      </div>
      <div class="diagram-branches"><span>↑ Electric SQL</span><span>↓ SQLAlchemy</span></div>
      <div class="diagram-node postgres-node">
        <Database :size="23" />
        <div>
          <strong>PostgreSQL 18</strong
          ><span>Единый источник данных · WAL logical replication</span>
        </div>
      </div>
    </section>
    <section class="architecture-notes">
      <h2>Попробуйте сами</h2>
      <ol>
        <li>
          <strong>Измените состав бригады</strong>
          <p>
            Под Ириной добавьте Марию в другую бригаду. Во вкладке Марии её очередь изменится через
            join членства; строки заказов останутся прежними.
          </p>
        </li>
        <li>
          <strong>Переведите заказ в работу</strong>
          <p>
            Карточка сразу переместится в TanStack DB. API проверит данные, сохранит их и вернёт
            txid. Worker дождётся этого txid в потоке и подтвердит запись вкладке.
          </p>
        </li>
        <li>
          <strong>Переименуйте мастера</strong>
          <p>
            На карточках хранится ссылка на пользователя. Изменение имени обновит связанные карточки
            и архив через live join. Загрузка считается через groupBy, count и sum.
          </p>
        </li>
      </ol>
      <div class="txid-box">
        <span>Последняя запись в этой вкладке</span
        ><code>{{ lastTxid ? `txid: ${lastTxid}` : 'Измените любой заказ' }}</code>
      </div>
    </section>
  </div>
  <div class="architecture-details">
    <article>
      <h3>Backend · PORTO</h3>
      <p>
        Python 3.12, FastAPI, async SQLAlchemy, Pydantic, Alembic. ORM → Resource DTO. Доменные
        tasks обращаются к repositories. Версия записи защищает от потерянных изменений.
      </p>
      <code>backend/src/containers/order/</code>
    </article>
    <article>
      <h3>Frontend · FSD</h3>
      <p>
        app → pages → widgets → features → entities → shared. DTO в snake_case, модель интерфейса в
        camelCase. Маппер преобразует даты и ограничивает поля записи.
      </p>
      <code>frontend/src/</code>
    </article>
    <article>
      <h3>Изолированное окружение</h3>
      <p>
        Свой Docker Compose, сеть и volumes. Caddy публикует HTTPS на localhost:8447 и HTTP на 8097.
        PostgreSQL и Electric снаружи недоступны. Сессия демонстрационная — без пароля.
      </p>
      <a href="/api/docs" target="_blank" rel="noreferrer"
        >Открыть Swagger<ArrowRight :size="14"
      /></a>
    </article>
  </div>
</template>

<style scoped>
.architecture-grid {
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  gap: 25px;
}
.architecture-diagram,
.architecture-notes {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  padding: 25px;
}
.diagram-node {
  border: 1px solid #e0e6d7;
  border-radius: 9px;
  padding: 17px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8faf4;
}
.diagram-node strong {
  display: block;
  font-size: 12px;
}
.diagram-node span {
  display: block;
  font-size: 9px;
  color: #8a997c;
  margin-top: 5px;
}
.diagram-node > svg {
  color: #8da477;
  flex-shrink: 0;
}
.architecture-diagram > .eyebrow {
  display: block;
  margin-bottom: 15px;
}
.diagram-arrow {
  display: block;
  margin: 10px auto;
  color: #97ac83;
}
.accent-node {
  background: #eaf2de;
  border-color: #d8e7c6;
}
.diagram-branches {
  display: flex;
  justify-content: space-around;
  padding: 14px 0;
  font-size: 9px;
  color: #899e75;
}
.diagram-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.diagram-pair .diagram-node {
  flex-direction: column;
  align-items: flex-start;
  padding: 14px;
}
.postgres-node {
  background: #2e5141;
  color: #f0f5e9;
  border-color: #2e5141;
}
.postgres-node span {
  color: #aec399;
}
.architecture-notes h2 {
  font-size: 18px;
  margin: 0 0 25px;
  font-weight: 500;
}
.architecture-notes ol {
  list-style: none;
  counter-reset: steps;
  padding: 0;
  margin: 0;
}
.architecture-notes li {
  position: relative;
  padding-left: 34px;
  margin: 24px 0;
  counter-increment: steps;
}
.architecture-notes li:before {
  content: counter(steps);
  position: absolute;
  left: 0;
  top: -3px;
  background: #eaf0e1;
  color: #8c9f77;
  width: 23px;
  height: 23px;
  border-radius: 50%;
  font-size: 11px;
  display: grid;
  place-items: center;
}
.architecture-notes strong {
  font-size: 12px;
}
.architecture-notes p {
  font-size: 11px;
  line-height: 1.8;
  color: #8c9881;
  margin-top: 7px;
}
.txid-box {
  border: 1px dashed #d6dfcb;
  border-radius: 8px;
  padding: 16px;
  margin-top: 30px;
}
.txid-box span {
  display: block;
  font-size: 10px;
  color: #91a17f;
  margin-bottom: 8px;
}
.txid-box code {
  font-size: 13px;
  color: #5b7c43;
}
.architecture-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 25px;
  margin-top: 25px;
}
.architecture-details article {
  border-top: 1px solid var(--border);
  padding: 20px 0;
}
.architecture-details h3 {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 10px;
}
.architecture-details p {
  font-size: 11px;
  line-height: 1.8;
  color: #8b9880;
  margin-bottom: 15px;
}
.architecture-details code {
  font-size: 10px;
  background: #eaf0e1;
  padding: 5px 8px;
  border-radius: 5px;
  color: #7a9264;
}
.architecture-details a {
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #6c8558;
}
@media (max-width: 980px) {
  .architecture-grid {
    grid-template-columns: 1fr;
  }
  .architecture-details {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
@media (max-width: 640px) {
  .architecture-diagram,
  .architecture-notes {
    padding: 18px;
  }
  .diagram-node {
    padding: 13px;
  }
  .diagram-node span {
    line-height: 1.5;
  }
  .diagram-pair {
    gap: 7px;
  }
  .diagram-pair .diagram-node {
    padding: 11px;
  }
  .diagram-node strong {
    font-size: 11px;
  }
}
</style>
