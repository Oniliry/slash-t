import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'

import { useAuth } from '../../app/providers/AuthProvider.jsx'
import { getMyFamily } from '../../shared/api/family.ts'
import { createExpense } from '../../shared/api/expenses.ts'
import { EXPENSE_CATEGORIES } from '../../shared/lib/expenseCategories.js'

import './ReceiptScanner.css'

/**
 * Экран проверки распознанных товаров: покупка всегда добавляется одной
 * записью на весь чек, а владелец (личное/общее) выбирается у каждого
 * товара отдельно — по умолчанию проставляется автоматически.
 */
function ReceiptReviewScreen({ shop, items, onClose, onCreated }) {
  const { user } = useAuth()
  const [members, setMembers] = useState([])
  const [rows, setRows] = useState(() =>
    items.map((item) => ({
      ...item,
      // Авто-определение владельца: алкоголь/косметика/техника — личное,
      // остальное — общее. Дальше можно выбрать вручную.
      owner: item.personal ? String(user?.id ?? 'shared') : 'shared',
    })),
  )
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getMyFamily().then((response) => {
      if (!response.error && response.data) setMembers(response.data.members)
    })
  }, [])

  function setItemCategory(index, category) {
    setRows((current) =>
      current.map((row, i) => (i === index ? { ...row, category } : row)),
    )
  }

  function setItemOwner(index, owner) {
    setRows((current) =>
      current.map((row, i) => (i === index ? { ...row, owner } : row)),
    )
  }

  const total = rows.reduce((sum, row) => sum + row.sum, 0)

  async function handleSubmit() {
    setIsSaving(true)
    setError('')

    // Покупка всегда сохраняется одной записью в истории — владелец
    // указывается у каждого товара внутри неё.
    const payload = {
      shop_name: shop || null,
      items: rows.map((row) =>
        row.owner === 'shared'
          ? { name: row.name, sum: row.sum, category: row.category, owner_type: 'shared' }
          : {
              name: row.name,
              sum: row.sum,
              category: row.category,
              owner_type: 'member',
              owner_id: Number(row.owner),
            },
      ),
    }

    const response = await createExpense(payload)
    setIsSaving(false)

    if (response.error) {
      setError(response.message ?? 'Не удалось добавить покупку.')
      return
    }

    onCreated()
    onClose()
  }

  return createPortal(
    <div className="receipt-result" role="dialog" aria-modal="true">
      <button
        type="button"
        className="receipt-result__close"
        onClick={onClose}
        aria-label="Закрыть"
      >
        ×
      </button>

      <div className="receipt-result__scroll">
        <p className="receipt-result__eyebrow">Проверьте товары</p>
        <h2 className="receipt-result__shop">{shop || 'Чек распознан'}</h2>

        <div className="receipt-result__total">
          <span>Итого · {rows.length} {rows.length === 1 ? 'товар' : 'товаров'}</span>
          <strong>{total.toFixed(2)} ₽</strong>
        </div>

        <p className="add-purchase-modal__field">Товары в чеке</p>
        <p className="receipt-review__hint-dark">
          Алкоголь, косметику и технику мы отметили как личные — остальное общее.
          При необходимости поправьте вручную.
        </p>
        <div className="receipt-review__items">
          {rows.map((row, index) => (
            <div className="receipt-review__item" key={index}>
              <div className="receipt-review__item-head">
                <b>{row.name}</b>
                <strong>{row.sum.toFixed(2)} ₽</strong>
              </div>
              <div className="receipt-review__item-meta">
                <select
                  className="receipt-review__category"
                  value={row.category}
                  onChange={(event) => setItemCategory(index, event.target.value)}
                >
                  {EXPENSE_CATEGORIES.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.label}
                    </option>
                  ))}
                </select>

                <select
                  className="receipt-review__owner"
                  value={row.owner}
                  onChange={(event) => setItemOwner(index, event.target.value)}
                >
                  <option value="shared">Общее</option>
                  {members.map((member) => (
                    <option key={member.id} value={String(member.id)}>
                      {member.id === user?.id ? `${member.name} (я, личное)` : member.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          ))}
        </div>

        {error && <p className="receipt-scanner__error">{error}</p>}

        <button
          type="button"
          className="receipt-review__submit"
          onClick={handleSubmit}
          disabled={isSaving || rows.length === 0}
        >
          {isSaving ? 'Добавляем...' : 'Добавить покупку'}
        </button>
      </div>
    </div>,
    document.body,
  )
}

export default ReceiptReviewScreen
