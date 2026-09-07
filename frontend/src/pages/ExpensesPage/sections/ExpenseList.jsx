import { getExpenseCategory } from "../../../shared/lib/expenseCategories.js";
import {
  formatExpenseAmount,
  formatExpenseDate,
  formatExpenseOwner,
} from "../../../shared/lib/expenseFormat.js";
import "./ExpenseList.css";

function ExpenseList({ expenses, isLoading, error }) {
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

export default ExpenseList;
