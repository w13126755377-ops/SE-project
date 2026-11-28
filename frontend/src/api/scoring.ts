import { request } from './client'
export const segments = [
  '芯片设计',
  '晶圆制造',
  '半导体材料',
  '半导体设备',
  '先进封装',
]
export interface Dimension {
  key: string
  label: string
  score: number | null
  weight: number
  contribution: number | null
  evidence: Record<string, unknown>
  reason: string
  source_url?: string
}
export interface Score {
  enterprise_id: number
  name: string
  total_score: number
  score_upper_bound: number
  coverage: number
  score_kind: string
  dimensions: Dimension[]
  missing_dimensions: string[]
  warnings: string[]
  target_segment: string
  rule_version: string
  as_of: string
}
export interface Profile {
  enterprise_id: number
  name: string
  dimensions: Record<string, Record<string, unknown> | null>
  missing_dims: string[]
}
export interface Rules {
  version: string
  label: string
  weights: Record<string, number>
  employee_bands: number[][]
  qualification_rules: [string, number][]
  activity_month_bands: number[][]
}
export async function searchScores(
  segment: string,
  keyword: string,
  signal: AbortSignal,
) {
  const groups = await Promise.all(
    (segment ? [segment] : segments).map(async (target) => {
      const q = new URLSearchParams({
        target_segment: target,
        keyword,
        page_size: '100',
      })
      return (
        await request<{ items: Score[] }>(`/scoring/rankings?${q}`, { signal })
      ).items
    }),
  )
  return groups
    .flat()
    .sort(
      (a, b) =>
        b.total_score - a.total_score ||
        b.coverage - a.coverage ||
        a.enterprise_id - b.enterprise_id,
    )
}
export const getProfile = (id: number, signal: AbortSignal) =>
  request<Profile>(`/enterprises/${id}/profile`, { signal })
export const getRules = (signal: AbortSignal) =>
  request<Rules>('/scoring/rules', { signal })
