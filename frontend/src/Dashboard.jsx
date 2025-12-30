import { useEffect, useState } from "react";

const BASE_URL = "http://127.0.0.1:8000";

export default function Dashboard() {
  const [attendance, setAttendance] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      setError("Not authenticated");
      return;
    }

    fetch(`${BASE_URL}/attendance/S001`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Unauthorized");
        return res.json();
      })
      .then((data) => {
        setAttendance(data.attendance || []);
      })
      .catch(() => {
        setError("Failed to load attendance");
      });
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h2>Dashboard</h2>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <ul>
        {attendance.map((a, i) => (
          <li key={i}>
            {a.student_id} — {a.timestamp}
          </li>
        ))}
      </ul>
    </div>
  );
}
