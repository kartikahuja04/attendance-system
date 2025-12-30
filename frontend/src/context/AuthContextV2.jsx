/**
 * Enhanced Authentication Context
 * Manages user authentication state and permissions
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import * as api from "../services/apiV2";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = () => {
      const storedUser = api.getStoredUser();
      const token = localStorage.getItem("access_token");

      if (storedUser && token) {
        setUser(storedUser);
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = useCallback(async (email, password) => {
    try {
      setError(null);
      const response = await api.login(email, password);

      // Store token and user
      api.setAuthToken(response.access_token);
      setUser(response.user);

      return response.user;
    } catch (err) {
      const errorMessage = err.message || "Login failed";
      setError(errorMessage);
      throw err;
    }
  }, []);

  const register = useCallback(async (userData, orgCode) => {
    try {
      setError(null);
      await api.register(userData, orgCode);
      return true;
    } catch (err) {
      const errorMessage = err.message || "Registration failed";
      setError(errorMessage);
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    api.logout();
    setUser(null);
    setError(null);
  }, []);

  const hasRole = useCallback((roles) => {
    if (!user) return false;
    if (typeof roles === "string") {
      return user.role === roles;
    }
    return roles.includes(user.role);
  }, [user]);

  const hasPermission = useCallback((permission) => {
    if (!user) return false;

    const permissionMap = {
      super_admin: ["*"],
      org_admin: [
        "manage_organization",
        "create_user",
        "edit_user",
        "view_users",
        "create_student",
        "edit_student",
        "view_students",
        "create_faculty",
        "edit_faculty",
        "view_faculty",
        "create_subject",
        "edit_subject",
        "view_subjects",
        "create_timetable",
        "edit_timetable",
        "view_timetable",
        "view_attendance",
        "edit_attendance",
        "export_attendance",
        "view_reports",
        "create_reports",
        "export_reports",
        "view_audit_logs",
      ],
      faculty: [
        "view_timetable",
        "mark_attendance",
        "edit_attendance",
        "view_attendance",
        "export_attendance",
        "view_reports",
        "create_reports",
        "export_reports",
      ],
      student: [
        "view_timetable",
        "view_attendance",
        "view_reports",
      ],
    };

    const userPermissions = permissionMap[user.role] || [];
    return userPermissions.includes("*") || userPermissions.includes(permission);
  }, [user]);

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    hasRole,
    hasPermission,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
