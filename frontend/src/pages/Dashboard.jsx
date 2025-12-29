import { useState } from "react";
import { getAttendance, exportAttendance } from "../api";

export default function Dashboard() {
  const [sessionId, setSessionId] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const fetchAttendance = async () => {
    setError("");
    setData(null);

    if (!sessionId.trim()) {
      setError("Please enter a session ID");
      return;
    }

    try {
      const res = await getAttendance(sessionId);

      if (res.detail || res.message) {
        setError(res.detail || res.message);
      } else {
        setData(res);
      }
    } catch (err) {
      setError("Failed to fetch attendance");
    }
  };

  return (
    <div style={{ maxWidth: "900px", margin: "30px auto" }}>
      <h2>Attendance Dashboard</h2>

      <div style={{ marginBottom: "15px" }}>
        <input
          placeholder="Enter Session ID (e.g. S001)"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          style={{ padding: "6px", marginRight: "10px" }}
        />
        <button onClick={fetchAttendance}>Fetch</button>
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {data && (
        <>
          <h3>Session Details</h3>
          <p><b>Subject:</b> {data.session.subject}</p>
          <p>
            <b>Class:</b> {data.session.class_name} - {data.session.section}
          </p>
          <p><b>Date:</b> {data.session.date}</p>

          <h3>Present Students</h3>
          <table border="1" cellPadding="8" width="100%">
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {data.attendance.length === 0 ? (
                <tr>
                  <td colSpan="2" align="center">
                    No attendance found
                  </td>
                </tr>
              ) : (
                data.attendance.map((s) => (
                  <tr key={s.id}>
                    <td>{s.student_id}</td>
                    <td>{s.timestamp}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          <br />
          <button onClick={() => exportAttendance(sessionId)}>
            Export Excel
          </button>
        </>
      )}
    </div>
  );
}
