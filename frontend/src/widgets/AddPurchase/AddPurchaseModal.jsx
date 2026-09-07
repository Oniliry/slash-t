import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'

import { useAuth } from '../../app/providers/AuthProvider.jsx'
import { getMyFamily } from '../../shared/api/family.ts'
import { createExpense } from '../../shared/api/expenses.ts'
import { EXPENSE_CATEGORIES } from '../../shared/lib/expenseCategories.js'

import './AddPurchase.css'

function AddPurchaseModal({ onClose, onCreated }) {
  const { user } = useAuth()

  const [members, setMembers] = useState([])
  const [isLoadingFamily, setIsLoadingFamily] = useState(true)
  const [amount, setAmount] = useState('')
  const [ownerChoice, setOwnerChoice] = useState('shared')
  const [category, setCategory] = useState('groceries')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let isCurrent = true

    getMyFamily().then((response) => {
      if (!isCurrent) return
      if (!response.error && response.data) {
        setMembers(response.data.members)
      }
      setIsLoadingFamily(false)
    })

    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      isCurrent = false
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose])

  const parsedAmount = Number(amount.replace(',', '.'))
  const canSave = parsedAmount > 0 && !isSaving

  async function handleSubmit(event) {
    event.preventDefault()
    if (!canSave) return

    setIsSaving(true)
    setError('')

    const payload =
      ownerChoice === 'shared'
        ? { amount: parsedAmount, owner_type: 'shared', category }
        : {
            amount: parsedAmount,
            owner_type: 'member',
            owner_id: Number(ownerChoice),
            category,
          }

    const response = await createExpense(payload)
    setIsSaving(false)

    if (response.error) {
      setError(response.message ?? 'Не удалось добавить покупку.')
      return
    }

    onCreated?.(response.data)
    onClose()
  }

  return createPortal(
    <div className="add-purchase-overlay" onClick={onClose}>
      <div
        className="add-purchase-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Добавить покупку"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="add-purchase-modal__header">
          <h2>Добавить покупку</h2>
          <button
            className="add-purchase-modal__close"
            type="button"
            onClick={onClose}
            aria-label="Закрыть"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <label
            className="add-purchase-modal__field add-purchase-modal__field--amount"
            htmlFor="purchase-amount"
          >
            Сумма покупки
          </label>
          <div className="add-purchase-modal__amount-row">
            <input
              id="purchase-amount"
              type="number"
              inputMode="decimal"
              min="0"
              step="0.01"
              placeholder="0"
              autoFocus
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />
            <span className="add-purchase-modal__currency">₽</span>
          </div>

          <p className="add-purchase-modal__field">Кому принадлежит покупка</p>

          {isLoadingFamily ? (
            <p className="add-purchase-modal__hint">Загружаем участников семьи...</p>
          ) : (
            <div className="add-purchase-modal__owners">
              <button
                type="button"
                className={`add-purchase-modal__owner${
                  ownerChoice === 'shared' ? ' add-purchase-modal__owner--active' : ''
                }`}
                onClick={() => setOwnerChoice('shared')}
              >
                Общая
                <small>Долг разойдётся по доле бюджета</small>
              </button>

              {members.map((member) => (
                <button
                  type="button"
                  key={member.id}
                  className={`add-purchase-modal__owner${
                    ownerChoice === String(member.id) ? ' add-purchase-modal__owner--active' : ''
                  }`}
                  onClick={() => setOwnerChoice(String(member.id))}
                >
                  {member.id === user?.id ? `${member.name} (я)` : member.name}
                  <small>{member.id === user?.id ? 'Личный расход' : 'Весь долг — на нём'}</small>
                </button>
              ))}
            </div>
          )}

          <p className="add-purchase-modal__field">Категория</p>
          <div className="add-purchase-modal__categories">
            {EXPENSE_CATEGORIES.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`add-purchase-modal__category${
                  category === item.id ? ' add-purchase-modal__category--active' : ''
                }`}
                onClick={() => setCategory(item.id)}
                aria-pressed={category === item.id}
              >
                <span className="add-purchase-modal__category-icon" aria-hidden="true">
                  {item.icon}
                </span>
                <span className="add-purchase-modal__category-label">{item.label}</span>
              </button>
            ))}
          </div>

          {error && <p className="add-purchase-modal__error">{error}</p>}

          <button className="add-purchase-modal__submit" type="submit" disabled={!canSave}>
            {isSaving ? 'Добавляем...' : 'Добавить покупку'}
          </button>
        </form>
      </div>
    </div>,
    document.body
  )
}

export default AddPurchaseModal
