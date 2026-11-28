<script setup lang="ts">
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  searchScores,
  getProfile,
  getRules,
  segments,
  type Score,
  type Profile,
  type Rules,
} from '../../api/scoring'
import UiIcon from '../../components/UiIcon.vue'
import FlipText from '../../components/FlipText.vue'
import SpecialistDetail from './SpecialistDetail.vue'
import {
  enterpriseLogos,
  darkLogoBackgrounds,
  transparentLogoBackgrounds,
  smallLogoMarks,
} from '../../data/enterpriseLogos'
gsap.registerPlugin(ScrollTrigger)
const root = ref<HTMLElement>(),
  results = ref<HTMLElement>(),
  input = ref<HTMLInputElement>(),
  rulesDialog = ref<HTMLDialogElement>()
const keyword = ref(''),
  segment = ref(''),
  items = ref<Score[]>([]),
  loading = ref(false),
  searched = ref(false),
  error = ref('')
const selected = ref<Score>(),
  profile = ref<Profile>(),
  detailError = ref(''),
  detailLoading = ref(false),
  rules = ref<Rules>(),
  rulesError = ref('')
let searchAbort: AbortController | undefined,
  detailAbort: AbortController | undefined,
  ruleAbort: AbortController | undefined,
  ctx: gsap.Context | undefined,
  observer: IntersectionObserver | undefined
let savedScroll = 0,
  selectedButton: HTMLElement | undefined,
  disposed = false
