import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'

import { useAuth } from '../../app/providers/AuthProvider.jsx'
import { getMyFamily } from '../../shared/api/family.ts'
import { createExpense, scanReceipt } from '../../shared/api/expenses.ts'

import './AddPurchase.css'

const PERSONAL_WORDS = [
  'алког',
  'пиво',
  'вино',
  'водк',
  'коньяк',
  'сигар',
  'табак',
  'чипс',
  'сухар',
  'шоколад',
  'конфет',
  'печень',
  'мармелад',
  'жвач',
  'газиров',
  'энергет',
]

function classifyItem(name) {
  const normalizedName = name.toLowerCase()
  return PERSONAL_WORDS.some((word) => normalizedName.includes(word)) ? 'personal' : 'shared'
}

function formatMoney(value) {
  return `${new Intl.NumberFormat('ru-RU').format(value)} ₽`
}

function ScanResultOverlay({ text, onClose, onCreated }) {
  const { user } = useAuth()
  const [receipt, setReceipt] = useState(null)
  const [members, setMembers] = useState([])
  const [items, setItems] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    let isCurrent = true

    async function loadReceipt() {
      const [receiptResponse, familyResponse] = await Promise.all([
        scanReceipt(text),
        getMyFamily(),
      ])

      if (!isCurrent) return
      if (receiptResponse.error || !receiptResponse.data) {
        setError(receiptResponse.message ?? 'Не удалось распознать чек.')
        setStatus('error')
        return
      }

      setReceipt(receiptResponse.data)
      setMembers(familyResponse.data?.members ?? [])
      setItems(
        receiptResponse.data.items.map((item, index) => ({
          ...item,
          id: `${item.name}-${index}`,
          assignment: classifyItem(item.name) === 'shared' ? 'shared' : String(user?.id),
        })),
      )
      setStatus('review')
    }

    loadReceipt()
    return () => {
      isCurrent = false
    }
  }, [text, user?.id])

  const total = useMemo(() => items.reduce((sum, item) => sum + Number(item.amount), 0), [items])

  function updateAssignment(itemId, assignment) {
    setItems((current) =>
      current.map((item) => (item.id === itemId ? { ...item, assignment } : item)),
    )
  }

  async function handleSave() {
    const groups = new Map()
    items.forEach((item) => {
      const key = item.assignment
      groups.set(key, (groups.get(key) ?? 0) + Number(item.amount))
    })

    setIsSaving(true)
    setError('')
    for (const [assignment, amount] of groups) {
      const payload =
        assignment === 'shared'
          ? { amount, owner_type: 'shared', category: 'groceries' }
          : { amount, owner_type: 'member', owner_id: Number(assignment), category: 'groceries' }
      const response = await createExpense(payload)
      if (response.error) {
        setError(response.message ?? 'Не удалось сохранить траты из чека.')
        setIsSaving(false)
        return
      }
    }

    setIsSaving(false)
    onCreated?.()
    onClose()
  }

  return createPortal(
    <div className="scan-result">
      <button className="scan-result__close" type="button" onClick={onClose} aria-label="Закрыть">
        ×
      </button>

      <div className="scan-result__body">
        {status === 'loading' && <p className="scan-result__message">Проверяем чек...</p>}
        {status === 'error' && (
          <div className="scan-result__message scan-result__message--error">
            <p>{error}</p>
            <button type="button" onClick={onClose}>Закрыть</button>
          </div>
        )}
        {status === 'review' && receipt && (
          <>
            <p className="scan-result__label">{receipt.store}</p>
            <h2 className="scan-result__title">Проверьте товары</h2>
            <p className="scan-result__total">Итого: {formatMoney(total)}</p>
            <div className="scan-result__items">
              {items.map((item) => (
                <div className="scan-result__item" key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    <small>{item.quantity} × {formatMoney(item.price)}</small>
                  </div>
                  <div className="scan-result__item-controls">
                    <b>{formatMoney(item.amount)}</b>
                    <select
                      value={item.assignment}
                      onChange={(event) => updateAssignment(item.id, event.target.value)}
                      aria-label={`Кому предназначен товар ${item.name}`}
                    >
                      <option value="shared">Общее</option>
                      {members.map((member) => (
                        <option value={member.id} key={member.id}>
                          {member.id === user?.id ? `${member.name} (я)` : member.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </div>
            {error && <p className="scan-result__error">{error}</p>}
            <button className="scan-result__save" type="button" onClick={handleSave} disabled={isSaving}>
              {isSaving ? 'Сохраняем...' : 'Добавить траты'}
            </button>
          </>
        )}
      </div>
    </div>,
    document.body,
  )
}

export default ScanResultOverlay
