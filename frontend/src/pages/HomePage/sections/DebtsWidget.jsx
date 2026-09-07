import { useCallback, useEffect, useState } from 'react'

import { confirmDebt, getMyDebts } from '../../../shared/api/expenses.ts'

import './DebtsWidget.css'

function formatMoney(value) {
  return `${new Intl.NumberFormat('ru-RU').format(value ?? 0)} ₽`
}

// Объединяет несколько долгов с одним и тем же человеком в одну строку:
// если, например, вам должны 300 ₽ по одной покупке и 500 ₽ по другой —
// на главной это должно выглядеть как один долг на 800 ₽, а не два отдельных.
function groupByCounterpart(debts, getCounterpart) {
  const grouped = new Map()

  debts.forEach((debt) => {
    const counterpart = getCounterpart(debt)
    const existing = grouped.get(counterpart.id)

    if (existing) {
      existing.amount += Number(debt.amount)
      existing.debtIds.push(debt.id)
    } else {
      grouped.set(counterpart.id, {
        id: counterpart.id,
        name: counterpart.name,
        amount: Number(debt.amount),
        debtIds: [debt.id],
      })
    }
  })

  return [...grouped.values()].sort((a, b) => b.amount - a.amount)
}

function DebtsWidget() {
  const [debts, setDebts] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [confirmingId, setConfirmingId] = useState(null)

  const loadDebts = useCallback(async () => {
    const response = await getMyDebts()

    if (response.error) {
      setError(response.message ?? 'Не удалось загрузить долги.')
      return
    }

    setError('')
    setDebts(response.data)
  }, [])

  useEffect(() => {
    setIsLoading(true)
    loadDebts().finally(() => setIsLoading(false))

    function handleExpenseCreated() {
      loadDebts()
    }

    window.addEventListener('slash-t:expense-created', handleExpenseCreated)
    return () => window.removeEventListener('slash-t:expense-created', handleExpenseCreated)
  }, [loadDebts])

  // Долг на главной может быть объединением нескольких реальных долгов
  // (из разных покупок), поэтому подтверждаем их все разом.
  async function handleConfirm(group) {
    setConfirmingId(group.id)
    const results = await Promise.all(group.debtIds.map((debtId) => confirmDebt(debtId)))
    setConfirmingId(null)

    const failed = results.find((response) => response.error)
    if (failed) {
      setError(failed.message ?? 'Не удалось подтвердить долг.')
      return
    }

    setError('')
    await loadDebts()
  }

  if (isLoading) {
    return (
      <article className="card debts-widget">
        <div className="section-heading">
          <h2>Взаиморасчёты</h2>
        </div>
        <p className="debts-widget__hint">Загружаем...</p>
      </article>
    )
  }

  if (error && !debts) {
    return (
      <article className="card debts-widget">
        <div className="section-heading">
          <h2>Взаиморасчёты</h2>
        </div>
        <p className="debts-widget__hint">{error}</p>
      </article>
    )
  }

  const iOwe = groupByCounterpart(debts?.i_owe ?? [], (debt) => debt.creditor)
  const owedToMe = groupByCounterpart(debts?.owed_to_me ?? [], (debt) => debt.debtor)

  if (iOwe.length === 0 && owedToMe.length === 0) {
    return (
      <article className="card debts-widget">
        <div className="section-heading">
          <h2>Взаиморасчёты</h2>
        </div>
        <p className="debts-widget__hint">Все долги погашены — отличная работа!</p>
      </article>
    )
  }

  return (
    <article className="card debts-widget">
      <div className="section-heading">
        <h2>Взаиморасчёты</h2>
      </div>

      {error && <p className="debts-widget__error">{error}</p>}

      {iOwe.length > 0 && (
        <div className="debts-widget__group">
          <p className="debts-widget__group-title">Вы должны</p>
          <div className="list">
            {iOwe.map((group) => (
              <div className="list__row" key={group.id}>
                <span>
                  <b>{group.name}</b>
                  <small>Ждёт перевода и подтверждения от получателя</small>
                </span>
                <strong className="debts-widget__amount debts-widget__amount--negative">
                  {formatMoney(group.amount)}
                </strong>
              </div>
            ))}
          </div>
        </div>
      )}

      {owedToMe.length > 0 && (
        <div className="debts-widget__group">
          <p className="debts-widget__group-title">Вам должны</p>
          <div className="list">
            {owedToMe.map((group) => (
              <div className="list__row" key={group.id}>
                <span>
                  <b>{group.name}</b>
                  <small>Подтвердите, когда получите перевод</small>
                </span>
                <div className="debts-widget__owed-actions">
                  <strong className="debts-widget__amount debts-widget__amount--positive">
                    {formatMoney(group.amount)}
                  </strong>
                  <button
                    className="debts-widget__confirm"
                    type="button"
                    onClick={() => handleConfirm(group)}
                    disabled={confirmingId === group.id}
                  >
                    {confirmingId === group.id ? 'Подтверждаем...' : 'Подтвердить'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </article>
  )
}

export default DebtsWidget
