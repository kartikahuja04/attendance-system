/**
 * Mark Attendance Page (CRITICAL)
 * Faculty can mark attendance for a session
 */

import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContextV2";
import { useNavigate } from "react-router-dom";
import * as api from "../services/apiV2";
import "../App.css";

const MarkAttendancePage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Form data
  const [subjects, setSubjects] = useState([]);
  const [batches, setBatches] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedBatch, setSelectedBatch] = useState("");
  const [sessionDate, setSessionDate] = useState(new Date().toISOString().split("T")[0]);
  const [startTime, setStartTime] = useState("09:00:00");

  // Session & students
  const [session, setSession] = useState(null);
  const [students, setStudents] = useState([]);
  const [markings, setMarkings] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [subjectsData, batchesData] = await Promise.all([
          api.listSubjects(),
          api.listBatches(),
        ]);
        setSubjects(subjectsData.subjects || []);
        setBatches(batchesData.batches || []);
      } catch (err) {
        setError("Failed to load subjects and batches");
        console.error(err);
      }
    };
    fetchData();
  }, []);

  // Create/fetch session
  const handleSessionSetup = async (e) => {
    e.preventDefault();
    if (!selectedSubject || !selectedBatch) {
      setError("Please select subject and batch");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Get faculty ID
      const facultyData = await api.listFaculty({ limit: 1 });
      const myFaculty = facultyData.faculty.find(f => f.user_id === user.user_id);

      if (!myFaculty) {
        setError("Faculty profile not found");
        return;
      }

      // Create attendance session
      const sessionData = await api.createAttendanceSession({
        subject_id: selectedSubject,
        batch_id: selectedBatch,
        faculty_id: myFaculty._id,
        date: sessionDate,
        start_time: startTime,
      });

      // Fetch session details with students
      const sessionDetails = await api.getAttendanceSession(sessionData.session_id);
      setSession(sessionDetails.session);

      // Prepare markings object
      const newMarkings = {};
      sessionDetails.entries?.forEach(entry => {
        newMarkings[entry.student_id] = "absent";
      });
      setMarkings(newMarkings);
      setStudents(sessionDetails.entries || []);
    } catch (err) {
      setError(err.message || "Failed to create session");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Update marking for a student
  const updateMarking = (studentId, status) => {
    setMarkings(prev => ({
      ...prev,
      [studentId]: status,
    }));
  };

  // Submit attendance
  const handleSubmitAttendance = async () => {
    if (!session) {
      setError("No session selected");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await api.markAttendance(session._id, markings);
      setSuccess(true);

      setTimeout(() => {
        navigate("/faculty/attendance-history");
      }, 2000);
    } catch (err) {
      setError(err.message || "Failed to mark attendance");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Mark all as present
  const markAllPresent = () => {
    const newMarkings = {};
    students.forEach(entry => {
      newMarkings[entry.student_id] = "present";
    });
    setMarkings(newMarkings);
  };

  // Reset
  const resetMarkings = () => {
    const newMarkings = {};
    students.forEach(entry => {
      newMarkings[entry.student_id] = "absent";
    });
    setMarkings(newMarkings);
  };

  const presentCount = Object.values(markings).filter(s => s === "present").length;
  const absentCount = Object.values(markings).filter(s => s === "absent").length;
  const leaveCount = Object.values(markings).filter(s => s === "leave").length;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Mark Attendance</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
          Attendance marked successfully! Redirecting...
        </div>
      )}

      {!session ? (
        // Session Setup Form
        <form onSubmit={handleSessionSetup} className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Setup Attendance Session</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-gray-700 font-bold mb-2">Subject</label>
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="w-full border rounded px-3 py-2"
                required
              >
                <option value="">Select a subject</option>
                {subjects.map(subject => (
                  <option key={subject._id} value={subject._id}>
                    {subject.code} - {subject.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">Batch</label>
              <select
                value={selectedBatch}
                onChange={(e) => setSelectedBatch(e.target.value)}
                className="w-full border rounded px-3 py-2"
                required
              >
                <option value="">Select a batch</option>
                {batches.map(batch => (
                  <option key={batch._id} value={batch._id}>
                    {batch.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">Date</label>
              <input
                type="date"
                value={sessionDate}
                onChange={(e) => setSessionDate(e.target.value)}
                className="w-full border rounded px-3 py-2"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">Start Time</label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full border rounded px-3 py-2"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded transition"
          >
            {loading ? "Creating session..." : "Create Session & Load Students"}
          </button>
        </form>
      ) : (
        // Attendance Marking
        <div>
          {/* Session Summary */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div>
                <p className="text-gray-600 text-sm">Date</p>
                <p className="font-bold">{session.date}</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Time</p>
                <p className="font-bold">{session.start_time}</p>
              </div>
              <div className="bg-green-50 p-3 rounded">
                <p className="text-green-600 text-sm">Present</p>
                <p className="text-2xl font-bold text-green-600">{presentCount}</p>
              </div>
              <div className="bg-red-50 p-3 rounded">
                <p className="text-red-600 text-sm">Absent</p>
                <p className="text-2xl font-bold text-red-600">{absentCount}</p>
              </div>
              <div className="bg-yellow-50 p-3 rounded">
                <p className="text-yellow-600 text-sm">Leave</p>
                <p className="text-2xl font-bold text-yellow-600">{leaveCount}</p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={markAllPresent}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded transition"
            >
              ✓ Mark All Present
            </button>
            <button
              onClick={resetMarkings}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded transition"
            >
              ↻ Reset All
            </button>
          </div>

          {/* Students Table */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4">Mark Student Attendance</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-4 py-3 text-left">Roll Number</th>
                    <th className="px-4 py-3 text-left">Name</th>
                    <th className="px-4 py-3 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((entry) => (
                    <tr key={entry.student_id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono">{entry.roll_number}</td>
                      <td className="px-4 py-3">{entry.student_name}</td>
                      <td className="px-4 py-3">
                        <select
                          value={markings[entry.student_id] || "absent"}
                          onChange={(e) => updateMarking(entry.student_id, e.target.value)}
                          className={`px-3 py-1 rounded font-semibold ${
                            markings[entry.student_id] === "present"
                              ? "bg-green-100 text-green-800"
                              : markings[entry.student_id] === "leave"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          <option value="present">Present</option>
                          <option value="absent">Absent</option>
                          <option value="leave">Leave</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-2">
            <button
              onClick={handleSubmitAttendance}
              disabled={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded transition"
            >
              {loading ? "Submitting..." : "Submit Attendance"}
            </button>
            <button
              onClick={() => setSession(null)}
              className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded transition"
            >
              Back
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarkAttendancePage;
