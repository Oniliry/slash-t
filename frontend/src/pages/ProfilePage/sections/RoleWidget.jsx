import { useEffect, useState } from 'react'

import { useAuth } from '../../../app/providers/AuthProvider.jsx'
import { getMyFamily } from '../../../shared/api/family.ts'
import { updateIncome } from '../../../shared/api/profile.ts'

import './ProfileWidgets.css'

const ROLE_LABELS = {
  adult: 'Взрослый',
  child: 'Ребёнок',
}

function formatShare(income_share) {
  if (income_share === null || income_share === undefined) return '—'
  return `${Math.round(income_share * 100)}%`
}

function RoleWidget() {
  const { user, refreshUser } = useAuth()
  const isAdult = user?.role === 'adult'

  const [income, setIncome] = useState(user?.monthly_income ?? '')
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [incomeShare, setIncomeShare] = useState(null)
  const [isShareLoading, setIsShareLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    async function loadShare() {
      setIsShareLoading(true)
      const response = await getMyFamily()

      if (!isMounted) return

      if (!response.error && response.data) {
        const me = response.data.members.find((member) => member.id === user?.id)
        setIncomeShare(me?.income_share ?? null)
      }

      setIsShareLoading(false)
    }

    loadShare()

    return () => {
      isMounted = false
    }
  }, [user?.id, user?.monthly_income])

  const numericIncome = Number(income)
  const isUnchanged = numericIncome === Number(user?.monthly_income ?? 0)
  const canSave = isAdult && numericIncome > 0 && !isUnchanged && !isSaving

  async function handleSave() {
    if (!canSave) return

    setIsSaving(true)
    setMessage(null)

    const response = await updateIncome({ monthly_income: numericIncome })

    setIsSaving(false)

    if (response.error) {
      setMessage({ type: 'error', text: response.message ?? 'Не удалось сохранить доход.' })
      return
    }

    await refreshUser()
    setMessage({ type: 'success', text: 'Доход обновлён.' })
  }

  return (
    <article className="profile-widget">
      <h2>Роль в семье</h2>
      <p className="profile-widget__hint">
        Роль задаётся один раз при входе в семью и не меняется. Доход можно
        обновить в любой момент — доля в общем бюджете пересчитывается
        автоматически.
      </p>

      <dl className="profile-widget__readonly-list">
        <div>
          <dt>Роль</dt>
          <dd>{ROLE_LABELS[user?.role] ?? '—'}</dd>
        </div>
        <div>
          <dt>Доля бюджета</dt>
          <dd>{isShareLoading ? '...' : formatShare(incomeShare)}</dd>
        </div>
      </dl>

      {isAdult ? (
        <>
          <div className="profile-widget__row">
            <div className="profile-widget__field">
              <label htmlFor="profile-income">Примерный доход, ₽/мес</label>
              <input
                id="profile-income"
                value={income}
                onChange={(event) => setIncome(event.target.value)}
                type="number"
                min="1"
                step="1"
              />
            </div>
            <button
              className="profile-widget__save"
              type="button"
              onClick={handleSave}
              disabled={!canSave}
            >
              {isSaving ? 'Сохраняем...' : 'Сохранить'}
            </button>
          </div>
          {message && (
            <p className={`profile-widget__message profile-widget__message--${message.type}`}>
              {message.text}
            </p>
          )}
        </>
      ) : (
        <p className="profile-widget__hint" style={{ margin: 0 }}>
          У роли «ребёнок» доход не указывается — общие траты компенсируют взрослые.
        </p>
      )}
    </article>
  )
}

export default RoleWidget
