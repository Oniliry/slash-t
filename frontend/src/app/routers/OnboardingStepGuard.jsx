import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../providers/AuthProvider.jsx'

/**
 * Следит за порядком шагов онбординга: "войти в семью/создать семью" -> "роль".
 *
 * Если у пользователя уже есть и семья, и роль — онбординг пройден, отправляем
 * его сразу на главную. Если пользователь пытается открыть шаг "роль" раньше,
 * чем присоединился к семье, возвращаем его на шаг выбора семьи.
 */
function OnboardingStepGuard() {
  const { user } = useAuth()
  const location = useLocation()

  if (!user) {
    return <Navigate to="/auth" replace />
  }

  if (user.family_id && user.role) {
    return <Navigate to="/" replace />
  }

  const isRoleStep = location.pathname.startsWith('/onboarding/role')
  if (isRoleStep && !user.family_id) {
    return <Navigate to="/onboarding/family" replace />
  }

  return <Outlet />
}

export default OnboardingStepGuard
