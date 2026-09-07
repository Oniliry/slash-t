import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../../app/providers/AuthProvider.jsx'
import AddPurchaseButton from '../AddPurchase/AddPurchaseButton.jsx'
import { LogoutIcon, ProfileIcon } from '../TabBar/icons.jsx'

function Navbar() {
  const navigate = useNavigate()
  const { logout, user } = useAuth()

  async function handleLogout() {
    await logout()
    navigate('/auth', { replace: true })
  }

  return (
    <header className="navbar">
      <Link className="navbar__brand" to="/">
        <span className="navbar__mark">/</span>
        <span>Slash T</span>
      </Link>
      <div className="navbar__actions">
        <AddPurchaseButton variant="navbar" />
        <span className="navbar__user">
          <ProfileIcon />
          <span>{user?.name ?? 'Профиль'}</span>
        </span>
        <button
          className="navbar__logout"
          type="button"
          onClick={handleLogout}
          aria-label="Выйти"
          title="Выйти"
        >
          <LogoutIcon />
        </button>
      </div>
    </header>
  )
}

export default Navbar