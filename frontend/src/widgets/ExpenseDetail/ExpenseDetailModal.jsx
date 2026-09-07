import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'

import { getExpense } from '../../shared/api/expenses.ts'
import { getExpenseCategory } from '../../shared/lib/expenseCategories.js'
import {
  formatExpenseAmount,
  formatExpenseDate,
  formatExpenseOwner,
} from '../../shared/lib/expenseFormat.js'

import './ExpenseDetailModal.css'

/**
 * Карточка покупки, открываемая по клику на строку в истории покупок
 * или в «Последних расходах». Если покупка добавлена через чек —
 * показывает список товаров внутри неё.
 */
function ExpenseDetailModal({ expenseId, onClose }) {
  const [expense, setExpense] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isCurrent = true

    getExpense(expenseId).then((response) => {
      if (!isCurrent) return
      if (response.error || !response.data) {
        setError(response.message ?? 'Не удалось загрузить покупку.')
      } else {
        setExpense(response.data)
      }
      setIsLoading(false)
    })

    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      isCurrent = false
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [expenseId, onClose])

  const category = expense ? getExpenseCategory(expense.category) : null

  return createPortal(
    <div className="expense-detail-overlay" onClick={onClose}>
      <div
        className="expense-detail-modal"
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="expense-detail-modal__header">
          <h2>{expense?.shop_name || 'Покупка'}</h2>
          <button
            className="expense-detail-modal__close"
            type="button"
            onClick={onClose}
            aria-label="Закрыть"
          >
            ×
          </button>
        </div>

        {isLoading && <p className="list__empty">Загружаем покупку...</p>}
        {!isLoading && error && <p className="list__empty">{error}</p>}

        {!isLoading && !error && expense && (
          <>
            <div className="expense-detail-modal__summary">
              <span>
                <b>
                  <span aria-hidden="true">{category.icon}</span> {category.label}
                </b>
                <small>
                  {formatExpenseDate(expense.created_at)}
                  {expense.payer_name ? ` · ${expense.payer_name}` : ''} ·{' '}
                  {formatExpenseOwner(expense)}
                </small>
              </span>
              <strong>{formatExpenseAmount(expense.amount)}</strong>
            </div>

            {expense.items && expense.items.length > 0 && (
              <div className="expense-detail-modal__items">
                <p className="expense-detail-modal__items-title">
                  Товары ({expense.items.length})
                </p>
                {expense.items.map((item) => {
                  const itemCategory = getExpenseCategory(item.category)
                  const ownerLabel =
                    item.owner_type === 'shared' ? 'Общее' : item.owner_name ? `Личное · ${item.owner_name}` : 'Личное'
                  return (
                    <div className="expense-detail-modal__item" key={item.id}>
                      <span>
                        <span aria-hidden="true">{itemCategory.icon}</span> {item.name}
                        <small className="expense-detail-modal__item-owner"> · {ownerLabel}</small>
                      </span>
                      <strong>{formatExpenseAmount(item.sum)}</strong>
                    </div>
                  )
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>,
    document.body,
  )
}

export default ExpenseDetailModal
