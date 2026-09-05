import { createBrowserRouter } from 'react-router-dom'

import MainLayout from './layouts/MainLayout/MainLayout.jsx'
import HomePage from '../pages/HomePage.jsx'
import SearchPage from '../pages/SearchPage.jsx'
import NotificationsPage from '../pages/NotificationsPage.jsx'
import ProfilePage from '../pages/ProfilePage.jsx'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'search', element: <SearchPage /> },
      { path: 'notifications', element: <NotificationsPage /> },
      { path: 'profile', element: <ProfilePage /> },
    ],
  },
])