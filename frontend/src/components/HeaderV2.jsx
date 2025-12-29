/**
 * Header Component
 * Top navigation bar with user menu
 */

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContextV2";

const Header = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex items-center">
          <h1 className="text-2xl font-bold text-blue-600">📚 Attendance System</h1>
        </div>

        <div className="flex items-center gap-4">
          {/* Notifications (placeholder) */}
          <button className="relative text-gray-600 hover:text-gray-900">
            🔔
            <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              2
            </span>
          </button>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center gap-2 text-gray-700 hover:text-gray-900"
            >
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                {user?.full_name?.charAt(0).toUpperCase() || "U"}
              </div>
              <span className="hidden sm:inline">{user?.email?.split("@")[0]}</span>
              <span className="text-xs">▼</span>
            </button>

            {showMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-50">
                <div className="px-4 py-2 border-b">
                  <p className="text-sm text-gray-600">Signed in as</p>
                  <p className="font-bold text-sm">{user?.email}</p>
                  <p className="text-xs text-gray-500 capitalize">{user?.role?.replace("_", " ")}</p>
                </div>

                <button
                  onClick={() => navigate("/profile")}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
                >
                  👤 My Profile
                </button>

                <button
                  onClick={() => navigate("/settings")}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
                >
                  ⚙️ Settings
                </button>

                <button
                  onClick={() => navigate("/help")}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
                >
                  ❓ Help
                </button>

                <div className="border-t">
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 hover:bg-red-50 text-red-600 text-sm font-bold"
                  >
                    🚪 Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
