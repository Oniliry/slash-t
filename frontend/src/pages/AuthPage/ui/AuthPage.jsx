import { Navigate } from 'react-router-dom'

import { useAuth } from '../../../app/providers/AuthProvider.jsx'
import AuthForm from "../sections/AuthForm.jsx";

function AuthPage() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <div>Проверяем авторизацию...</div>
  }

  if (user) {
    return <Navigate to="/" replace />
  }

  return <AuthForm />;
}

export default AuthPage;
