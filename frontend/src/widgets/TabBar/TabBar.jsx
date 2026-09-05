import { NavLink } from 'react-router-dom'

const navigationItems = [
  { to: '/', label: 'Главная', end: true },
  { to: '/search', label: 'Поиск' },
  { to: '/notifications', label: 'Уведомления' },
  { to: '/profile', label: 'Профиль' },
]

function TabBar() {
  return (
    <nav className="tab-bar" aria-label="Мобильная навигация">
      {navigationItems.map((item) => (
        <NavLink
          className={({ isActive }) => `tab-bar__link${isActive ? ' tab-bar__link--active' : ''}`}
          end={item.end}
          key={item.to}
          to={item.to}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}

export default TabBar