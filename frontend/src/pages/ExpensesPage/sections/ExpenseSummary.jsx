import SpendingByPayerChart from "./SpendingByPayerChart.jsx";
import "./ExpenseSummary.css";

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
});

function formatAmount(value) {
  return `${currencyFormatter.format(value)} ₽`;
}

function formatShare(part, total) {
  if (total <= 0) return "0% всех трат";
  return `${Math.round((part / total) * 100)}% всех трат`;
}

function ExpenseSummary({ expenses, members, isLoading }) {
  // owner_type "self" — личный расход. "member"/"shared" так или иначе
  // ложатся расходом на семейный бюджет (просто по-разному делятся долгами).
  const personalTotal = expenses
    .filter((expense) => expense.owner_type === "self")
    .reduce((sum, expense) => sum + Number(expense.amount), 0);

  const sharedTotal = expenses
    .filter((expense) => expense.owner_type !== "self")
    .reduce((sum, expense) => sum + Number(expense.amount), 0);

  const total = personalTotal + sharedTotal;

  return (
    <div className="stats-grid">
      <article className="card card--total">
        <span className="card__eyebrow">Всего за месяц</span>
        <strong className="stat__value">
          {isLoading ? "…" : formatAmount(total)}
        </strong>
        <span className="stat__caption">
          {expenses.length === 0 && !isLoading ? "Пока нет покупок" : "по всем категориям"}
        </span>
        {!isLoading && <SpendingByPayerChart expenses={expenses} members={members} />}
      </article>
      <article className="card card--shared">
        <span className="card__eyebrow">Общие</span>
        <strong className="stat__value">
          {isLoading ? "…" : formatAmount(sharedTotal)}
        </strong>
        <span className="stat__caption">
          {isLoading ? "" : formatShare(sharedTotal, total)}
        </span>
      </article>
      <article className="card card--personal">
        <span className="card__eyebrow">Личные</span>
        <strong className="stat__value">
          {isLoading ? "…" : formatAmount(personalTotal)}
        </strong>
        <span className="stat__caption">
          {isLoading ? "" : formatShare(personalTotal, total)}
        </span>
      </article>
    </div>
  );
}

export default ExpenseSummary;
