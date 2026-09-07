import { useState } from "react";

import ExpenseDetailModal from "../../../widgets/ExpenseDetail/ExpenseDetailModal.jsx";
import { getExpenseCategory } from "../../../shared/lib/expenseCategories.js";
import {
  formatExpenseAmount,
  formatExpenseDate,
  formatExpenseOwner,
} from "../../../shared/lib/expenseFormat.js";
import "./ExpenseList.css";

function ExpenseList({ expenses, isLoading, error }) {
  const [openExpenseId, setOpenExpenseId] = useState(null);

  return (
    <article className="card">
      <div className="section-heading">
        <h2>История покупок</h2>
        <span className="section-heading__hint">Все категории</span>
      </div>

      {isLoading && <p className="list__empty">Загружаем историю покупок...</p>}

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
            const title = expense.shop_name || category.label;
            return (
              <button
                type="button"
                className="list__row list__row--button"
                key={expense.id}
                onClick={() => setOpenExpenseId(expense.id)}
              >
                <span>
                  <b>
                    <span aria-hidden="true">{category.icon}</span> {title}
                  </b>
                  <small>
                    {formatExpenseDate(expense.created_at)}
                    {expense.payer_name ? ` · ${expense.payer_name}` : ""} ·{" "}
                    {formatExpenseOwner(expense)}
                    {expense.items_count > 0 ? ` · ${expense.items_count} товаров` : ""}
                  </small>
                </span>
                <strong>{formatExpenseAmount(expense.amount)}</strong>
              </button>
            );
          })}
        </div>
      )}

      {openExpenseId && (
        <ExpenseDetailModal expenseId={openExpenseId} onClose={() => setOpenExpenseId(null)} />
      )}
    </article>
  );
}

export default ExpenseList;
