const BASE_URL = "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("token");
}

export async function loginUser(email, password) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  return res.json();
}

export async function getAttendance(sessionId) {
  const res = await fetch(`${BASE_URL}/attendance/${sessionId}`, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  });
  return res.json();
}

export function exportAttendance(sessionId) {
  window.open(`${BASE_URL}/attendance/export/${sessionId}`, "_blank", {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  });
}
