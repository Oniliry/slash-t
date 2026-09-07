import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../../../app/providers/AuthProvider.jsx'
import { getMyFamily, leaveFamily } from '../../../shared/api/family.ts'
import FamilyNameWidget from '../sections/FamilyNameWidget.jsx'
import BudgetWidget from '../sections/BudgetWidget.jsx'
import MemberList from '../sections/MemberList.jsx'
import InviteCodeWidget from '../sections/InviteCodeWidget.jsx'
import "./FamilyPage.css";

function FamilyPage() {
  const navigate = useNavigate()
  const { user, refreshUser } = useAuth()
  const [familyState, setFamilyState] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isLeaving, setIsLeaving] = useState(false)

  const loadFamily = useCallback(async () => {
    const response = await getMyFamily()

    if (response.error) {
      setError(response.message ?? 'Не удалось загрузить данные семьи.')
      return
    }

    setError('')
    setFamilyState(response.data)
  }, [])

  useEffect(() => {
    setIsLoading(true)
    loadFamily().finally(() => setIsLoading(false))
  }, [loadFamily])

  async function handleLeaveFamily() {
    if (!window.confirm('Покинуть текущую семью?')) return

    setIsLeaving(true)
    setError('')
    const response = await leaveFamily()

    if (response.error) {
      setError(response.message ?? 'Не удалось покинуть семью.')
      setIsLeaving(false)
      return
    }

    await refreshUser()
    navigate('/onboarding/family', { replace: true })
  }

  return (
    <section className="page">
      <header className="page__header">
        <div>
          <p className="page__eyebrow">Семейное пространство</p>
          <h1>Семья</h1>
          <p className="page__lead">
            Роли, доходы и честное распределение общих покупок.
          </p>
        </div>
      </header>

      {isLoading && <p className="page__lead">Загружаем данные семьи...</p>}
      {!isLoading && error && <p className="page__lead">{error}</p>}

      {!isLoading && familyState && (
        <>
          <FamilyNameWidget
            family={familyState.family}
            isAdmin={familyState.family.created_by === user?.id}
            onChanged={loadFamily}
            onLeave={handleLeaveFamily}
            isLeaving={isLeaving}
          />
          <BudgetWidget
            members={familyState.members}
            isAdmin={familyState.family.created_by === user?.id}
            onChanged={loadFamily}
          />
          <MemberList
            members={familyState.members}
            isAdmin={familyState.family.created_by === user?.id}
            currentUserId={user?.id}
            onChanged={loadFamily}
          />
          <InviteCodeWidget inviteCode={familyState.family.invite_code} />
        </>
      )}
    </section>
  );
}

export default FamilyPage;
