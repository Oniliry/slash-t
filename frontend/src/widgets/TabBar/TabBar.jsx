import { NavLink } from 'react-router-dom'

import AddPurchaseButton from '../AddPurchase/AddPurchaseButton.jsx'
import { FamilyIcon, HomeIcon, ProfileIcon, ReceiptIcon } from '../../shared/ui/icons.jsx'

import './TabBar.css'

const leftItems = [
  { to: '/', label: 'Главная', end: true, Icon: HomeIcon },
  { to: '/expenses', label: 'Расходы', Icon: ReceiptIcon },
]

const rightItems = [
  { to: '/family', label: 'Семья', Icon: FamilyIcon },
  { to: '/profile', label: 'Профиль', Icon: ProfileIcon },
]

function TabBar() {
  return (
    <nav className="tab-bar" aria-label="Мобильная навигация">
      {leftItems.map(({ to, label, end, Icon }) => (
        <NavLink
          className={({ isActive }) => `tab-bar__link${isActive ? ' tab-bar__link--active' : ''}`}
          end={end}
          key={to}
          to={to}
          aria-label={label}
        >
          <Icon />
          <span className="tab-bar__visually-hidden">{label}</span>
        </NavLink>
      ))}
      <AddPurchaseButton variant="tabbar" />
      {rightItems.map(({ to, label, end, Icon }) => (
        <NavLink
          className={({ isActive }) => `tab-bar__link${isActive ? ' tab-bar__link--active' : ''}`}
          end={end}
          key={to}
          to={to}
          aria-label={label}
        >
          <Icon />
          <span className="tab-bar__visually-hidden">{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

export default TabBar