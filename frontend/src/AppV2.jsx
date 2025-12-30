/**
 * Main App Component
 * Routes and layout setup for the complete attendance system
 */

import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContextV2";
import { ProtectedRoute, RoleGuard } from "./components/ProtectedRoute";

// Pages
import LandingPage from "./pages/LandingPage";
import LoginV2 from "./pages/LoginV2";
import SignupV2 from "./pages/SignupV2";
import StudentDashboard from "./pages/StudentDashboard";
import FacultyDashboard from "./pages/FacultyDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import MarkAttendancePage from "./pages/MarkAttendanceV2";

// Layout
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";

import "./App.css";

// Layout wrapper
const AppLayout = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return children;
  }

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

function AppContent() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginV2 />} />
      <Route path="/signup" element={<SignupV2 />} />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RoleGuard allowedRoles={["student", "faculty", "org_admin", "super_admin"]}>
                {/* Route based on role */}
                <RoleBasedDashboard />
              </RoleGuard>
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Student Routes */}
      <Route
        path="/student/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RoleGuard allowedRoles={["student"]}>
                <StudentDashboard />
              </RoleGuard>
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Faculty Routes */}
      <Route
        path="/faculty/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RoleGuard allowedRoles={["faculty"]}>
                <FacultyDashboard />
              </RoleGuard>
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/faculty/mark-attendance"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RoleGuard allowedRoles={["faculty"]}>
                <MarkAttendancePage />
              </RoleGuard>
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/faculty/mark-attendance/:sessionId"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RoleGuard allowedRoles={["faculty"]}>
                <MarkAttendancePage />
              </RoleGuard>
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Admin Routes */}
      <Route
        path="/admin/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RoleGuard allowedRoles={["org_admin", "super_admin"]}>
                <AdminDashboard />
              </RoleGuard>
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/admin/students"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RoleGuard allowedRoles={["org_admin", "super_admin"]}>
                <StudentManagement />
              </RoleGuard>
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/admin/faculty"
        element={
          <ProtectedRoute>
            <AppLayout>
              <RoleGuard allowedRoles={["org_admin", "super_admin"]}>
                <FacultyManagement />
              </RoleGuard>
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <AppLayout>
            <RoleBasedDashboard />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// Component to route to correct dashboard based on role
function RoleBasedDashboard() {
  const { user } = useAuth();

  switch (user?.role) {
    case "student":
      return <StudentDashboard />;
    case "faculty":
      return <FacultyDashboard />;
    case "org_admin":
    case "super_admin":
      return <AdminDashboard />;
    default:
      return <Navigate to="/login" />;
  }
}

// Placeholder components (to be implemented)
function StudentManagement() {
  return <div className="text-2xl font-bold">Student Management (Coming Soon)</div>;
}

function FacultyManagement() {
  return <div className="text-2xl font-bold">Faculty Management (Coming Soon)</div>;
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}
