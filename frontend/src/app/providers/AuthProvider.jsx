import { createContext, useContext, useEffect, useState } from 'react'

import { getCurrentUser, loginUser, logoutUser, registerUser } from '../../shared/api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    getCurrentUser()
      .then((response) => {
        if (!response.error && response.data) {
          setUser(response.data)
        }
      })
      .finally(() => setIsLoading(false))
  }, [])

  async function login(credentials) {
    const response = await loginUser(credentials)

    if (!response.error && response.data) {
      setUser(response.data)
    }

    return response
  }

  async function register(credentials) {
    const response = await registerUser(credentials)

    if (!response.error && response.data) {
      setUser(response.data)
    }

    return response
  }

  async function logout() {
    const response = await logoutUser()
    setUser(null)
    return response
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
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