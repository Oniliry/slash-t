import { Outlet } from 'react-router-dom'

import Navbar from '../../Navbar/Navbar.jsx'
import Sidebar from '../../Sidebar/Sidebar.jsx'
import TabBar from '../../TabBar/TabBar.jsx'
import './MainLayout.css'

function MainLayout() {
  return (
    <div className="main-layout">
      <Navbar />
      <div className="main-layout__body">
        <Sidebar />
        <main className="main-layout__main">
          <div className="main-layout__content">
            <Outlet />
          </div>
        </main>
      </div>
      <TabBar />
    </div>
  )
}

export default MainLayout