import { useCallback, useEffect, useState } from 'react'

import { useAuth } from '../../../app/providers/AuthProvider.jsx'
import { getMyFamily } from '../../../shared/api/family.ts'
import FamilyNameWidget from '../sections/FamilyNameWidget.jsx'
import BudgetWidget from '../sections/BudgetWidget.jsx'
import MemberList from '../sections/MemberList.jsx'
import InviteCodeWidget from '../sections/InviteCodeWidget.jsx'
import "./FamilyPage.css";

function FamilyPage() {
  const { user } = useAuth()
  const [familyState, setFamilyState] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

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
