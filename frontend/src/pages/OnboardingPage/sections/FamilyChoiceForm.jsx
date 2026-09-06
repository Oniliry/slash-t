import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../../../app/providers/AuthProvider.jsx'
import { createFamily, joinFamily } from '../../../shared/api/family.ts'

import '../OnboardingPage.css'

function FamilyChoiceForm() {
  const { refreshUser } = useAuth()
  const navigate = useNavigate()

  const [familyName, setFamilyName] = useState('')
  const [inviteCode, setInviteCode] = useState('')

  const [createError, setCreateError] = useState('')
  const [joinError, setJoinError] = useState('')

  const [isCreating, setIsCreating] = useState(false)
  const [isJoining, setIsJoining] = useState(false)

  const [createdFamily, setCreatedFamily] = useState(null)
  const [isCopied, setIsCopied] = useState(false)

  async function handleCreate(event) {
    event.preventDefault()
    setCreateError('')
    setIsCreating(true)

    const response = await createFamily({ name: familyName.trim() })

    setIsCreating(false)

    if (response.error) {
      setCreateError(response.message ?? 'Не удалось создать семью.')
      return
    }

    await refreshUser()
    setCreatedFamily(response.data)
  }

  async function handleJoin(event) {
    event.preventDefault()
    setJoinError('')
    setIsJoining(true)

    const response = await joinFamily({ invite_code: inviteCode.trim().toUpperCase() })

    setIsJoining(false)

    if (response.error) {
      setJoinError(response.message ?? 'Не удалось присоединиться к семье.')
      return
    }

    await refreshUser()
    navigate('/onboarding/role')
  }

  async function handleCopyCode() {
    if (!createdFamily) return

    try {
      await navigator.clipboard.writeText(createdFamily.invite_code)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch {
      // Буфер обмена недоступен — молча игнорируем, код всё равно виден на экране.
    }
  }

  if (createdFamily) {
    return (
      <section className="onboarding-page">
        <p className="onboarding-page__step">Шаг 1 из 2</p>
        <h1>Семья «{createdFamily.name}» создана</h1>
        <p>Передайте этот код остальным членам семьи — по нему они присоединятся.</p>
        <div className="onboarding-success">
          <div className="onboarding-success__code">{createdFamily.invite_code}</div>
          <div className="onboarding-success__actions">
            <button type="button" className="onboarding-success__copy" onClick={handleCopyCode}>
              {isCopied ? 'Скопировано' : 'Скопировать код'}
            </button>
            <button
              type="button"
              className="onboarding-success__continue"
              onClick={() => navigate('/onboarding/role')}
            >
              Далее
            </button>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="onboarding-page">
      <p className="onboarding-page__step">Шаг 1 из 2</p>
      <h1>Семейное пространство</h1>
      <p>Создайте новую семью или присоединитесь к уже существующей по коду.</p>

      <div className="onboarding-card">
        <h2>Создать семью</h2>
        <p className="onboarding-card__hint">Вы станете создателем и сможете редактировать семью.</p>
        <form className="onboarding-page__fields" onSubmit={handleCreate}>
          <label>
            Название семьи
            <input
              value={familyName}
              onChange={(event) => setFamilyName(event.target.value)}
              type="text"
              placeholder="Например, Беловы"
              minLength={1}
              required
            />
          </label>
          {createError && <p className="onboarding-page__error">{createError}</p>}
          <button className="onboarding-page__submit" type="submit" disabled={isCreating}>
            {isCreating ? 'Создаём...' : 'Создать семью'}
          </button>
        </form>
      </div>

      <div className="onboarding-divider">или</div>

      <div className="onboarding-card">
        <h2>Войти в семью</h2>
        <p className="onboarding-card__hint">Введите код приглашения, который вам отправили.</p>
        <form className="onboarding-page__fields" onSubmit={handleJoin}>
          <label>
            Код приглашения
            <input
              value={inviteCode}
              onChange={(event) => setInviteCode(event.target.value.toUpperCase())}
              type="text"
              placeholder="Например, A3F9K2"
              minLength={4}
              maxLength={12}
              required
            />
          </label>
          {joinError && <p className="onboarding-page__error">{joinError}</p>}
          <button className="onboarding-page__submit" type="submit" disabled={isJoining}>
            {isJoining ? 'Проверяем код...' : 'Войти в семью'}
          </button>
        </form>
      </div>
    </section>
  )
}

export default FamilyChoiceForm
