import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getActiveSessions, createSession, getTeacherSchedule } from '../services/api';
import Layout from '../components/Layout';

export default function MarkAttendance() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState('');
    const [schedule, setSchedule] = useState([]);
    const [suggestion, setSuggestion] = useState(null);
    const [formData, setFormData] = useState({
        class_name: '',
        subject: '',
        section: '',
        start_time: new Date().toISOString().slice(0, 16)
    });

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }
        fetchSessions();
        fetchSchedule();
    }, [user, navigate]);

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

    const fetchSchedule = async () => {
        try {
            const response = await getTeacherSchedule();
            const todaySchedule = response.data.schedule || [];
            setSchedule(todaySchedule);
            detectCurrentSession(todaySchedule);
        } catch (error) {
            console.error('Error fetching schedule:', error);
        }
    };

    const detectCurrentSession = (todaySchedule) => {
        const now = new Date();
        const currentTimeStr = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });

        // Find session where currentTime is between start and end
        const current = todaySchedule.find(s => {
            const [start, end] = s.time.split('-');
            return currentTimeStr >= start && currentTimeStr <= end;
        });

        if (current) {
            setSuggestion(current);
        }
    };

    const useSuggestedSession = () => {
        if (!suggestion) return;
        setFormData({
            ...formData,
            class_name: suggestion.class_name,
            subject: suggestion.subject,
            section: suggestion.section
        });
        setShowCreateForm(true);
        setSuggestion(null); // Clear suggestion after use
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleCreateSession = async (e) => {
        e.preventDefault();
        setCreating(true);
        setError('');

        try {
            const response = await createSession(formData);
            if (response.data.success) {
                navigate(`/session/${response.data.session_id}`);
            } else {
                setError(response.data.message || 'Failed to create session');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Error creating session');
        } finally {
            setCreating(false);
        }
    };

    return (
        <Layout>
            <div className="max-w-4xl">
                <div className="mb-6 flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-semibold text-text-primary">Mark Attendance</h2>
                        <p className="text-sm text-text-secondary">
                            {showCreateForm ? 'Create a new attendance session' : 'Select a session or create new'}
                        </p>
                    </div>
                    <button
                        onClick={() => setShowCreateForm(!showCreateForm)}
                        className={showCreateForm ? "btn-secondary" : "btn-primary"}
                    >
                        {showCreateForm ? 'Cancel' : '+ New Session'}
                    </button>
                </div>

                {/* Smart Suggestion */}
                {suggestion && !showCreateForm && (
                    <div className="card mb-6 border-l-4 border-primary bg-primary/5 animate-in slide-in-from-top duration-500">
                        <div className="flex justify-between items-center">
                            <div className="flex gap-4 items-center">
                                <div className="bg-primary/10 p-2 rounded-full text-primary">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-text-primary">Ongoing Class Scheduled?</h3>
                                    <p className="text-sm text-text-secondary">
                                        Detected class: <span className="font-medium">{suggestion.subject}</span> ({suggestion.class_name}) at {suggestion.time}
                                    </p>
                                </div>
                            </div>
                            <button onClick={useSuggestedSession} className="btn-primary text-sm py-2">
                                Use This Session
                            </button>
                        </div>
                    </div>
                )}

                {/* Create Session Form */}
                {showCreateForm && (
                    <div className="card mb-6 animate-in fade-in duration-300">
                        <h3 className="section-header">Create New Session</h3>
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                                {error}
                            </div>
                        )}
                        <form onSubmit={handleCreateSession}>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="block text-sm font-medium text-text-primary mb-1">
                                        Class Name *
                                    </label>
                                    <input
                                        type="text"
                                        name="class_name"
                                        value={formData.class_name}
                                        onChange={handleInputChange}
                                        placeholder="e.g., CSE-3A"
                                        className="input"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-primary mb-1">
                                        Subject *
                                    </label>
                                    <input
                                        type="text"
                                        name="subject"
                                        value={formData.subject}
                                        onChange={handleInputChange}
                                        placeholder="e.g., Data Structures"
                                        className="input"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-primary mb-1">
                                        Section *
                                    </label>
                                    <input
                                        type="text"
                                        name="section"
                                        value={formData.section}
                                        onChange={handleInputChange}
                                        placeholder="e.g., A"
                                        className="input"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-primary mb-1">
                                        Start Time *
                                    </label>
                                    <input
                                        type="datetime-local"
                                        name="start_time"
                                        value={formData.start_time}
                                        onChange={handleInputChange}
                                        className="input"
                                        required
                                    />
                                </div>
                            </div>
                            <button
                                type="submit"
                                disabled={creating}
                                className="btn-primary"
                            >
                                {creating ? 'Creating...' : 'Start Session'}
                            </button>
                        </form>
                    </div>
                )}

                {/* Active Sessions List */}
                <div className="card">
                    <h3 className="section-header">Active Sessions</h3>
                    {loading ? (
                        <p className="text-text-secondary">Loading sessions...</p>
                    ) : sessions.length > 0 ? (
                        <div className="overflow-x-auto">
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
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <p className="text-text-secondary mb-4">No active sessions</p>
                            <p className="text-sm text-text-secondary">
                                Click "New Session" above to create one.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </Layout>
    );
}


