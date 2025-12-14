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

// Directory
export const getTeachersDirectory = () => api.get('/api/teachers/directory');
export const getTeacherProfile = (id) => api.get(`/api/teachers/${id}/profile`);

// Sessions
export const getSessions = () => api.get('/api/sessions');
export const getActiveSessions = () => api.get('/api/sessions/active');

export default api;
