/**
 * Faculty Dashboard
 * Shows today's classes, quick actions, and attendance statistics
 */

import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContextV2";
import { useNavigate } from "react-router-dom";
import * as api from "../services/apiV2";
import "../App.css";

const FacultyDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [faculty, setFaculty] = useState(null);
  const [timetable, setTimetable] = useState([]);
  const [stats, setStats] = useState({
    total_sessions: 0,
    locked_sessions: 0,
    pending_sessions: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch faculty details
        const facultyData = await api.listFaculty();
        if (facultyData.faculty.length > 0) {
          const myFaculty = facultyData.faculty.find(f => f.user_id === user.user_id);
          setFaculty(myFaculty);

          // Fetch timetable
          if (myFaculty && myFaculty._id) {
            const timetableData = await api.getFacultyTimetable(myFaculty._id);
            setTimetable(timetableData.timetables || []);
          }
        }
      } catch (err) {
        setError(err.message);
        console.error("Error fetching data:", err);
      } finally {
        setLoading(false);
      }
    };

    if (user?.user_id) {
      fetchData();
    }
  }, [user]);

  const getTodayClasses = () => {
    const today = new Date().toLocaleDateString("en-US", { weekday: "long" });
    return timetable.filter(t =>
      t.time_slots?.some(slot => slot.day.toLowerCase() === today.toLowerCase())
    );
  };

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

  const todayClasses = getTodayClasses();

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Faculty Dashboard</h1>
        <p className="text-gray-600">Welcome, {faculty?.full_name || user?.full_name || "Faculty"}</p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <p>{error}</p>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <button
          onClick={() => navigate("/faculty/mark-attendance")}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition"
        >
          📊 Mark Attendance
        </button>
        <button
          onClick={() => navigate("/faculty/attendance-history")}
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition"
        >
          📋 Attendance History
        </button>
        <button
          onClick={() => navigate("/faculty/timetable")}
          className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition"
        >
          📅 My Timetable
        </button>
      </div>

      {/* Today's Classes */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4">Today's Classes</h2>
        {todayClasses.length === 0 ? (
          <p className="text-gray-600">No classes scheduled for today.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {todayClasses.map((timetable_item) => (
              <div key={timetable_item._id} className="border rounded-lg p-4 hover:shadow-md transition">
                <h3 className="font-bold text-lg">{timetable_item.subject_id}</h3>
                <p className="text-gray-600">
                  {timetable_item.time_slots?.[0]?.start_time} - {timetable_item.time_slots?.[0]?.end_time}
                </p>
                <button
                  onClick={() => navigate(`/faculty/mark-attendance/${timetable_item._id}`)}
                  className="mt-3 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition"
                >
                  Mark Attendance
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <p className="text-gray-600 text-sm">Total Sessions</p>
          <p className="text-3xl font-bold text-blue-600">{stats.total_sessions}</p>
        </div>
        <div className="bg-white rounded-lg shadow-lg p-6">
          <p className="text-gray-600 text-sm">Locked Sessions</p>
          <p className="text-3xl font-bold text-green-600">{stats.locked_sessions}</p>
        </div>
        <div className="bg-white rounded-lg shadow-lg p-6">
          <p className="text-gray-600 text-sm">Pending Sessions</p>
          <p className="text-3xl font-bold text-orange-600">{stats.pending_sessions}</p>
        </div>
      </div>
    </div>
  );
};

export default FacultyDashboard;
