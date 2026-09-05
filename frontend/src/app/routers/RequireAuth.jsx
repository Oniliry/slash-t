import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../providers/AuthProvider.jsx'

function RequireAuth() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <div>Проверяем авторизацию...</div>
  }

  if (!user) {
    return <Navigate to="/auth" replace state={{ from: location }} />
  }

  return <Outlet />
}

export default RequireAuth