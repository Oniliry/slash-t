import { getExpenseCategory } from "../../../shared/lib/expenseCategories.js";
import {
  formatExpenseAmount,
  formatExpenseDate,
  formatExpenseOwner,
} from "../../../shared/lib/expenseFormat.js";
import "./ExpenseList.css";

function ExpenseList({ expenses, isLoading, error, onEdit }) {
  return (
    <article className="card expense-history">
      <div className="section-heading expense-history__heading">
        <h2>История покупок</h2>
        <span className="expense-history__filter">Все категории</span>
      </div>

      {isLoading && <p className="list__empty">Загружаем историю покупок...</p>}

      {!isLoading && error && <p className="list__empty">{error}</p>}

      {!isLoading && !error && expenses.length === 0 && (
        <p className="list__empty">
          Пока нет ни одной покупки — добавьте первую через кнопку «+».
        </p>
      )}

      {!isLoading && !error && expenses.length > 0 && (
        <div className="list expense-history__list">
          {expenses.map((expense) => {
            const category = getExpenseCategory(expense.category);
            return (
              <div
                className="list__row expense-history__row"
                data-category={expense.category}
                key={expense.id}
              >
                <span className="expense-history__details">
                  <b className="expense-history__category">
                    <span className="expense-history__category-icon" aria-hidden="true">
                      {category.icon}
                    </span>
                    {category.label}
                  </b>
                  <small className="expense-history__meta">
                    {formatExpenseDate(expense.created_at)}
                    {expense.payer_name ? ` · ${expense.payer_name}` : ""} ·{" "}
                    {formatExpenseOwner(expense)}
                  </small>
                </span>
                <span className="list__amount expense-history__amount">
                  <strong>{formatExpenseAmount(expense.amount)}</strong>
                  {expense.can_edit && (
                    <button
                      className="list__edit"
                      type="button"
                      onClick={() => onEdit(expense)}
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
    </article>
  );
}

export default ExpenseList;
