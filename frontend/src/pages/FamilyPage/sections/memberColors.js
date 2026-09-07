export const MEMBER_COLORS = [
  '#d97757',
  '#4c6fef',
  '#2f8f5b',
  '#a855f7',
  '#eab308',
  '#ef4444',
  '#0ea5e9',
  '#14b8a6',
]

export function getMemberColor(adultIndex) {
  return MEMBER_COLORS[adultIndex % MEMBER_COLORS.length]
}
