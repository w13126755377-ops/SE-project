import { afterEach, expect, it, vi } from 'vitest'
import { searchScores, segments } from './scoring'
afterEach(() => vi.unstubAllGlobals())
it('combines all segments then sorts the full result, preserving query and cancellation', async () => {
  const signal = new AbortController().signal
  const fetcher = vi.fn(async (url: string) => {
    const u = new URL(url, 'http://local')
    const i = segments.indexOf(u.searchParams.get('target_segment')!)
    return new Response(
      JSON.stringify({
        code: 0,
        data: {
          items: [{ enterprise_id: i, total_score: 50 + i, coverage: 1 }],
        },
      }),
    )
  })
  vi.stubGlobal('fetch', fetcher)
  const result = await searchScores('', '联芸', signal)
  expect(result.map((r) => r.total_score)).toEqual([54, 53, 52, 51, 50])
  expect(fetcher).toHaveBeenCalledTimes(5)
  for (const call of fetcher.mock.calls) {
    expect(new URL(call[0], 'http://local').searchParams.get('keyword')).toBe(
      '联芸',
    )
  }
})
it('queries only the selected segment and surfaces backend errors', async () => {
  const fetcher = vi.fn(
    async () =>
      new Response(
        JSON.stringify({
          code: 400,
          message: '目标产业环节不在环节字典中',
          data: null,
        }),
      ),
  )
  vi.stubGlobal('fetch', fetcher)
  await expect(
    searchScores('设备', '', new AbortController().signal),
  ).rejects.toThrow('目标产业环节不在环节字典中')
  expect(fetcher).toHaveBeenCalledTimes(1)
})
