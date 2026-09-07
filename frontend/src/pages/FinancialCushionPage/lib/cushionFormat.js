export const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
});

const statementFormatter = new Intl.NumberFormat("ru-RU", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatCushionAmount(value) {
  return `${currencyFormatter.format(Number(value))} ₽`;
}

export function formatStatementAmount(value) {
  return `${statementFormatter.format(Number(value))} ₽`;
}

export function formatCushionDate(isoDate) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(isoDate));
}
