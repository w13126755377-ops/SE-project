<script setup lang="ts">
import { computed } from 'vue'
import type { Score, Profile } from '../../api/scoring'
import FlipText from '../../components/FlipText.vue'
const props = defineProps<{
  score: Score
  profile?: Profile
  loading: boolean
  error: string
}>()
defineEmits<{ close: []; rules: [] }>()
const dim = (name: string) => props.profile?.dimensions[name]
const facts = computed(() => [
  ['成立年份', dim('基础信息')?.founded_year],
  ['员工规模', dim('经营规模')?.employee_scale],
  ['营收规模', dim('经营规模')?.revenue_scale],
  ['所在地', dim('地域布局')?.region],
])
const tech = computed(
  () =>
    dim('技术/资质')?.tech_qualifications as
      | { 专利数?: number; 资质?: string[] }
      | undefined,
)
function readable(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (Array.isArray(value))
    return value.map(readable).filter(Boolean).join('、')
  if (typeof value === 'object')
    return Object.entries(value)
      .map(([key, v]) => `${key}：${readable(v)}`)
      .join('；')
  return String(value)
}
const locations = computed(() => {
  let value = dim('地域布局')?.production_bases
  if (typeof value === 'string') {
    try {
      value = JSON.parse(value)
    } catch {}
  }
  return (Array.isArray(value) ? value : [value]).map(readable).filter(Boolean)
})
const events = computed(() => {
  const raw = dim('投资动向')?.investment_events
  return Array.isArray(raw) ? (raw as Record<string, unknown>[]) : []
})
const sources = computed(() => [
  ...new Set(
    props.score.dimensions
      .map((d) => d.source_url)
      .filter((url): url is string => !!url && /^https?:\/\//.test(url)),
  ),
])
function eventTitle(event: Record<string, unknown>) {
  return (
    readable(event['事件']) ||
    [event['轮次'], event['金额']].map(readable).filter(Boolean).join(' · ') ||
    '投资记录'
  )
}
</script>
<template>
  <article class="enterprise-detail">
    <div class="detail-actions">
      <button
        class="close-detail"
        aria-label="关闭企业详情"
        @click="$emit('close')"
      >
        ×</button
      ><button class="rule-entry motion-trigger" @click="$emit('rules')">
        <FlipText text="评分规则" />
      </button>
    </div>
    <header class="overview">
      <div>
        <p class="eyebrow">{{ score.target_segment }}</p>
        <h1>{{ score.name }}</h1>
      </div>
      <div class="total">
        <strong>{{ score.total_score.toFixed(1) }}</strong>
        <p v-if="score.score_kind !== 'complete'">资料待补充 · 已有证据得分</p>
      </div>
    </header>
    <p v-if="loading" role="status" class="muted">正在读取企业画像…</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <dl class="facts">
      <div v-for="[label, value] in facts" :key="String(label)">
        <dt>{{ label }}</dt>
        <dd>{{ value || '待补充' }}</dd>
      </div>
    </dl>
    <section class="detail-section">
      <h2>评分构成</h2>
      <p v-if="score.score_kind !== 'complete'" class="coverage-note">
        已评权重 {{ Math.round(score.coverage * 100) }}% · 分数范围
        {{ score.total_score.toFixed(1) }}–{{
          score.score_upper_bound.toFixed(1)
        }}
      </p>
      <div class="score-chart">
        <div class="chart-labels">
          <span>分项得分</span><span>权重</span><span>贡献分</span>
        </div>
        <div v-for="d in score.dimensions" :key="d.key" class="chart-row">
          <span class="dimension-name">{{ d.label }}</span>
          <div class="track">
            <div
              v-if="d.score !== null"
              class="bar"
              :style="{ width: `${d.score}%` }"
            ></div>
            <span class="bar-value">{{ d.score ?? '待补充' }}</span>
          </div>
          <span class="weight">{{ Math.round(d.weight * 100) }}%</span
          ><span class="contribution">{{ d.contribution ?? '—' }}</span>
        </div>
        <div class="chart-axis">
          <span>0</span><span>25</span><span>50</span><span>75</span
          ><span>100</span>
        </div>
      </div>
      <ul v-if="score.warnings.length" class="warnings">
        <li v-for="warning in score.warnings" :key="warning">{{ warning }}</li>
      </ul>
    </section>
    <section class="detail-section">
      <h2>技术资质</h2>
      <div class="technical">
        <div>
          <p class="muted">已收录专利数</p>
          <strong>{{ tech?.专利数 ?? '—' }}</strong>
        </div>
        <ul v-if="tech?.资质?.length">
          <li v-for="q in tech.资质" :key="q">{{ q }}</li>
        </ul>
        <p v-else class="muted">资质资料待补充</p>
      </div>
    </section>
    <section class="detail-section">
      <h2>投资动向</h2>
      <ol v-if="events.length" class="timeline">
        <li v-for="(event, i) in events" :key="i">
          <time>{{ readable(event['时间']) || '日期待补充' }}</time>
          <div class="event-content">
            <span class="event-marker" aria-hidden="true"></span>
            <h3>{{ eventTitle(event) }}</h3>
            <p
              v-if="event['事件'] && (event['轮次'] || event['金额'])"
              class="muted"
            >
              {{
                [event['轮次'], event['金额']]
                  .map(readable)
                  .filter(Boolean)
                  .join(' · ')
              }}
            </p>
            <p v-if="event['投资方']" class="muted">
              投资方：{{ readable(event['投资方']) }}
            </p>
          </div>
        </li>
      </ol>
      <p v-else class="muted">暂无已收录的投资事件</p>
    </section>
    <section v-if="locations.length" class="detail-section">
      <h2>地域布局</h2>
      <ul class="location-list">
        <li v-for="(city, i) in locations" :key="i">{{ city }}</li>
      </ul>
    </section>
    <section class="detail-section">
      <h2>资料来源</h2>
      <a
        v-for="(url, i) in sources"
        :key="url"
        :href="url"
        target="_blank"
        rel="noopener noreferrer"
        class="source-link"
        >企业公开资料 {{ sources.length > 1 ? i + 1 : '' }} <span>↗</span></a
      >
      <p v-if="!sources.length" class="muted">来源链接待补充</p>
    </section>
  </article>
</template>
<style scoped>
.enterprise-detail {
  max-width: 1280px;
  margin: auto;
  padding: 116px 64px 120px;
  color: white;
  min-height: 100svh;
}
.detail-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 64px;
}
.close-detail {
  background: #343940;
  color: white;
  width: 40px;
  height: 40px;
  font-size: 28px;
}
.rule-entry {
  background: var(--color-blue);
  color: white;
  padding: 12px 24px;
  font-size: 14px;
}
.overview {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 56px;
  align-items: center;
}
.eyebrow {
  color: var(--color-muted);
  font-size: 14px;
  margin-bottom: 20px;
}
.overview h1 {
  font-size: clamp(28px, 3vw, 42px);
  font-weight: 400;
  line-height: 1.5;
  max-width: 750px;
}
.total {
  text-align: right;
}
.total strong {
  font-size: 76px;
  font-weight: 400;
  color: var(--color-blue);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}
