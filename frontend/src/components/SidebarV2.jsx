/**
 * Sidebar Component
 * Navigation sidebar showing role-based menu items
 */

import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContextV2";

const Sidebar = () => {
  const { user, hasRole } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const studentMenus = [
    { label: "Dashboard", path: "/student/dashboard", icon: "📊" },
    { label: "My Attendance", path: "/student/attendance", icon: "📋" },
    { label: "Timetable", path: "/student/timetable", icon: "📅" },
    { label: "Reports", path: "/student/reports", icon: "📈" },
  ];

  const facultyMenus = [
    { label: "Dashboard", path: "/faculty/dashboard", icon: "📊" },
    { label: "Mark Attendance", path: "/faculty/mark-attendance", icon: "✓" },
    { label: "Attendance History", path: "/faculty/attendance-history", icon: "📋" },
    { label: "My Timetable", path: "/faculty/timetable", icon: "📅" },
    { label: "Reports", path: "/faculty/reports", icon: "📈" },
  ];

  const adminMenus = [
    { label: "Dashboard", path: "/admin/dashboard", icon: "📊" },
    { label: "Students", path: "/admin/students", icon: "👥" },
    { label: "Faculty", path: "/admin/faculty", icon: "👨‍🏫" },
    { label: "Subjects", path: "/admin/subjects", icon: "📚" },
    { label: "Timetables", path: "/admin/timetables", icon: "📅" },
    { label: "Rooms", path: "/admin/rooms", icon: "🏛️" },
    { label: "Batches", path: "/admin/batches", icon: "🎓" },
    { label: "Attendance Control", path: "/admin/attendance-control", icon: "🔒" },
    { label: "Reports", path: "/admin/reports", icon: "📈" },
    { label: "Audit Logs", path: "/admin/audit-logs", icon: "📜" },
  ];

  const getMenus = () => {
    if (hasRole("super_admin") || hasRole("org_admin")) {
      return adminMenus;
    } else if (hasRole("faculty")) {
      return facultyMenus;
    } else if (hasRole("student")) {
      return studentMenus;
    }
    return [];
  };

  const menus = getMenus();

  return (
    <aside className="w-64 bg-gray-900 text-white h-screen flex flex-col shadow-lg">
      {/* Logo */}
      <div className="p-6 border-b border-gray-700">
        <h2 className="text-xl font-bold">📚 Attendance</h2>
        <p className="text-xs text-gray-400 mt-1">Management System</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-2">
          {menus.map((menu) => (
            <li key={menu.path}>
              <Link
                to={menu.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  isActive(menu.path)
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-800"
                }`}
              >
                <span className="text-lg">{menu.icon}</span>
                <span className="text-sm font-medium">{menu.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {/* Role Badge */}
      <div className="p-4 border-t border-gray-700">
        <div className="bg-gray-800 rounded p-3">
          <p className="text-xs text-gray-400">Your Role</p>
          <p className="text-sm font-bold capitalize">
            {user?.role?.replace("_", " ")}
          </p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
