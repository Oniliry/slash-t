import { NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../../app/providers/AuthProvider.jsx'
import {
  CushionIcon,
  FamilyIcon,
  HomeIcon,
  ProfileIcon,
  ReceiptIcon,
} from '../TabBar/icons.jsx'

const navigationItems = [
  { to: '/', label: 'Главная', end: true, Icon: HomeIcon },
  { to: '/expenses', label: 'Расходы', Icon: ReceiptIcon },
  { to: '/financial-cushion', label: 'ФинПодушка', Icon: CushionIcon },
  { to: '/family', label: 'Семья', Icon: FamilyIcon },
  { to: '/profile', label: 'Профиль', Icon: ProfileIcon },
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