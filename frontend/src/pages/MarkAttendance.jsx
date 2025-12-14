import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getActiveSessions } from '../services/api';
import Layout from '../components/Layout';

export default function MarkAttendance() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }

        const fetchSessions = async () => {
            try {
                const response = await getActiveSessions();
                setSessions(response.data.sessions || []);
            } catch (error) {
                console.error('Error fetching sessions:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchSessions();
    }, [user, navigate]);

    return (
        <Layout>
            <div className="max-w-4xl">
                <div className="mb-6">
                    <h2 className="text-xl font-semibold text-text-primary">Mark Attendance</h2>
                    <p className="text-sm text-text-secondary">Select a session to display QR code</p>
                </div>

                <div className="card">
                    {loading ? (
                        <p className="text-text-secondary">Loading sessions...</p>
                    ) : sessions.length > 0 ? (
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Subject</th>
                                    <th>Class</th>
                                    <th>Date</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sessions.map((session) => (
                                    <tr key={session.id}>
                                        <td className="font-medium">{session.subject}</td>
                                        <td>{session.class_name} - {session.section}</td>
                                        <td>{session.date}</td>
                                        <td>
                                            <span className="badge badge-success">Active</span>
                                        </td>
                                        <td>
                                            <button
                                                onClick={() => navigate(`/session/${session.id}`)}
                                                className="btn-primary text-sm py-1 px-3"
                                            >
                                                View QR
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <div className="text-center py-8">
                            <p className="text-text-secondary mb-4">No active sessions</p>
                            <p className="text-sm text-text-secondary">
                                Start a new session from the main system to generate QR codes.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </Layout>
    );
}
