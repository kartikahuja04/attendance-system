import { createContext, useContext, useState, useEffect } from 'react';
import api, { login as apiLogin, logout as apiLogout, signup as apiSignup, me as apiMe } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const init = async () => {
            const storedUser = localStorage.getItem('user');
            if (storedUser) {
                try {
                    const parsed = JSON.parse(storedUser);
                    setUser(parsed);
                    // Validate token and refresh user profile
                    try {
                        const res = await api.get('/api/auth/me');
                        const merged = { ...parsed, ...res.data.user };
                        setUser(merged);
                        localStorage.setItem('user', JSON.stringify(merged));
                    } catch (e) {
                        // Token invalid; clear session
                        localStorage.removeItem('user');
                        setUser(null);
                    }
                } catch (e) {
                    localStorage.removeItem('user');
                    setUser(null);
                }
            }
            setLoading(false);
        };
        init();
    }, []);

    const login = async (username, password) => {
        try {
            console.log('[Auth] Attempting login...');
            // Treat username as email for JWT auth
            const response = await apiLogin(username, password);
            console.log('[Auth] Login response:', response.data);

            const userData = {
                token: response.data?.token,
                id: response.data?.user?.id,
                name: response.data?.user?.name,
                email: response.data?.user?.email,
                role: response.data?.user?.role,
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

    const signup = async (name, email, password, role = 'teacher') => {
        try {
            const res = await apiSignup(name, email, password, role);
            // Immediately login after signup
            const loginRes = await apiLogin(email, password);
            const userData = {
                token: loginRes.data?.token,
                id: loginRes.data?.user?.id,
                name: loginRes.data?.user?.name,
                email: loginRes.data?.user?.email,
                role: loginRes.data?.user?.role,
            };
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));
            return { success: true };
        } catch (error) {
            let msg = 'Signup failed';
            if (error.response?.data?.detail) msg = error.response.data.detail;
            else if (error.message) msg = error.message;
            return { success: false, error: msg };
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
        <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
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
