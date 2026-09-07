import { useCallback, useEffect, useState } from "react";
import AddPurchaseModal from "../../../widgets/AddPurchase/AddPurchaseModal.jsx";

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
  const [editingExpense, setEditingExpense] = useState(null);

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
    <article className="card expense-preview">
      <div className="section-heading expense-preview__heading">
        <h2>Последние расходы</h2>
        <span className="expense-preview__period">
          {capitalize(monthFormatter.format(new Date()))}
        </span>
      </div>

      {isLoading && <p className="list__empty">Загружаем расходы...</p>}

      {!isLoading && error && <p className="list__empty">{error}</p>}

      {!isLoading && !error && expenses.length === 0 && (
        <p className="list__empty">
          Пока нет ни одной покупки — добавьте первую через кнопку «+».
        </p>
      )}

      {!isLoading && !error && expenses.length > 0 && (
        <div className="list expense-preview__list">
          {expenses.map((expense) => {
            const category = getExpenseCategory(expense.category);
            return (
              <div
                className="list__row expense-preview__row"
                data-category={expense.category}
                key={expense.id}
              >
                <span className="expense-preview__details">
                  <b className="expense-preview__category">
                    <span className="expense-preview__category-icon" aria-hidden="true">
                      {category.icon}
                    </span>
                    {category.label}
                  </b>
                  <small className="expense-preview__meta">
                    {formatExpenseDate(expense.created_at)}
                    {expense.payer_name ? ` · ${expense.payer_name}` : ""} ·{" "}
                    {formatExpenseOwner(expense)}
                  </small>
                </span>
                <span className="list__amount expense-preview__amount">
                  <strong>{formatExpenseAmount(expense.amount)}</strong>
                  {expense.can_edit && (
                    <button
                      className="list__edit"
                      type="button"
                      onClick={() => setEditingExpense(expense)}
                      aria-label={`Изменить покупку на ${formatExpenseAmount(expense.amount)}`}
                      title="Изменить покупку"
                    >
                      ✎
                    </button>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      )}
      {editingExpense && (
        <AddPurchaseModal
          expense={editingExpense}
          onClose={() => setEditingExpense(null)}
          onCreated={() => {
            setEditingExpense(null);
            loadExpenses();
          }}
        />
      )}
    </article>
  );
}

export default ExpensePreview;
