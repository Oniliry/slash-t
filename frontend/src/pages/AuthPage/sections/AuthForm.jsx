import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../../../app/providers/AuthProvider.jsx'

import './AuthForm.css'

function AuthForm() {
  const [isRegistration, setIsRegistration] = useState(false)
  const [name, setName] = useState('')
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { login: loginUser, register } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    const normalizedLogin = login.trim()
    const response = isRegistration
      ? await register({ name: name.trim(), login: normalizedLogin, password })
      : await loginUser({ login: normalizedLogin, password })

    setIsSubmitting(false)

    if (response.error) {
      setError(response.message ?? 'Не удалось выполнить запрос.')
      return
    }

    navigate('/')
  }

  return (
    <section className="auth-page">
      <p className="page__eyebrow">Slash T</p>
      <h1>{isRegistration ? 'Создать аккаунт' : 'Войти в Slash T'}</h1>
      <p>
        {isRegistration ? 'Создайте семейное пространство.' : 'Управляйте бюджетом вместе.'}
      </p>
      <form className="auth-page__fields" onSubmit={handleSubmit}>
        {isRegistration && (
          <label>
            Имя
            <input value={name} onChange={(event) => setName(event.target.value)} type="text" placeholder="Введите имя" required />
          </label>
        )}
        <label>
          Логин
          <input
            value={login}
            onChange={(event) => setLogin(event.target.value)}
            type="text"
            placeholder="Введите логин"
            minLength={3}
            required
          />
        </label>
        <label>
          Пароль
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Введите пароль" minLength={isRegistration ? 8 : 1} required />
        </label>
        {error && <p className="auth-page__error">{error}</p>}
        <div className="auth-page__actions">
          <button className="auth-page__login" type="submit" disabled={isSubmitting}>
            {isSubmitting
              ? 'Проверяем...'
              : isRegistration
                ? 'Зарегистрироваться'
                : 'Войти'}
          </button>
        </div>
      </form>
      <div className="auth-page__actions">
        <button
          className="auth-page__toggle"
          type="button"
          onClick={() => {
            setIsRegistration((value) => !value)
            setError('')
          }}
        >
          {isRegistration ? 'У меня уже есть аккаунт' : 'Создать аккаунт'}
        </button>
      </div>
    </section>
  );
}

export default AuthForm;