const failedLogos = ref(new Set<string>())
function logo(name: string) {
  return failedLogos.value.has(name) ? undefined : enterpriseLogos[name]
}
function shortName(name: string) {
  return name.replace(/股份有限公司|有限责任公司|有限公司|\(.*?\)|（.*?）/g, '')
}
async function search(scroll = true) {
  searchAbort?.abort()
  const abort = (searchAbort = new AbortController())
  loading.value = true
  error.value = ''
  searched.value = true
  try {
    const data = await searchScores(
      segment.value,
      keyword.value.trim(),
      abort.signal,
    )
    if (!abort.signal.aborted) {
      items.value = data
      await nextTick()
      revealCards()
      if (scroll)
        results.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  } catch (e) {
    if (!abort.signal.aborted) {
      items.value = []
      error.value = e instanceof Error ? e.message : '检索失败'
      if (scroll) {
        await nextTick()
        results.value?.scrollIntoView({ behavior: 'smooth' })
      }
    }
  } finally {
    if (!abort.signal.aborted) loading.value = false
  }
}
function revealCards() {
  observer?.disconnect()
  const cards = root.value?.querySelectorAll<HTMLElement>('.company-card') || []
  gsap.set(cards, { y: 52, opacity: 0 })
  observer = new IntersectionObserver(
    (entries) => {
      entries
        .filter((entry) => entry.isIntersecting)
        .forEach((entry, index) => {
          gsap.to(entry.target, {
            y: 0,
            opacity: 1,
            duration: 0.9,
            delay: index * 0.07,
            ease: 'power3.out',
            clearProps: 'transform,opacity',
          })
          observer?.unobserve(entry.target)
        })
    },
    { threshold: 0.12 },
  )
  cards.forEach((card) => observer!.observe(card))
}
function hoverCard(event: Event, active: boolean) {
  const card = event.currentTarget as HTMLElement,
    line = card.querySelector('.hover-progress')
  if (!line) return
  if (active) {
    gsap.set(line, { opacity: 1 })
    gsap.fromTo(
      line,
      { width: '10%' },
      { width: '100%', duration: 0.45, overwrite: true },
    )
  } else
    gsap.to(line, {
      width: '0%',
      duration: 0.45,
      overwrite: true,
      onComplete: () => {
        gsap.set(line, { opacity: 0 })
      },
    })
}
async function openDetail(item: Score, event: MouseEvent) {
  savedScroll = window.scrollY
  selectedButton = event.currentTarget as HTMLElement
  detailAbort?.abort()
  const abort = (detailAbort = new AbortController())
  selected.value = item
  profile.value = undefined
  detailError.value = ''
  detailLoading.value = true
  await nextTick()
  window.scrollTo({ top: 0 })
  try {
    const data = await getProfile(item.enterprise_id, abort.signal)
    if (!abort.signal.aborted) profile.value = data
  } catch (e) {
    if (!abort.signal.aborted)
      detailError.value = e instanceof Error ? e.message : '资料读取失败'
  } finally {
    if (!abort.signal.aborted) detailLoading.value = false
  }
}
async function closeDetail() {
  detailAbort?.abort()
  selected.value = undefined
  await nextTick()
  window.scrollTo({ top: savedScroll })
  selectedButton?.focus({ preventScroll: true })
  ScrollTrigger.refresh()
}
async function showRules() {
  rulesDialog.value?.showModal()
  if (rules.value) return
  ruleAbort?.abort()
  const abort = (ruleAbort = new AbortController())
  rulesError.value = ''
  try {
    rules.value = await getRules(abort.signal)
  } catch (e) {
    if (!abort.signal.aborted)
      rulesError.value = e instanceof Error ? e.message : '读取失败'
  }
}
function shortcut(e: KeyboardEvent) {
  if (
    e.key === '/' &&
    !rulesDialog.value?.open &&
    !selected.value &&
    !(e.target instanceof HTMLInputElement) &&
    !(e.target instanceof HTMLSelectElement)
  ) {
    e.preventDefault()
    input.value?.focus()
  }
}
onMounted(async () => {
  await nextTick()
  if (disposed) return
  ctx = gsap.context(() => {
    gsap.fromTo(
      '.search-composition',
      { y: 20, opacity: 0 },
      { y: 0, opacity: 1, duration: 1, ease: 'expo.out' },
    )
    gsap.to(root.value!, {
      backgroundColor: '#000',
      ease: 'none',
      scrollTrigger: {
        trigger: '.search-stage',
        start: '40% top',
        end: '65% top',
        scrub: true,
      },
    })
  }, root.value)
  window.addEventListener('keydown', shortcut)
  search(false)
})
onBeforeUnmount(() => {
  disposed = true
  searchAbort?.abort()
  detailAbort?.abort()
  ruleAbort?.abort()
  observer?.disconnect()
  if (root.value)
    gsap.killTweensOf(root.value.querySelectorAll('.company-card'))
  ctx?.revert()
  window.removeEventListener('keydown', shortcut)
})
</script>

<template>
  <div ref="root" class="specialist-page" :class="{ 'detail-open': selected }">
    <div v-show="!selected">
      <section class="search-stage" aria-label="检索企业">
        <div class="search-composition">
          <form class="search-form" @submit.prevent="search()">
            <div class="input-wrap">
              <svg
                class="search-glass"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <circle
                  cx="10.5"
                  cy="10.5"
                  r="7.5"
                  stroke="currentColor"
                  stroke-width="1.6"
                />
                <path
                  d="m16 16 5 5"
                  stroke="currentColor"
                  stroke-width="1.6"
                /></svg
              ><input
                ref="input"
                v-model="keyword"
                placeholder="搜索企业"
                aria-label="搜索企业名称或行业"
              /><kbd>/</kbd>
            </div>
            <button
              class="search-submit"
              type="submit"
              :disabled="loading"
              aria-label="检索企业"
            >
              <UiIcon name="arrow" />
            </button>
            <button
              class="rules-button motion-trigger"
              type="button"
              @click="showRules"
            >
              <FlipText text="评分规则" />
            </button>
          </form>
          <nav class="segment-nav" aria-label="产业环节">
            <button
              v-for="option in ['', ...segments]"
              :key="option"
              type="button"
              :aria-pressed="segment === option"
              @click="segment = option"
            >
              {{ option || '全部环节' }}
            </button>
          </nav>
        </div>
        <button
          class="browse-down"
          aria-label="浏览企业结果"
          @click="results?.scrollIntoView({ behavior: 'smooth' })"
        >
          ↓
        </button>
      </section>
      <section
        ref="results"
        class="results-stage"
        aria-label="企业检索结果"
        :aria-busy="loading"
      >
        <p v-if="loading" class="result-message" role="status">正在检索企业…</p>
        <div v-else-if="error" class="result-message" role="alert">
          <p>{{ error }}</p>
          <button @click="search(false)">重新检索 →</button>
          <p class="muted">请确认数据服务已启动。</p>
        </div>
        <p v-else-if="searched && !items.length" class="result-message">
          没有找到匹配企业，请返回上方调整关键词或环节。
        </p>
        <div v-else class="company-grid">
          <article
            v-for="item in items"
            :key="item.enterprise_id"
            class="company-card"
            @mouseenter="hoverCard($event, true)"
            @mouseleave="hoverCard($event, false)"
            @focusin="hoverCard($event, true)"
            @focusout="hoverCard($event, false)"
          >
            <span class="hover-progress" aria-hidden="true"></span>
            <div class="card-heading">
              <h2>{{ shortName(item.name) }}</h2>
              <button
                class="card-arrow"
                :aria-label="`查看${item.name}详情`"
                @click="openDetail(item, $event)"
              >
                <UiIcon name="arrow" />
              </button>
            </div>
            <p class="card-description">{{ item.target_segment }}</p>
            <div class="brand-panel">
              <img
                v-if="logo(item.name)"
                :src="logo(item.name)"
                :class="{
                  'logo-dark': darkLogoBackgrounds.has(item.name),
                  'logo-transparent': transparentLogoBackgrounds.has(item.name),
                  'logo-small': smallLogoMarks.has(item.name),
                }"
                :alt="item.name"
                @error="failedLogos.add(item.name)"
              /><span v-else class="brand-fallback">{{
                shortName(item.name)
              }}</span>
              <div class="score-corner">
                <strong>{{ item.total_score.toFixed(1) }}</strong
                ><span v-if="item.score_kind !== 'complete'">资料待补充</span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
    <SpecialistDetail
      v-if="selected"
      :score="selected"
      :profile="profile"
      :loading="detailLoading"
      :error="detailError"
      @close="closeDetail"
      @rules="showRules"
    />
    <dialog
      ref="rulesDialog"
      class="rules-dialog"
      aria-labelledby="rules-title"
    >
      <button
        class="dialog-close"
        aria-label="关闭评分规则"
        @click="rulesDialog?.close()"
      >
        ×
      </button>
      <header class="rules-intro">
        <span class="rules-eyebrow"
          >评分方法 · {{ rules?.version || 'D4' }}</span
        >
        <h2 id="rules-title">评分方法说明</h2>
        <p>
          本系统采用加权求和模型（WSM），对企业的目标环节匹配、员工规模、技术资质及投资事件时效进行评价，并依据综合得分确定考察优先级。
        </p>
      </header>
      <p v-if="rulesError" role="alert">
        {{ rulesError }} <button @click="showRules">重试</button>
      </p>
      <template v-else-if="rules">
        <section class="rule-section">
          <h3>评价指标与权重</h3>
          <p>各指标依据预设规则转换为 0–100 分，权重合计为 100%。</p>
          <dl class="weight-list">
            <div v-for="(weight, key) in rules.weights" :key="key">
              <dt>
                {{
                  {
                    segment: '目标环节匹配',
                    scale: '员工规模',
                    qualification: '技术资质',
                    activity: '投资事件时效',
                  }[key]
                }}
              </dt>
              <dd>{{ Math.round(weight * 100) }}<span>%</span></dd>
            </div>
          </dl>
        </section>
        <section class="rule-section">
          <h3>指标赋分规则</h3>
          <div class="rule-explanation">
            <h4>目标环节匹配</h4>
            <p>
              依据企业画像中的产业链环节字段进行精确匹配。一致赋 100
              分，不一致赋 0
              分。检索结果已按目标环节筛选，因此同一结果集内该项得分一致。
            </p>
            <h4>员工规模</h4>
            <p>
              依据企业画像中的员工规模区间，以区间下界作为分档依据；开放区间同样采用下界。各档位及对应分值见下表。
            </p>
            <h4>技术资质</h4>
            <p>
              依据已收录的技术资质名称匹配对应档位。同一企业存在多项有效匹配时，取最高档位分值。专利数量单独展示，不参与本项计算。
            </p>
            <h4>投资事件时效</h4>
            <p>
              选取日期有效且不晚于评估日期的最近一条投资事件，按年月差计算间隔月份，再匹配时效档位。事件日期缺失或无法识别时，该事件不参与计算。
            </p>
          </div>
          <details class="score-bands">
            <summary>查看分档标准 <span>＋</span></summary>
            <div class="band-group">
              <h4>员工规模</h4>
              <p>以员工规模区间下界匹配下表。</p>
              <table>
                <thead>
                  <tr>
                    <th>起始人数</th>
                    <th>分项得分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="([limit, score], i) in rules.employee_bands"
                    :key="i"
                  >
                    <td>
                      {{ i === 0 ? '0' : rules.employee_bands[i - 1]![0]! + 1
                      }}{{ limit! > 100000 ? ' 人及以上' : `–${limit} 人` }}
                    </td>
                    <td>{{ score }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="band-group">
              <h4>技术资质</h4>
              <table>
                <thead>
                  <tr>
                    <th>资质类型</th>
                    <th>分项得分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="[name, score] in rules.qualification_rules"
                    :key="name"
                  >
                    <td>{{ name }}</td>
                    <td>{{ score }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="band-group">
              <h4>投资事件时效</h4>
              <table>
                <thead>
                  <tr>
                    <th>距评估日期</th>
                    <th>分项得分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>12 个月以内</td>
                    <td>100</td>
                  </tr>
                  <tr>
                    <td>13–24 个月</td>
                    <td>75</td>
                  </tr>
                  <tr>
                    <td>25–36 个月</td>
                    <td>50</td>
                  </tr>
                  <tr>
                    <td>36 个月以上</td>
                    <td>25</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>
        </section>
        <section class="rule-section">
          <h3>综合得分计算</h3>
          <p>
            综合得分为各项指标得分与对应权重乘积之和，结果四舍五入保留两位小数。
          </p>
          <div class="scoring-formula">
            S = 0.40 × M + 0.20 × E + 0.25 × Q + 0.15 × I
          </div>
          <p>
            M、E、Q、I
            依次表示环节匹配、员工规模、技术资质和投资事件时效得分。分项贡献分等于该项得分与权重的乘积。
          </p>
        </section>
        <section class="rule-section">
          <h3>缺失值处理</h3>
          <p>
            无法取得或无法按规则识别的指标记为「待补充」，并保留原始权重。当前综合得分仅汇总可评价指标的贡献。
          </p>
          <p>
            分数下界为当前综合得分；上界为当前综合得分加上缺失指标全部取得满分时的贡献。该区间表示资料缺失带来的取值范围。已评权重为可评价指标权重之和。
          </p>
        </section>
        <section class="rule-section">
          <h3>排序与复算</h3>
          <p>
            企业依次按综合得分降序、已评权重降序、企业编号升序排列。先对全部匹配结果评分排序，再进行分页。
          </p>
          <p>
            评分记录保留目标环节、评估日期及规则版本。相同数据、规则版本与评估日期产生相同结果。
          </p>
        </section>
        <footer class="rules-footnote">
          <a
            href="https://github.com/Valdecy/pyDecision"
            target="_blank"
            rel="noopener noreferrer"
            >方法参考 · 加权求和 ↗</a
          >
        </footer>
      </template>
      <p v-else role="status">正在读取规则…</p>
    </dialog>
  </div>
</template>

<style scoped>
.specialist-page {
  background: #fafbfc;
}
.specialist-page.detail-open {
  background: #000 !important;
}
.search-stage {
  height: 100svh;
  min-height: 540px;
  background: transparent;
  position: relative;
  display: grid;
  place-items: center;
  color: #15171a;
}
.search-composition {
  width: min(900px, calc(100% - 64px));
}
.search-form {
  display: flex;
  gap: 12px;
  align-items: center;
}
.input-wrap {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 18px;
  background: white;
  border-radius: 12px;
  padding: 0 22px;
  height: 66px;
  border: 1px solid #eef0f4;
  box-shadow: 0 6px 30px #253a5510;
}
.input-wrap > svg {
  width: 24px;
  color: #9ba0a8;
  flex: none;
}
.input-wrap input {
  width: 100%;
  min-width: 0;
  background: none;
  border: 0;
  outline: 0;
  color: #17191d;
  font-size: 19px;
}
.input-wrap:has(input:focus-visible) {
  box-shadow:
    0 6px 30px #253a5510,
    0 0 0 1px #cbd2dd;
}
.input-wrap input::placeholder {
  color: #9b9fa8;
}
.input-wrap kbd {
  background: #f0f1f5;
  color: #747b88;
  border-radius: 5px;
  padding: 5px 12px;
}
.search-submit,
.rules-button {
  height: 56px;
  background: var(--color-blue);
  color: white;
  display: grid;
  place-items: center;
  transition:
    background 0.3s,
    transform 0.4s var(--ease-out);
}
.search-submit {
  width: 56px;
  flex: none;
}
.search-submit svg {
  width: 23px;
  transition: transform 0.4s var(--ease-out);
}
.search-submit:hover svg {
  transform: none;
}
.search-submit:disabled {
  opacity: 0.5;
}
.rules-button {
  padding: 0 24px;
  font-size: 14px;
  white-space: nowrap;
}
.segment-nav {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px 28px;
  margin: 30px auto 0;
}
.segment-nav button {
  position: relative;
  padding: 10px 0;
  background: none;
  color: #828994;
  font-size: 13px;
  line-height: 1.5;
  white-space: nowrap;
  transition: color 0.25s;
}
.segment-nav button::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 16px;
  height: 2px;
  background: var(--color-blue);
  transform: translateX(-50%) scaleX(0);
  transition: transform 0.3s var(--ease-out);
}
.segment-nav button[aria-pressed='true'] {
  color: var(--color-blue);
}
.segment-nav button[aria-pressed='true']::after {
  transform: translateX(-50%) scaleX(1);
}
.segment-nav button:hover {
  color: #4f73c5;
}
.browse-down {
  position: absolute;
  bottom: 48px;
  background: none;
  color: #7d838c;
  font-size: 24px;
  padding: 10px;
}
.results-stage {
  min-height: 100svh;
  padding: 120px max(32px, 4vw) 160px;
  scroll-margin-top: 0;
  background: transparent;
}
.company-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  column-gap: 40px;
  row-gap: 96px;
}
.company-card {
  position: relative;
  border-top: 1px dotted #626974;
  padding-top: 24px;
  transition:
    translate 0.4s var(--ease-out),
    border-color 0.3s;
  min-width: 0;
}
.company-card:hover,
.company-card:focus-within {
  translate: 0 -8px;
}
.hover-progress {
  position: absolute;
  left: 0;
  top: -1px;
  height: 3px;
  width: 0;
  opacity: 0;
  background: var(--color-blue);
  pointer-events: none;
}
.card-heading {
  min-height: 60px;
  display: flex;
  gap: 16px;
  align-items: start;
  justify-content: space-between;
}
.card-heading h2 {
  font-size: 19px;
  line-height: 1.55;
  font-weight: 400;
  overflow-wrap: anywhere;
}
.card-arrow {
  width: 34px;
  height: 34px;
  background: #343940;
  color: white;
  display: grid;
  place-items: center;
  flex: none;
  transition: background 0.3s;
}
.card-arrow svg {
  width: 16px;
  transition: transform 0.4s var(--ease-out);
}
.company-card:hover .card-arrow,
.company-card:focus-within .card-arrow {
  background: var(--color-blue);
}
.card-arrow:hover svg {
  transform: none;
}
.card-description {
  font-size: 14px;
  color: var(--color-muted);
  margin-top: 18px;
}
.brand-panel {
  margin-top: 44px;
  aspect-ratio: 1.05;
  background: #222529;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px 24px 84px;
  overflow: hidden;
}
.brand-panel img {
  width: min(100%, 210px);
  height: 160px;
  object-fit: contain;
  filter: grayscale(1) invert(1) contrast(3);
  mix-blend-mode: screen;
}
.brand-panel img.logo-dark {
  filter: grayscale(1) contrast(3);
}
.brand-panel img.logo-transparent {
  filter: brightness(0) invert(1);
}
.brand-panel img.logo-small {
  width: 76px;
  height: 76px;
}
.brand-fallback {
  font-size: clamp(18px, 1.7vw, 28px);
  text-align: center;
  line-height: 1.6;
  overflow-wrap: anywhere;
  color: #f1f2f5;
}
.score-corner {
  position: absolute;
  right: 20px;
  bottom: 18px;
  text-align: right;
}
.score-corner strong {
  font-size: clamp(36px, 3vw, 52px);
  color: var(--color-blue);
  font-weight: 400;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}
