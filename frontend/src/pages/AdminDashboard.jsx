/**
 * Admin Dashboard
 * KPI cards, attendance overview, quick management actions
 */

import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContextV2";
import { useNavigate } from "react-router-dom";
import * as api from "../services/apiV2";
import "../App.css";

const AdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_students: 0,
    total_faculty: 0,
    total_subjects: 0,
    total_batches: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all statistics
        const [studentsData, facultyData, subjectsData, batchesData] = await Promise.all([
          api.listStudents({ limit: 1 }),
          api.listFaculty({ limit: 1 }),
          api.listSubjects(),
          api.listBatches(),
        ]);

        setStats({
          total_students: studentsData.total || 0,
          total_faculty: facultyData.total || 0,
          total_subjects: subjectsData.total || 0,
          total_batches: batchesData.total || 0,
        });
      } catch (err) {
        setError(err.message);
        console.error("Error fetching statistics:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Admin Dashboard</h1>
        <p className="text-gray-600">Organization Overview & Management</p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <p>{error}</p>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg shadow-lg p-6">
          <p className="text-sm opacity-90">Total Students</p>
          <p className="text-3xl font-bold mt-2">{stats.total_students}</p>
          <button
            onClick={() => navigate("/admin/students")}
            className="text-xs mt-3 opacity-75 hover:opacity-100 transition"
          >
            Manage →
          </button>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-lg shadow-lg p-6">
          <p className="text-sm opacity-90">Total Faculty</p>
          <p className="text-3xl font-bold mt-2">{stats.total_faculty}</p>
          <button
            onClick={() => navigate("/admin/faculty")}
            className="text-xs mt-3 opacity-75 hover:opacity-100 transition"
          >
            Manage →
          </button>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-lg shadow-lg p-6">
          <p className="text-sm opacity-90">Total Subjects</p>
          <p className="text-3xl font-bold mt-2">{stats.total_subjects}</p>
          <button
            onClick={() => navigate("/admin/subjects")}
            className="text-xs mt-3 opacity-75 hover:opacity-100 transition"
          >
            Manage →
          </button>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 text-white rounded-lg shadow-lg p-6">
          <p className="text-sm opacity-90">Total Batches</p>
          <p className="text-3xl font-bold mt-2">{stats.total_batches}</p>
          <button
            onClick={() => navigate("/admin/batches")}
            className="text-xs mt-3 opacity-75 hover:opacity-100 transition"
          >
            Manage →
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Student Management</h2>
          <div className="space-y-2">
            <button
              onClick={() => navigate("/admin/students/new")}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition"
            >
              ➕ Add New Student
            </button>
            <button
              onClick={() => navigate("/admin/students/bulk-import")}
              className="w-full bg-blue-400 hover:bg-blue-500 text-white px-4 py-2 rounded transition"
            >
              📤 Bulk Import Students
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Faculty Management</h2>
          <div className="space-y-2">
            <button
              onClick={() => navigate("/admin/faculty/new")}
              className="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded transition"
            >
              ➕ Add New Faculty
            </button>
            <button
              onClick={() => navigate("/admin/faculty/assignments")}
              className="w-full bg-green-400 hover:bg-green-500 text-white px-4 py-2 rounded transition"
            >
              📋 Manage Assignments
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Timetable Management</h2>
          <div className="space-y-2">
            <button
              onClick={() => navigate("/admin/timetables")}
              className="w-full bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded transition"
            >
              📅 Manage Timetables
            </button>
            <button
              onClick={() => navigate("/admin/rooms")}
              className="w-full bg-purple-400 hover:bg-purple-500 text-white px-4 py-2 rounded transition"
            >
              🏛️ Manage Rooms
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Reports & Exports</h2>
          <div className="space-y-2">
            <button
              onClick={() => navigate("/admin/reports")}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded transition"
            >
              📊 View Reports
            </button>
            <button
              onClick={() => navigate("/admin/exports")}
              className="w-full bg-orange-400 hover:bg-orange-500 text-white px-4 py-2 rounded transition"
            >
              📥 Manage Exports
            </button>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">System Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-4 rounded">
            <p className="text-gray-600 text-sm">Organization ID</p>
            <p className="font-mono text-sm mt-1">{user?.organization_id?.substring(0, 16)}...</p>
          </div>
          <div className="bg-gray-50 p-4 rounded">
            <p className="text-gray-600 text-sm">Your Role</p>
            <p className="font-bold mt-1 capitalize">{user?.role?.replace("_", " ")}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded">
            <p className="text-gray-600 text-sm">Your Email</p>
            <p className="text-sm mt-1">{user?.email}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
