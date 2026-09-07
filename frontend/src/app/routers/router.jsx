import { Routes, Route } from 'react-router-dom'

import MainLayout from '../../widgets/layouts/MainLayout/MainLayout.jsx'
import AuthLayout from '../../widgets/layouts/AuthLayout/AuthLayout.jsx'
import RequireAuth from './RequireAuth.jsx'
import RequireOnboarding from './RequireOnboarding.jsx'
import OnboardingStepGuard from './OnboardingStepGuard.jsx'
import AuthPage from '../../pages/AuthPage/ui/AuthPage.jsx'
import FamilyChoicePage from '../../pages/OnboardingPage/ui/FamilyChoicePage.jsx'
import RoleChoicePage from '../../pages/OnboardingPage/ui/RoleChoicePage.jsx'
import HomePage from '../../pages/HomePage/ui/HomePage.jsx'
import ExpensesPage from '../../pages/ExpensesPage/ui/ExpensesPage.jsx'
import FamilyPage from '../../pages/FamilyPage/ui/FamilyPage.jsx'
import ProfilePage from '../../pages/ProfilePage/ui/ProfilePage.jsx'
import FinancialCushionPage from '../../pages/FinancialCushionPage/ui/CushionPage.jsx'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/auth" element={<AuthPage />} />
      </Route>

      <Route element={<RequireAuth />}>
        <Route element={<OnboardingStepGuard />}>
          <Route element={<AuthLayout />}>
            <Route path="/onboarding/family" element={<FamilyChoicePage />} />
            <Route path="/onboarding/role" element={<RoleChoicePage />} />
          </Route>
        </Route>

        <Route element={<RequireOnboarding />}>
          <Route element={<MainLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/expenses" element={<ExpensesPage />} />
            <Route path="/financial-cushion" element={<FinancialCushionPage />} />
            <Route path="/family" element={<FamilyPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  )
}

export default AppRouter