import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Header() {
    const { user, logout } = useAuth();

    const handleLogout = async () => {
        await logout();
    };

    return (
        <header className="bg-white border-b border-border px-6 py-3">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <h1 className="text-lg font-semibold text-text-primary">
                        Attendance Management System
                    </h1>
                </div>

                <div className="flex items-center gap-6">
                    <span className="text-sm text-text-secondary">
                        {user?.username || 'Teacher'}
                    </span>
                    <button
                        onClick={handleLogout}
                        className="text-sm text-text-secondary hover:text-text-primary"
                    >
                        Sign out
                    </button>
                </div>
            </div>
        </header>
    );
}
