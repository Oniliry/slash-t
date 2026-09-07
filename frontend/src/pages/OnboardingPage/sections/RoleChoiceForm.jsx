import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../../../app/providers/AuthProvider.jsx'
import { setFamilyRole } from '../../../shared/api/family.ts'

import '../OnboardingPage.css'

function RoleChoiceForm() {
  const { refreshUser } = useAuth()
  const navigate = useNavigate()

  const [role, setRole] = useState('adult')
  const [monthlyIncome, setMonthlyIncome] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (role === 'adult' && (!monthlyIncome || Number(monthlyIncome) <= 0)) {
      setError('Укажите примерный месячный доход.')
      return
    }

    setIsSubmitting(true)

    const payload =
      role === 'adult'
        ? { role, monthly_income: Number(monthlyIncome) }
        : { role }

    const response = await setFamilyRole(payload)

    setIsSubmitting(false)

    if (response.error) {
      setError(response.message ?? 'Не удалось сохранить роль.')
      return
    }

    await refreshUser()
    navigate('/')
  }

  return (
    <section className="onboarding-page">
      <p className="onboarding-page__step">Шаг 2 из 2</p>
      <h1>Ваша роль в семье</h1>
      <p>От роли зависит, как система будет распределять общие траты.</p>

      <form className="onboarding-page__fields" onSubmit={handleSubmit}>
        <div className="role-options">
          <button
            type="button"
            className={`role-option ${role === 'adult' ? 'role-option--active' : ''}`}
            onClick={() => setRole('adult')}
          >
            <strong>Взрослый</strong>
            <span>Платежеспособный, вносит долю в общий бюджет</span>
          </button>
          <button
            type="button"
            className={`role-option ${role === 'child' ? 'role-option--active' : ''}`}
            onClick={() => setRole('child')}
          >
            <strong>Ребёнок</strong>
            <span>Неплатежеспособный, покупки за него компенсируют взрослые</span>
          </button>
        </div>

        {role === 'adult' && (
          <>
            <label>
              Примерный месячный доход, ₽
              <input
                value={monthlyIncome}
                onChange={(event) => setMonthlyIncome(event.target.value)}
                type="number"
                min="1"
                step="1"
                placeholder="Например, 90000"
                required
              />
            </label>
            <p className="role-note">
              Доход нужен только для расчёта вашей доли в общих тратах семьи — например,
              если вы зарабатываете 60% семейного бюджета, то и общие покупки будут
              делиться в пропорции 60/40. Точная сумма дохода другим участникам не
              показывается — видна только рассчитанная доля.
            </p>
          </>
        )}

        {error && <p className="onboarding-page__error">{error}</p>}

        <button className="onboarding-page__submit" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Сохраняем...' : 'Продолжить'}
        </button>
      </form>
    </section>
  )
}

export default RoleChoiceForm
