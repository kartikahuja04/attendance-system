/**
 * API Service - Handles all backend communication
 * Production-ready with error handling and auth
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

// Get token from localStorage
const getToken = () => localStorage.getItem("access_token");

// API Request wrapper
const apiCall = async (method, endpoint, data = null) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const options = {
    method,
    headers,
  };

  if (data && method !== "GET") {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url, options);

    if (response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem("access_token");
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${method} ${endpoint}]:`, error);
    throw error;
  }
};

// ============ AUTH ENDPOINTS ============

export const login = (email, password) =>
  apiCall("POST", "/auth/login", { email, password });

export const register = (userData, orgCode) =>
  apiCall("POST", `/auth/register?org_code=${orgCode}`, userData);

export const getProfile = () => apiCall("GET", "/auth/me");

export const logout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  return Promise.resolve();
};

// ============ ORGANIZATION ENDPOINTS ============

export const createOrganization = (orgData) =>
  apiCall("POST", "/organizations/organizations", orgData);

export const getOrganization = (orgId) =>
  apiCall("GET", `/organizations/organizations/${orgId}`);

export const updateOrganization = (orgId, orgData) =>
  apiCall("PUT", `/organizations/organizations/${orgId}`, orgData);

// ============ STUDENT ENDPOINTS ============

export const createStudent = (studentData) =>
  apiCall("POST", "/students/students", studentData);

export const listStudents = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return apiCall("GET", `/students/students?${query}`);
};

export const getStudent = (studentId) =>
  apiCall("GET", `/students/students/${studentId}`);

export const updateStudent = (studentId, studentData) =>
  apiCall("PUT", `/students/students/${studentId}`, studentData);

export const deleteStudent = (studentId) =>
  apiCall("DELETE", `/students/students/${studentId}`);

// ============ FACULTY ENDPOINTS ============

export const createFaculty = (facultyData) =>
  apiCall("POST", "/faculty/faculty", facultyData);

export const listFaculty = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return apiCall("GET", `/faculty/faculty?${query}`);
};

export const getFaculty = (facultyId) =>
  apiCall("GET", `/faculty/faculty/${facultyId}`);

export const updateFaculty = (facultyId, facultyData) =>
  apiCall("PUT", `/faculty/faculty/${facultyId}`, facultyData);

export const deleteFaculty = (facultyId) =>
  apiCall("DELETE", `/faculty/faculty/${facultyId}`);

// ============ SUBJECT ENDPOINTS ============

export const createSubject = (subjectData) =>
  apiCall("POST", "/timetables/subjects", subjectData);

export const listSubjects = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return apiCall("GET", `/timetables/subjects?${query}`);
};

// ============ BATCH ENDPOINTS ============

export const createBatch = (batchData) =>
  apiCall("POST", "/timetables/batches", batchData);

export const listBatches = () =>
  apiCall("GET", "/timetables/batches");

// ============ ROOM ENDPOINTS ============

export const createRoom = (roomData) =>
  apiCall("POST", "/timetables/rooms", roomData);

export const listRooms = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return apiCall("GET", `/timetables/rooms?${query}`);
};

// ============ TIMETABLE ENDPOINTS ============

export const createTimetable = (timetableData) =>
  apiCall("POST", "/timetables/timetables", timetableData);

export const getFacultyTimetable = (facultyId) =>
  apiCall("GET", `/timetables/timetables/faculty/${facultyId}`);

export const getBatchTimetable = (batchId) =>
  apiCall("GET", `/timetables/timetables/batch/${batchId}`);

// ============ ATTENDANCE ENDPOINTS ============

export const createAttendanceSession = (sessionData) =>
  apiCall("POST", "/attendance/sessions", sessionData);

export const getAttendanceSession = (sessionId) =>
  apiCall("GET", `/attendance/sessions/${sessionId}`);

export const markAttendance = (sessionId, markings) =>
  apiCall("POST", `/attendance/sessions/${sessionId}/mark`, markings);

export const lockAttendanceSession = (sessionId) =>
  apiCall("POST", `/attendance/sessions/${sessionId}/lock`, {});

// ============ REPORTS & EXPORTS ENDPOINTS ============

export const getStudentAttendanceSummary = (studentId, params = {}) => {
  const query = new URLSearchParams(params).toString();
  return apiCall("GET", `/reports/attendance/student/${studentId}/summary?${query}`);
};

export const getSubjectAttendanceReport = (subjectId, params = {}) => {
  const query = new URLSearchParams(params).toString();
  return apiCall("GET", `/reports/attendance/subject/${subjectId}/report?${query}`);
};

export const createExport = (exportData) =>
  apiCall("POST", "/reports/exports", exportData);

export const getExportStatus = (exportId) =>
  apiCall("GET", `/reports/exports/${exportId}`);

// ============ UTILITY FUNCTIONS ============

export const setAuthToken = (token) => {
  localStorage.setItem("access_token", token);
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      localStorage.setItem("user", JSON.stringify({
        user_id: payload.user_id,
        email: payload.email,
        role: payload.role,
        organization_id: payload.organization_id,
      }));
    } catch (error) {
      console.error("Error parsing token:", error);
    }
  }
};

export const getStoredUser = () => {
  const userStr = localStorage.getItem("user");
  return userStr ? JSON.parse(userStr) : null;
};

export default {
  login,
  register,
  getProfile,
  logout,
  createOrganization,
  getOrganization,
  updateOrganization,
  createStudent,
  listStudents,
  getStudent,
  updateStudent,
  deleteStudent,
  createFaculty,
  listFaculty,
  getFaculty,
  updateFaculty,
  deleteFaculty,
  createSubject,
  listSubjects,
  createBatch,
  listBatches,
  createRoom,
  listRooms,
  createTimetable,
  getFacultyTimetable,
  getBatchTimetable,
  createAttendanceSession,
  getAttendanceSession,
  markAttendance,
  lockAttendanceSession,
  getStudentAttendanceSummary,
  getSubjectAttendanceReport,
  createExport,
  getExportStatus,
  setAuthToken,
  getStoredUser,
};
