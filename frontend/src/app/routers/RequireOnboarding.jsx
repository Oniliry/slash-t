import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../providers/AuthProvider.jsx'

function RequireOnboarding() {
  const { user } = useAuth()

  if (!user) {
    return <Navigate to="/auth" replace />
  }

  if (!user.family_id) {
    return <Navigate to="/onboarding/family" replace />
  }

  if (!user.role) {
    return <Navigate to="/onboarding/role" replace />
  }

  return <Outlet />
}

export default RequireOnboarding
