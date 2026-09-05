import { NavLink } from 'react-router-dom'

const navigationItems = [
  { to: '/', label: 'Главная', end: true },
  { to: '/search', label: 'Поиск' },
  { to: '/notifications', label: 'Уведомления' },
  { to: '/profile', label: 'Профиль' },
]

function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Основная навигация">
      <nav>
        {navigationItems.map((item) => (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            end={item.end}
            key={item.to}
            to={item.to}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

export default Sidebar