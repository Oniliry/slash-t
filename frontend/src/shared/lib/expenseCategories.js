// Категории покупок. Порядок задаёт порядок отображения в выборе категории.
export const EXPENSE_CATEGORIES = [
  { id: 'groceries', label: 'Продукты', icon: '🛒' },
  { id: 'utilities', label: 'ЖКХ', icon: '🏠' },
  { id: 'transport', label: 'Транспорт', icon: '🚗' },
  { id: 'cafe', label: 'Кафе и рестораны', icon: '☕️' },
  { id: 'entertainment', label: 'Развлечения', icon: '🎬' },
  { id: 'health', label: 'Здоровье', icon: '💊' },
  { id: 'clothing', label: 'Одежда', icon: '👕' },
  { id: 'other', label: 'Другое', icon: '📦' },
]

const CATEGORY_BY_ID = Object.fromEntries(
  EXPENSE_CATEGORIES.map((category) => [category.id, category]),
)

export function getExpenseCategory(categoryId) {
  return CATEGORY_BY_ID[categoryId] ?? CATEGORY_BY_ID.other
}
