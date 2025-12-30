/**
 * Student Dashboard
 * Shows attendance summary, subject-wise attendance, and eligibility status
 */

import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContextV2";
import * as api from "../services/apiV2";
import "../App.css";

const StudentDashboard = () => {
  const { user } = useAuth();
  const [attendanceSummary, setAttendanceSummary] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch attendance summary
        if (user?.user_id) {
          const summary = await api.getStudentAttendanceSummary(user.user_id);
          setAttendanceSummary(summary);
        }

        // Fetch subjects
        const subjectsData = await api.listSubjects();
        setSubjects(subjectsData.subjects || []);
      } catch (err) {
        setError(err.message);
        console.error("Error fetching data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const getAttendanceColor = (percentage) => {
    if (percentage >= 75) return "text-green-600";
    if (percentage >= 65) return "text-yellow-600";
    return "text-red-600";
  };

  const getEligibilityStatus = (percentage) => {
    return percentage >= 75 ? "Eligible" : "Ineligible";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading attendance data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Attendance Dashboard</h1>
        <p className="text-gray-600">Welcome, {user?.full_name || "Student"}</p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <p>{error}</p>
        </div>
      )}

      {/* Overall Summary Card */}
      {attendanceSummary && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Overall Attendance Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <p className="text-gray-600 text-sm">Total Classes</p>
              <p className="text-2xl font-bold text-blue-600">
                {attendanceSummary.total_classes}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <p className="text-gray-600 text-sm">Present</p>
              <p className="text-2xl font-bold text-green-600">
                {attendanceSummary.present}
              </p>
            </div>
            <div className="bg-red-50 p-4 rounded">
              <p className="text-gray-600 text-sm">Absent</p>
              <p className="text-2xl font-bold text-red-600">
                {attendanceSummary.absent}
              </p>
            </div>
            <div className="bg-yellow-50 p-4 rounded">
              <p className="text-gray-600 text-sm">On Leave</p>
              <p className="text-2xl font-bold text-yellow-600">
                {attendanceSummary.leave}
              </p>
            </div>
            <div className={`${getAttendanceColor(attendanceSummary.attendance_percentage).replace("text-", "bg-").replace("600", "50")} p-4 rounded`}>
              <p className="text-gray-600 text-sm">Attendance %</p>
              <p className={`text-2xl font-bold ${getAttendanceColor(attendanceSummary.attendance_percentage)}`}>
                {attendanceSummary.attendance_percentage.toFixed(2)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Eligibility Status */}
      {attendanceSummary && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Eligibility Status</h2>
          <div className="flex items-center gap-4">
            <div className={`px-4 py-2 rounded-lg font-bold ${
              getEligibilityStatus(attendanceSummary.attendance_percentage) === "Eligible"
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}>
              {getEligibilityStatus(attendanceSummary.attendance_percentage)}
            </div>
            <p className="text-gray-600">
              Minimum 75% attendance required. You have {attendanceSummary.attendance_percentage.toFixed(2)}%
            </p>
          </div>
        </div>
      )}

      {/* Subject-wise Attendance */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Subject-wise Attendance</h2>
        {subjects.length === 0 ? (
          <p className="text-gray-600">No subjects found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-3 text-left">Subject Code</th>
                  <th className="px-4 py-3 text-left">Subject Name</th>
                  <th className="px-4 py-3 text-left">Department</th>
                  <th className="px-4 py-3 text-right">Semester</th>
                </tr>
              </thead>
              <tbody>
                {subjects.map((subject) => (
                  <tr key={subject._id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono">{subject.code}</td>
                    <td className="px-4 py-3">{subject.name}</td>
                    <td className="px-4 py-3">{subject.department}</td>
                    <td className="px-4 py-3 text-right">{subject.semester}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentDashboard;
