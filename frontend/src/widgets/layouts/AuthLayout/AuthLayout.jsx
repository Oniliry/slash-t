import { Link, Outlet } from 'react-router-dom'

import './AuthLayout.css'

function AuthLayout() {
  return (
    <div className="auth-layout">
      <header className="auth-layout__header">
        <Link className="auth-layout__brand" to="/">
          <span className="auth-layout__mark">/</span>
          <span>Slash T</span>
        </Link>
      </header>
      <main className="auth-layout__main">
        <Outlet />
      </main>
    </div>
  )
}

export default AuthLayout