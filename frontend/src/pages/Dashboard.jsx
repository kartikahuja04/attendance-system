import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getSchedule, getPreviousDayStats, getAnnouncements, getStats } from '../services/api';
import Layout from '../components/Layout';

export default function Dashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [schedule, setSchedule] = useState([]);
    const [prevDayStats, setPrevDayStats] = useState([]);
    const [announcements, setAnnouncements] = useState([]);
    const [dashboardStats, setDashboardStats] = useState({
        total_sessions: 0,
        active_sessions: 0,
        avg_attendance: 0,
        todays_classes: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }

        const fetchData = async () => {
            try {
                const [scheduleRes, prevStatsRes, announcementsRes, statsRes] = await Promise.all([
                    getSchedule(),
                    getPreviousDayStats(),
                    getAnnouncements().catch(() => ({ data: { announcements: [] } })),
                    getStats().catch(() => ({ data: {} })),
                ]);
                setSchedule(scheduleRes.data.schedule || []);
                setPrevDayStats(prevStatsRes.data.stats || []);
                setAnnouncements(announcementsRes.data.announcements || []);
                setDashboardStats(statsRes.data || {
                    total_sessions: 0,
                    active_sessions: 0,
                    avg_attendance: 0,
                    todays_classes: 0
                });
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
                                            {item.time && (
                                                <span className="text-text-secondary ml-2">({item.time})</span>
                                            )}
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

                {/* Stats Grid - Dynamic from API */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="stat-card">
                        <div className="stat-value">{dashboardStats.total_sessions || 0}</div>
                        <div className="stat-label">Total Sessions</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{dashboardStats.active_sessions || 0}</div>
                        <div className="stat-label">Active Sessions</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{dashboardStats.avg_attendance || 0}%</div>
                        <div className="stat-label">Avg Attendance</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{schedule.length}</div>
                        <div className="stat-label">Today's Classes</div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Announcements - Dynamic from API */}
                    <div className="card">
                        <h3 className="section-header">Announcements</h3>
                        <div className="space-y-3">
                            {announcements.length > 0 ? (
                                announcements.map((item) => (
                                    <AnnouncementItem
                                        key={item.id}
                                        date={item.date}
                                        text={item.content}
                                        priority={item.priority}
                                    />
                                ))
                            ) : (
                                <p className="text-text-secondary text-sm">No announcements</p>
                            )}
                        </div>
                    </div>

                    {/* Previous Day Summary */}
                    <div className="card">
                        <h3 className="section-header">Previous Day Summary</h3>
                        {prevDayStats.length > 0 ? (
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
                                    {prevDayStats.map((stat, idx) => (
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
                            <p className="text-text-secondary text-sm">No sessions from previous day</p>
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

