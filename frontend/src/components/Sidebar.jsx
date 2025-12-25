import { NavLink } from 'react-router-dom';

const navItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/mark-attendance', label: 'Mark Attendance' },
    { path: '/view-attendance', label: 'View Attendance' },
    { path: '/timetable', label: 'Timetable' },
    { path: '/directory', label: 'Teacher Directory' },
    { path: '/profile', label: 'Profile' },
];

export default function Sidebar() {
    return (
        <aside className="w-56 bg-white border-r border-border min-h-screen">
            <nav className="py-4">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `nav-item ${isActive ? 'active' : ''}`
                        }
                    >
                        {item.label}
                    </NavLink>
                ))}
            </nav>
        </aside>
    );
}
