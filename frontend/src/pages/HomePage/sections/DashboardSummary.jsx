import { useCallback, useEffect, useState } from "react";

import { getExpenses } from "../../../shared/api/expenses.ts";
import { getMyFamily } from "../../../shared/api/family.ts";
import "./DashboardSummary.css";

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
});

function formatAmount(value) {
  return `${currencyFormatter.format(value)} ₽`;
}

function isSameMonth(isoDate, now) {
  const date = new Date(isoDate);
  return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth();
}

function buildDonut(spent, budget) {
  const circumference = 2 * Math.PI * 45;
  // Доля потраченного визуально не может занять больше полного круга,
  // даже если реально потрачено больше бюджета (тогда просто закрашиваем весь круг).
  const share = budget > 0 ? Math.min(spent / budget, 1) : 0;
  const length = share * circumference;

  return {
    circumference,
    dasharray: `${length} ${circumference - length}`,
  };
}

function DashboardSummary() {
  const [familyBudget, setFamilyBudget] = useState(0);
  const [monthTotal, setMonthTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const [familyResponse, expensesResponse] = await Promise.all([
      getMyFamily(),
      getExpenses(),
    ]);

    if (!familyResponse.error && familyResponse.data) {
      const budget = familyResponse.data.members
        .filter((member) => member.role === "adult")
        .reduce((sum, member) => sum + Number(member.monthly_income ?? 0), 0);
      setFamilyBudget(budget);
    } else if (familyResponse.type !== "family_required") {
      setError(familyResponse.message ?? "Не удалось загрузить бюджет семьи.");
    }

    if (!expensesResponse.error && expensesResponse.data) {
      const now = new Date();
      const total = expensesResponse.data
        .filter((expense) => isSameMonth(expense.created_at, now))
        .reduce((sum, expense) => sum + Number(expense.amount), 0);
      setMonthTotal(total);
    }

    setIsLoading(false);
  }, []);

  useEffect(() => {
    load();

    window.addEventListener("slash-t:expense-created", load);
    return () => window.removeEventListener("slash-t:expense-created", load);
  }, [load]);

  if (isLoading) {
    return (
      <article className="card dashboard-budget">
        <span className="card__eyebrow">Бюджет семьи</span>
        <p className="dashboard-budget__hint">Загружаем...</p>
      </article>
    );
  }

  if (error) {
    return (
      <article className="card dashboard-budget">
        <span className="card__eyebrow">Бюджет семьи</span>
        <p className="dashboard-budget__hint">{error}</p>
      </article>
    );
  }

  const percent = familyBudget > 0 ? Math.round((monthTotal / familyBudget) * 100) : 0;
  const donut = buildDonut(monthTotal, familyBudget);

  return (
    <article className="card dashboard-budget">
      <span className="card__eyebrow">Бюджет семьи</span>

      <div className="dashboard-budget__body">
        <div className="dashboard-budget__figures">
          <div className="dashboard-budget__figure">
            <strong className="stat__value">{formatAmount(familyBudget)}</strong>
            <span className="stat__caption">бюджет на текущий месяц</span>
          </div>
          <div className="dashboard-budget__figure">
            <strong className="stat__value">{formatAmount(monthTotal)}</strong>
            <span className="stat__caption">общие расходы за месяц</span>
          </div>
        </div>

        <svg
          className="dashboard-budget__donut"
          viewBox="0 0 120 120"
          role="img"
          aria-label="Потрачено от бюджета семьи"
        >
          <circle className="dashboard-budget__track" cx="60" cy="60" r="45" />
          <circle
            className="dashboard-budget__value-arc"
            cx="60"
            cy="60"
            r="45"
            strokeDasharray={donut.dasharray}
            transform="rotate(-90 60 60)"
          />
          <text x="60" y="56" className="dashboard-budget__percent" textAnchor="middle">
            {percent}%
          </text>
          <text x="60" y="72" className="dashboard-budget__percent-caption" textAnchor="middle">
            потрачено
          </text>
        </svg>
      </div>
    </article>
  );
}

export default DashboardSummary;