.total p {
  color: var(--color-muted);
  font-size: 12px;
  margin-top: 12px;
}
.facts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 32px;
  margin: 64px 0 0;
}
.facts dt {
  font-size: 13px;
  color: var(--color-muted);
}
.facts dd {
  font-size: 21px;
  margin: 14px 0 0;
  line-height: 1.6;
}
.detail-section {
  border-top: 1px dotted #565e69;
  margin-top: 80px;
  padding-top: 48px;
}
.detail-section h2 {
  font-size: 26px;
  font-weight: 400;
  margin-bottom: 36px;
}
.coverage-note {
  font-size: 13px;
  color: var(--color-muted);
  margin: -16px 0 28px;
}
.score-chart {
  background: #131518;
  padding: 36px 32px 28px;
}
.chart-labels {
  display: grid;
  grid-template-columns: 1fr 64px 68px;
  gap: 24px;
  color: var(--color-muted);
  font-size: 12px;
  margin-bottom: 24px;
  text-align: right;
}
.chart-labels span:first-child {
  text-align: left;
}
.chart-row {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr) 64px 68px;
  align-items: center;
  gap: 24px;
  margin: 26px 0;
  font-size: 14px;
}
.dimension-name {
  line-height: 1.6;
}
.track {
  height: 28px;
  background: repeating-linear-gradient(
    to right,
    transparent 0,
    transparent calc(25% - 1px),
    #343940 25%
  );
  position: relative;
}
.bar {
  height: 12px;
  position: absolute;
  top: 8px;
  background: var(--color-blue);
  transform-origin: left;
  animation: grow 0.9s var(--ease-out) both;
}
.bar-value {
  position: relative;
  float: right;
  padding: 4px;
  background: #131518;
  min-width: 28px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.weight,
.contribution {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.chart-axis {
  display: flex;
  justify-content: space-between;
  margin: 24px 180px 0 174px;
  color: #929aa6;
  font: 12px var(--font-mono);
}
.technical {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 64px;
}
.technical strong {
  display: block;
  font-size: 56px;
  font-weight: 400;
  margin-top: 16px;
}
.technical ul {
  border-left: 1px solid #4b515b;
  padding-left: 48px;
  list-style: none;
  line-height: 2.4;
}
.muted {
  color: var(--color-muted);
  line-height: 1.8;
}
.timeline {
  list-style: none;
  padding: 0;
  margin: 0;
}
.timeline li {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr);
  gap: 32px;
  padding: 12px 0 36px;
}
.timeline time {
  font: 14px var(--font-mono);
  color: var(--color-muted);
  padding-top: 5px;
  line-height: 1.8;
}
.event-content {
  position: relative;
  padding: 0 0 12px 40px;
  min-height: 80px;
}
.event-content::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 15px;
  bottom: 0;
  width: 1px;
  background: #505865;
}
.event-marker {
  position: absolute;
  left: 0;
  top: 8px;
  width: 9px;
  height: 9px;
  background: var(--color-blue);
  z-index: 1;
}
.event-content h3 {
  font-size: 18px;
  font-weight: 400;
  line-height: 1.9;
  max-width: 700px;
  overflow-wrap: anywhere;
}
.event-content p {
  margin-top: 16px;
  font-size: 15px;
  line-height: 1.9;
}
.location-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 16px 32px;
}
.location-list li {
  font-size: 18px;
  line-height: 1.8;
}
.warnings {
  font-size: 13px;
  line-height: 1.8;
  color: var(--color-muted);
  padding-left: 20px;
  margin-top: 24px;
}
.source-link {
  display: flex;
  justify-content: space-between;
  padding: 20px 0;
  border-bottom: 1px solid #343940;
  font-size: 15px;
}
.source-link:hover {
  color: var(--color-blue);
}
@keyframes grow {
  from {
    transform: scaleX(0);
  }
  to {
    transform: scaleX(1);
  }
}
@media (max-width: 900px) {
  .enterprise-detail {
    padding: 110px 28px 80px;
  }
  .overview {
    gap: 24px;
  }
  .total strong {
    font-size: 56px;
  }
  .chart-row {
    grid-template-columns: 120px minmax(0, 1fr) 40px 44px;
    gap: 12px;
  }
  .chart-axis {
    margin-left: 132px;
    margin-right: 108px;
  }
  .score-chart {
    padding: 24px 16px;
  }
  .chart-labels {
    grid-template-columns: 1fr 40px 44px;
    gap: 12px;
  }
}
@media (max-width: 600px) {
  .overview {
    grid-template-columns: 1fr;
  }
  .total {
    text-align: left;
  }
  .facts {
    grid-template-columns: 1fr 1fr;
    margin-top: 40px;
  }
  .detail-actions {
    margin-bottom: 40px;
  }
  .detail-section {
    margin-top: 64px;
    padding-top: 36px;
  }
  .technical {
    gap: 24px;
    grid-template-columns: 1fr;
  }
  .technical ul {
    padding-left: 24px;
  }
  .timeline li {
    grid-template-columns: 82px minmax(0, 1fr);
    gap: 16px;
  }
  .timeline time {
    font-size: 12px;
  }
  .event-content {
    padding-left: 26px;
  }
  .event-content h3 {
    font-size: 16px;
  }
  .location-list {
    gap: 12px 24px;
  }
  .location-list li {
    font-size: 16px;
  }
  .chart-row {
    grid-template-columns: 78px minmax(0, 1fr) 28px 32px;
    gap: 8px;
    font-size: 11px;
  }
  .chart-labels {
    grid-template-columns: 1fr 28px 32px;
    gap: 8px;
    font-size: 10px;
  }
  .chart-axis {
    margin-left: 86px;
    margin-right: 76px;
  }
  .dimension-name {
    font-size: 12px;
  }
  .score-chart {
    padding: 20px 12px;
  }
  .bar-value {
    font-size: 10px;
    min-width: 24px;
  }
  .detail-section h2 {
    font-size: 24px;
  }
  .facts dd {
    font-size: 18px;
  }
}
</style>
