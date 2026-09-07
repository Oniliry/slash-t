import { useCallback, useEffect, useState } from "react";

import { getExpenses } from "../../../shared/api/expenses.ts";
import { getExpenseCategory } from "../../../shared/lib/expenseCategories.js";
import {
  formatExpenseAmount,
  formatExpenseDate,
  formatExpenseOwner,
} from "../../../shared/lib/expenseFormat.js";
import "./ExpensePreview.css";

const PREVIEW_COUNT = 5;

const monthFormatter = new Intl.DateTimeFormat("ru-RU", { month: "long" });

function capitalize(word) {
  return word.charAt(0).toUpperCase() + word.slice(1);
}

function ExpensePreview() {
  const [expenses, setExpenses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadExpenses = useCallback(async () => {
    const response = await getExpenses();

    if (!response.error && response.data) {
      // История покупок уже приходит от новых к старым — берём первые N.
      setExpenses(response.data.slice(0, PREVIEW_COUNT));
      setError("");
    } else if (response.type !== "family_required") {
      setError(response.message ?? "Не удалось загрузить расходы.");
    }

    setIsLoading(false);
  }, []);

  useEffect(() => {
    loadExpenses();

    // Обновляем превью сразу после добавления покупки через кнопку "+",
    // чтобы список на главной был синхронизирован с историей покупок.
    window.addEventListener("slash-t:expense-created", loadExpenses);
    return () => window.removeEventListener("slash-t:expense-created", loadExpenses);
  }, [loadExpenses]);

  return (
    <article className="card">
      <div className="section-heading">
        <h2>Последние расходы</h2>
        <span className="section-heading__hint">{capitalize(monthFormatter.format(new Date()))}</span>
      </div>

      {isLoading && <p className="list__empty">Загружаем расходы...</p>}

      {!isLoading && error && <p className="list__empty">{error}</p>}

      {!isLoading && !error && expenses.length === 0 && (
        <p className="list__empty">
          Пока нет ни одной покупки — добавьте первую через кнопку «+».
        </p>
      )}

      {!isLoading && !error && expenses.length > 0 && (
        <div className="list">
          {expenses.map((expense) => {
            const category = getExpenseCategory(expense.category);
            return (
              <div className="list__row" key={expense.id}>
                <span>
                  <b>
                    <span aria-hidden="true">{category.icon}</span> {category.label}
                  </b>
                  <small>
                    {formatExpenseDate(expense.created_at)}
                    {expense.payer_name ? ` · ${expense.payer_name}` : ""} ·{" "}
                    {formatExpenseOwner(expense)}
                  </small>
                </span>
                <strong>{formatExpenseAmount(expense.amount)}</strong>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}

export default ExpensePreview;
