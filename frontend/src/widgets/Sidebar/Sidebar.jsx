import { Link, NavLink } from 'react-router-dom'

const navigationItems = [
  { to: '/', label: 'Главная', end: true },
  { to: '/expenses', label: 'Расходы' },
  { to: '/family', label: 'Семья' },
  { to: '/profile', label: 'Профиль' },
]

function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Основная навигация">
      <span className="sidebar__label">Навигация</span>
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
      <Link className="sidebar__logout" to="/auth">
        Выйти
      </Link>
    </aside>
  )
}

export default Sidebar