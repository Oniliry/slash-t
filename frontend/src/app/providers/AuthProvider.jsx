import { createContext, useContext, useEffect, useState } from 'react'

import { getCurrentUser, loginUser, logoutUser, registerUser } from '../../shared/api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    setIsLoading(true) // Явно включаем загрузку перед проверкой
    getCurrentUser()
      .then((response) => {
        if (response && !response.error && response.data) {
          setUser(response.data)
        } else {
          setUser(null) // Если бэкенд ответил ошибкой 401 — пользователя точно нет
        }
      })
      .catch((err) => {
        console.error("Ошибка проверки сессии:", err)
        setUser(null)
      })
      .finally(() => setIsLoading(false))
  }, [])


  async function login(credentials) {
    const response = await loginUser(credentials)

    if (!response.error && response.data) {
      setUser(response.data.user)
    }

    return response
  }

  async function register(credentials) {
    const response = await registerUser(credentials)

    if (!response.error && response.data) {
      setUser(response.data.user)
    }

    return response
  }

  async function logout() {
    const response = await logoutUser()
    setUser(null)
    return response
  }

  async function refreshUser() {
    const response = await getCurrentUser()

    if (!response.error && response.data) {
      setUser(response.data)
    }

    return response
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth должен использоваться внутри AuthProvider.')
  }

  return context
}