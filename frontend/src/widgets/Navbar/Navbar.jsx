import { Link } from 'react-router-dom'

function Navbar() {
  return (
    <header className="navbar">
      <Link className="navbar__brand" to="/">
        <span className="navbar__mark">/</span>
        <span>Slash T</span>
      </Link>
      <div className="navbar__actions">
        <span className="navbar__status">Online</span>
        <Link className="navbar__logout" to="/auth">
          Выйти
        </Link>
      </div>
    </header>
  )
}

export default Navbar