import { useState } from 'react'
import { Link } from 'react-router-dom'

import './AuthForm.css'

function AuthForm() {
  const [isRegistration, setIsRegistration] = useState(false)

  return (
    <section className="auth-page">
      <p className="page__eyebrow">Slash T</p>
      <h1>{isRegistration ? 'Создать аккаунт' : 'Войти в Slash T'}</h1>
      <p>{isRegistration ? 'Создайте семейное пространство.' : 'Управляйте бюджетом вместе.'}</p>
      <div className="auth-page__fields">
        {isRegistration && <label>Имя<input type="text" placeholder="Введите имя" /></label>}
        <label>Логин<input type="text" placeholder="Введите логин" /></label>
        <label>Пароль<input type="password" placeholder="Введите пароль" /></label>
      </div>
      <div className="auth-page__actions">
        <Link className="auth-page__login" to="/">Войти</Link>
        <button className="auth-page__toggle" type="button" onClick={() => setIsRegistration((value) => !value)}>{isRegistration ? 'У меня уже есть аккаунт' : 'Создать аккаунт'}</button>
      </div>
    </section>
  )
}

export default AuthForm