.score-corner span {
  display: block;
  margin-top: 6px;
  color: #a3aab5;
  font-size: 11px;
}
.result-message {
  color: #b5bac3;
  padding: 64px 0;
  font-size: 18px;
}
.result-message button {
  color: var(--color-blue);
  background: none;
  margin: 24px 0;
}
.muted {
  color: var(--color-muted);
}
.rules-dialog {
  background: #131518;
  color: white;
  border: 1px solid #343940;
  width: min(780px, calc(100% - 32px));
  max-height: 85svh;
  padding: 56px;
  margin: auto;
  line-height: 1.8;
}
.rules-dialog::backdrop {
  background: #000a;
  backdrop-filter: blur(6px);
}
.dialog-close {
  position: absolute;
  right: 18px;
  top: 12px;
  background: none;
  color: #b4bcc9;
  font-size: 28px;
}
.rules-eyebrow {
  display: block;
  color: var(--color-blue);
  font: 12px var(--font-mono);
  margin-bottom: 22px;
}
.rules-intro h2 {
  font-size: 28px;
  line-height: 1.5;
  letter-spacing: -0.02em;
  max-width: 440px;
  margin-bottom: 20px;
}
.rules-intro > p,
.rule-section > p {
  color: #a8b0bd;
  font-size: 14px;
  line-height: 1.95;
  max-width: 600px;
}
.rule-section {
  margin-top: 48px;
}
.rule-section h3 {
  position: relative;
  font-size: 18px;
  line-height: 1.6;
  padding-left: 24px;
  margin: 0 0 18px;
}
.rule-section h3::before {
  content: '';
  width: 9px;
  height: 9px;
  background: var(--color-blue);
  position: absolute;
  left: 0;
  top: 10px;
}
.rule-section > p + p {
  margin-top: 14px;
}
.weight-list {
  margin: 24px 0 0;
}
.weight-list > div {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #343940;
  padding: 16px 0;
}
.weight-list dt {
  font-size: 14px;
  color: #d7dce4;
}
.weight-list dd {
  margin: 0;
  color: var(--color-blue);
  font-size: 24px;
  font-variant-numeric: tabular-nums;
}
.weight-list dd span {
  font-size: 13px;
  margin-left: 3px;
}
.rule-explanation {
  padding-left: 24px;
}
.rule-explanation h4,
.band-group h4 {
  font-size: 14px;
  color: #e1e5ec;
  font-weight: 400;
  margin: 24px 0 8px;
}
.rule-explanation p,
.band-group p {
  font-size: 13px;
  color: #9ca6b6;
  line-height: 1.9;
}
.score-bands {
  margin-top: 28px;
  border-top: 1px solid #343940;
  border-bottom: 1px solid #343940;
}
.score-bands summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  list-style: none;
  cursor: pointer;
  padding: 18px 0;
  color: #c4ccda;
  font-size: 13px;
}
.score-bands summary::-webkit-details-marker {
  display: none;
}
.score-bands summary span {
  color: var(--color-blue);
  font-size: 20px;
  transition: rotate 0.25s;
}
.score-bands[open] summary span {
  rotate: 45deg;
}
.band-group {
  margin-bottom: 32px;
}
.band-group h4 {
  margin-top: 16px;
}
.band-group table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
  font-size: 13px;
}
.band-group th {
  text-align: left;
  color: #8792a3;
  font-weight: 400;
  font-size: 12px;
}
.band-group th:last-child,
.band-group td:last-child {
  text-align: right;
}
.band-group th,
.band-group td {
  padding: 10px 0;
  border-bottom: 1px solid #292f38;
}
.band-group td {
  color: #b6bfcd;
}
.scoring-formula {
  margin: 22px 0;
  padding: 20px 24px;
  border-left: 2px solid var(--color-blue);
  background: #191d24;
  color: #d9e2f2;
  font: 13px/1.9 var(--font-mono);
  overflow-wrap: anywhere;
}
.rules-footnote {
  border-top: 1px solid #343940;
  margin-top: 44px;
  padding-top: 22px;
  font-size: 12px;
  line-height: 1.9;
  color: #818d9f;
}
.rules-footnote a {
  display: inline-block;
  color: var(--color-blue);
  margin-top: 10px;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  clip-path: inset(50%);
  overflow: hidden;
}
@media (min-width: 1700px) {
  .company-grid {
    column-gap: 56px;
  }
}
@media (max-width: 1100px) {
  .company-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 64px 28px;
  }
}
@media (max-width: 800px) {
  .company-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 64px 24px;
  }
  .search-composition {
    width: calc(100% - 40px);
  }
  .rules-button {
    padding: 0 16px;
  }
  .results-stage {
    padding: 96px 24px;
  }
  .input-wrap {
    padding: 0 16px;
    gap: 12px;
  }
  .input-wrap input {
    font-size: 16px;
  }
  .input-wrap kbd {
    display: none;
  }
}
@media (max-width: 520px) {
  .search-form {
    flex-wrap: wrap;
    gap: 12px;
  }
  .input-wrap {
    flex-basis: calc(100% - 70px);
    height: 56px;
  }
  .rules-button {
    margin: 8px auto 0;
    height: 42px;
  }
  .segment-nav {
    gap: 6px 20px;
    margin-top: 22px;
  }
  .segment-nav button {
    font-size: 12px;
  }
  .company-grid {
    grid-template-columns: 1fr;
    row-gap: 72px;
  }
  .brand-panel {
    aspect-ratio: 1.25;
  }
  .score-corner strong {
    font-size: 48px;
  }
  .rules-dialog {
    padding: 40px 24px;
  }
  .search-stage {
    min-height: 560px;
  }
}
</style>
