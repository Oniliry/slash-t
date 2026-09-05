import { Link } from 'react-router-dom'

function Navbar() {
  return (
    <header className="navbar">
      <Link className="navbar__brand" to="/">
        Slash T
      </Link>
    </header>
  )
}

export default Navbar