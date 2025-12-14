import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, logout as apiLogout } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user is logged in (you can add a /api/me endpoint)
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (e) {
                localStorage.removeItem('user');
            }
        }
        setLoading(false);
    }, []);

    const login = async (username, password) => {
        try {
            console.log('[Auth] Attempting login...');
            const response = await apiLogin(username, password);
            console.log('[Auth] Login response:', response.data);

            const userData = {
                username,
                id: response.data?.user?.id
            };
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));
            return { success: true };
        } catch (error) {
            console.error('[Auth] Login error:', error);

            // Handle different error types
            let errorMessage = 'Login failed';

            if (error.response?.data?.detail) {
                // Server returned an error
                errorMessage = error.response.data.detail;
            } else if (error.code === 'ERR_NETWORK' || error.code === 'ECONNRESET') {
                // Network error
                errorMessage = 'Network error. Server may be restarting. Please try again.';
            } else if (error.code === 'ECONNABORTED') {
                // Timeout
                errorMessage = 'Request timed out. Please try again.';
            } else if (error.message) {
                errorMessage = error.message;
            }

            return { success: false, error: errorMessage };
        }
    };

    const logout = async () => {
        try {
            await apiLogout();
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setUser(null);
            localStorage.removeItem('user');
        }
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};
