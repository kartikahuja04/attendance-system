import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getSchedule, getPreviousDayStats } from '../services/api';
import Layout from '../components/Layout';

export default function Dashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [schedule, setSchedule] = useState([]);
    const [stats, setStats] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }

        const fetchData = async () => {
            try {
                const [scheduleRes, statsRes] = await Promise.all([
                    getSchedule(),
                    getPreviousDayStats(),
                ]);
                setSchedule(scheduleRes.data.schedule || []);
                setStats(statsRes.data.stats || []);
            } catch (error) {
                console.error('Error fetching data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [user, navigate]);

    const currentDate = new Date().toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    return (
        <Layout>
            <div className="max-w-6xl">
                {/* Page Header */}
                <div className="mb-6">
                    <h2 className="text-xl font-semibold text-text-primary">Dashboard</h2>
                    <p className="text-sm text-text-secondary">{currentDate}</p>
                </div>

                {/* Primary Action - Today's Class */}
                <div className="card mb-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="section-header">Today's Classes</h3>
                            {loading ? (
                                <p className="text-text-secondary">Loading schedule...</p>
                            ) : schedule.length > 0 ? (
                                <div className="space-y-2">
                                    {schedule.map((item, idx) => (
                                        <div key={idx} className="text-sm">
                                            <span className="font-medium">{item.subject}</span>
                                            <span className="text-text-secondary ml-2">
                                                {item.class_name} - {item.section}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-text-secondary">No classes scheduled for today</p>
                            )}
                        </div>
                        <button
                            onClick={() => navigate('/mark-attendance')}
                            className="btn-primary"
                        >
                            Start Attendance
                        </button>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="stat-card">
                        <div className="stat-value">12</div>
                        <div className="stat-label">Total Sessions</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">3</div>
                        <div className="stat-label">Active Sessions</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">92%</div>
                        <div className="stat-label">Avg Attendance</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{schedule.length}</div>
                        <div className="stat-label">Today's Classes</div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Announcements */}
                    <div className="card">
                        <h3 className="section-header">Announcements</h3>
                        <div className="space-y-3">
                            <AnnouncementItem
                                date="Dec 12, 2025"
                                text="Mid-term examinations will be conducted from December 20-25, 2025."
                                priority="high"
                            />
                            <AnnouncementItem
                                date="Dec 10, 2025"
                                text="Faculty meeting scheduled for December 15, 2025 at 3:00 PM in Conference Hall."
                            />
                            <AnnouncementItem
                                date="Dec 8, 2025"
                                text="Student project submissions deadline: December 18, 2025."
                            />
                        </div>
                    </div>

                    {/* Previous Day Summary */}
                    <div className="card">
                        <h3 className="section-header">Previous Day Summary</h3>
                        {stats.length > 0 ? (
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Subject</th>
                                        <th>Total</th>
                                        <th>Present</th>
                                        <th>Absent</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {stats.map((stat, idx) => (
                                        <tr key={idx}>
                                            <td className="font-medium">{stat.subject}</td>
                                            <td>{stat.total_students}</td>
                                            <td className="text-success">{stat.present_students}</td>
                                            <td className="text-error">{stat.absent_students}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <p className="text-text-secondary text-sm">No data from previous day</p>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
}

function AnnouncementItem({ date, text, priority }) {
    return (
        <div className="py-2 border-b border-border last:border-0">
            <div className="flex items-start gap-2">
                {priority === 'high' && (
                    <span className="badge badge-warning">Important</span>
                )}
                <div className="flex-1">
                    <p className="text-sm text-text-primary">{text}</p>
                    <p className="text-xs text-text-secondary mt-1">{date}</p>
                </div>
            </div>
        </div>
    );
}
