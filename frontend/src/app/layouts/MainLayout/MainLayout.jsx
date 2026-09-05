import { Outlet } from 'react-router-dom'

import Navbar from '../../../widgets/Navbar/Navbar.jsx'
import Sidebar from '../../../widgets/Sidebar/Sidebar.jsx'
import TabBar from '../../../widgets/TabBar/TabBar.jsx'
import './MainLayout.css'

function MainLayout() {
  return (
    <div className="main-layout">
      <Navbar />
      <div className="main-layout__body">
        <Sidebar />
        <main className="main-layout__content">
          <Outlet />
        </main>
      </div>
      <TabBar />
    </div>
  )
}

export default MainLayout