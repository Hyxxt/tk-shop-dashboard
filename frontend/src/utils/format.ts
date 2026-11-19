export function money(n: number, digits = 2): string {
  const a = Math.abs(n)
  if (a >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (a >= 1_000) return `$${(n / 1_000).toFixed(a >= 10_000 ? 1 : 2)}k`
  return `$${n.toFixed(digits)}`
}

export function moneyFull(n: number): string {
  return `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function num(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 10_000) return `${(n / 10_000).toFixed(1)}万`
  return n.toLocaleString('en-US')
}

export function pct(n: number, digits = 2): string {
  return `${n > 0 ? '' : ''}${n.toFixed(digits)}%`
}

export function shortDate(d: string): string {
  const [, m, day] = d.split('-')
  return `${Number(m)}/${Number(day)}`
}

export function dt(s: string | null): string {
  if (!s) return '—'
  return s.replace('T', ' ').slice(0, 16)
}

export const PLATFORM_LABEL: Record<string, string> = {
  TIKTOK_SHOP: 'TikTok Shop',
  TIKTOK: 'TikTok',
  INSTAGRAM: 'Instagram',
  FACEBOOK: 'Facebook',
  YOUTUBE: 'YouTube',
}

export const PLATFORM_COLOR: Record<string, string> = {
  TIKTOK_SHOP: '#165dff',
  TIKTOK: '#1d2129',
  INSTAGRAM: '#d4537e',
  FACEBOOK: '#185fa5',
  YOUTUBE: '#f53f3f',
}
