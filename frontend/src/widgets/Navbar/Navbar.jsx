import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../../app/providers/AuthProvider.jsx'
import AddPurchaseButton from '../AddPurchase/AddPurchaseButton.jsx'

function Navbar() {
  const navigate = useNavigate()
  const { logout } = useAuth()

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
        <span className="navbar__status">Online</span>
        <button className="navbar__logout" type="button" onClick={handleLogout}>
          Выйти
        </button>
      </div>
    </header>
  )
}

export default Navbar