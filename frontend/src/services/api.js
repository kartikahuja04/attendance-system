import axios from 'axios';

// Use Vite proxy - empty baseURL means same origin
const api = axios.create({
    baseURL: '',
    withCredentials: true,
    timeout: 10000, // 10 second timeout
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add request interceptor to attach auth token
api.interceptors.request.use(
    (config) => {
        // Get auth token from localStorage
        const user = localStorage.getItem('user');
        if (user) {
            try {
                const userData = JSON.parse(user);
                if (userData.id) {
                    // Send token as custom header
                    config.headers['X-Auth-Token'] = userData.id;
                }
            } catch (e) {
                console.error('Error parsing user data:', e);
            }
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Add response interceptor for better error handling
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        // Log the error for debugging
        console.error('[API Error]', error.config?.url, error.message);

        // If network error, throw with more context
        if (error.code === 'ERR_NETWORK' || error.code === 'ECONNRESET') {
            error.message = 'Network connection failed. The server may be restarting.';
        }

        return Promise.reject(error);
    }
);


// Auth
export const login = async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/api/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};

export const logout = () => api.get('/logout');

// Teacher
export const getSchedule = () => api.get('/api/teacher/schedule');
export const getPreviousDayStats = () => api.get('/api/teacher/previous-day-stats');
export const getProfile = () => api.get('/api/teacher/profile');
export const updateProfile = (data) => api.post('/api/teacher/profile/update', data);
export const uploadPhoto = (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/teacher/profile/upload-photo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};
export const toggleVisibility = (visible) =>
    api.post('/api/teacher/profile/visibility', { visible });

// Teacher Stats (dynamic)
export const getStats = () => api.get('/api/teacher/stats');

// Announcements
export const getAnnouncements = () => api.get('/api/announcements');
export const createAnnouncement = (content, priority = 'normal', title = null) => {
    const formData = new FormData();
    formData.append('content', content);
    formData.append('priority', priority);
    if (title) formData.append('title', title);
    return api.post('/api/announcements', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};
export const deleteAnnouncement = (id) => api.delete(`/api/announcements/${id}`);

// Directory
export const getTeachersDirectory = () => api.get('/api/teachers/directory');
export const getTeacherProfile = (id) => api.get(`/api/teachers/${id}/profile`);

// Sessions
export const getSessions = (date = null) => {
    const params = date ? { date } : {};
    return api.get('/api/sessions', { params });
};
export const getActiveSessions = () => api.get('/api/sessions/active');
export const getTeacherSchedule = () => api.get('/api/teacher/schedule');
export const createSession = (data) => {
    const formData = new FormData();
    formData.append('class_name', data.class_name);
    formData.append('subject', data.subject);
    formData.append('section', data.section);
    formData.append('start_time', data.start_time);
    return api.post('/api/sessions/create', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};
export const endSession = (sessionId) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    return api.post('/api/sessions/end', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};

// QR Code & Attendance
export const getQRCode = (sessionId) => api.get(`/api/qr/${sessionId}`);
export const getSessionAttendance = (sessionId) => api.get(`/api/attendance/${sessionId}`);
export const getAttendanceData = (sessionId) => api.get(`/api/attendance/view/${sessionId}`);
export const exportAttendance = (sessionId) =>
    api.get(`/api/attendance/export/${sessionId}`, { responseType: 'blob' });

// Schedules
export const getSchedules = () => api.get('/api/schedules');
export const createScheduleEntry = (data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => {
        if (data[key]) formData.append(key, data[key]);
    });
    return api.post('/api/schedules', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};
export const deleteScheduleEntry = (id) => api.delete(`/api/schedules/${id}`);

// Class Rosters
export const getClasses = () => api.get('/api/classes');
export const getClassStudents = (className, section) =>
    api.get(`/api/classes/${encodeURIComponent(className)}/${encodeURIComponent(section)}/students`);
export const addStudentToRoster = (className, section, studentId, studentName) => {
    const formData = new FormData();
    formData.append('student_id', studentId);
    if (studentName) formData.append('student_name', studentName);
    return api.post(`/api/classes/${encodeURIComponent(className)}/${encodeURIComponent(section)}/students`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};
export const bulkImportStudents = (className, section, students) =>
    api.post(`/api/classes/${encodeURIComponent(className)}/${encodeURIComponent(section)}/students/bulk`, { students });

export default api;

