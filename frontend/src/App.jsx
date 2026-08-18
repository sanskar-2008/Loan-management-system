import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import OrganizationList from './pages/organizations/OrganizationList'
import OrganizationCreate from './pages/organizations/OrganizationCreate'
import OrganizationDetail from './pages/organizations/OrganizationDetail'
import LoanList from './pages/loans/LoanList'
import LoanCreate from './pages/loans/LoanCreate'
import LoanDetail from './pages/loans/LoanDetail'
import EmiList from './pages/emis/EmiList'
import PaymentList from './pages/payments/PaymentList'
import PaymentCreate from './pages/payments/PaymentCreate'
import PaymentDetail from './pages/payments/PaymentDetail'
import ReportsHub from './pages/reports/ReportsHub'
import {
  CollectionsReport,
  InterestReport,
  OrganizationStatement,
  OverdueReport,
  PortfolioReport,
} from './pages/reports/ReportPages'
import SettingsPage from './pages/Settings'
import ChangePassword from './pages/ChangePassword'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/organizations" element={<OrganizationList />} />
              <Route path="/organizations/new" element={<OrganizationCreate />} />
              <Route path="/organizations/:id" element={<OrganizationDetail />} />
              <Route path="/loans" element={<LoanList />} />
              <Route path="/loans/new" element={<LoanCreate />} />
              <Route path="/loans/:id" element={<LoanDetail />} />
              <Route path="/emis" element={<EmiList />} />
              <Route path="/payments" element={<PaymentList />} />
              <Route path="/payments/new" element={<PaymentCreate />} />
              <Route path="/payments/:id" element={<PaymentDetail />} />
              <Route path="/reports" element={<ReportsHub />} />
              <Route path="/reports/portfolio" element={<PortfolioReport />} />
              <Route path="/reports/collections" element={<CollectionsReport />} />
              <Route path="/reports/overdue" element={<OverdueReport />} />
              <Route path="/reports/interest" element={<InterestReport />} />
              <Route path="/reports/organization/:id" element={<OrganizationStatement />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/change-password" element={<ChangePassword />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
