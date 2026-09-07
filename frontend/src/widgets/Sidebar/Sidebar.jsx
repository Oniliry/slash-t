import { NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../../app/providers/AuthProvider.jsx'
import { FamilyIcon, HomeIcon, ProfileIcon, ReceiptIcon } from '../TabBar/icons.jsx'

const navigationItems = [
  { to: '/', label: 'Главная', end: true },
  { to: '/expenses', label: 'Расходы' },
  { to: '/family', label: 'Семья' },
  { to: '/profile', label: 'Профиль' },
]

function Sidebar() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  async function handleLogout() {
    await logout()
    navigate('/auth', { replace: true })
  }

  return (
    <aside className="sidebar" aria-label="Основная навигация">
      <span className="sidebar__label">Навигация</span>
      <nav>
        {navigationItems.map(({ to, label, end, Icon }) => (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            end={end}
            key={to}
            to={to}
          >
            <Icon />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <button className="sidebar__logout" type="button" onClick={handleLogout}>
        Выйти
      </button>
    </aside>
  )
}

export default Sidebar