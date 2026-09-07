const dateFormatter = new Intl.DateTimeFormat("ru-RU", {
  day: "numeric",
  month: "short",
});

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
});

export function formatExpenseDate(isoDate) {
  const date = new Date(isoDate);
  const today = new Date();
  const isSameDay = date.toDateString() === today.toDateString();
  if (isSameDay) return "Сегодня";

  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) return "Вчера";

  return dateFormatter.format(date);
}

export function formatExpenseOwner(expense) {
  if (expense.owner_type === "self") return "личный расход";
  if (expense.owner_type === "shared") return "общий расход";
  return "долг на участнике";
}

export function formatExpenseAmount(amount) {
  return `${currencyFormatter.format(Number(amount))} ₽`;
}
