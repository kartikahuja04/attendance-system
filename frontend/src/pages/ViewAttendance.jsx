import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getSessions, getAttendanceData, exportAttendance } from '../services/api';
import Layout from '../components/Layout';

export default function ViewAttendance() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);
    const [detailedAttendance, setDetailedAttendance] = useState(null);
    const [loading, setLoading] = useState(false);
    const [detailsLoading, setDetailsLoading] = useState(false);
    const [filterDate, setFilterDate] = useState(new Date().toLocaleDateString('en-CA'));

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }
        fetchSessions(filterDate);
    }, [user, navigate, filterDate]);

    const fetchSessions = async (date) => {
        setLoading(true);
        try {
            const response = await getSessions(date);
            setSessions(response.data.sessions || []);
            setSelectedSession(null);
            setDetailedAttendance(null);
        } catch (error) {
            console.error('Error fetching sessions:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSessionClick = async (session) => {
        setDetailsLoading(true);
        try {
            const response = await getAttendanceData(session.id);
            setSelectedSession(response.data);
            // Don't auto-show details on single click
            setDetailedAttendance(null);
        } catch (error) {
            console.error('Error fetching attendance summary:', error);
        } finally {
            setDetailsLoading(false);
        }
    };

    const handleSessionDoubleClick = async (session) => {
        setDetailsLoading(true);
        try {
            const response = await getAttendanceData(session.id);
            setSelectedSession(response.data);
            setDetailedAttendance(response.data.attendance);
        } catch (error) {
            console.error('Error fetching detailed attendance:', error);
        } finally {
            setDetailsLoading(false);
        }
    };

    const handleExport = async (sessionId) => {
        try {
            const response = await exportAttendance(sessionId);
            // Verify response is a blob before creating URL
            const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `attendance_${sessionId}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Export failed:', error);
            alert('Export failed. Please try again.');
        }
    };

    return (
        <Layout>
            <div className="max-w-6xl">
                <div className="mb-6 flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-semibold text-text-primary">Attendance Explorer</h2>
                        <p className="text-sm text-text-secondary">View and export attendance records by date</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column: Sessions List */}
                    <div className="lg:col-span-1">
                        <div className="card h-full">
                            <label className="label mb-2">Select Date</label>
                            <input
                                type="date"
                                className="input mb-4"
                                value={filterDate}
                                onChange={(e) => setFilterDate(e.target.value)}
                            />

                            <h3 className="section-header">Sessions</h3>
                            {loading ? (
                                <p className="text-sm text-text-secondary">Loading sessions...</p>
                            ) : sessions.length > 0 ? (
                                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                                    {sessions.map((s) => (
                                        <div
                                            key={s.id}
                                            onClick={() => handleSessionClick(s)}
                                            onDoubleClick={() => handleSessionDoubleClick(s)}
                                            className={`p-3 border rounded-lg cursor-pointer transition-all duration-200 ${selectedSession?.session?.session_id === s.id
                                                    ? 'border-primary bg-primary/5 shadow-sm'
                                                    : 'border-border hover:bg-gray-50'
                                                }`}
                                        >
                                            <div className="flex justify-between items-start">
                                                <h4 className="font-semibold text-text-primary">{s.subject}</h4>
                                                <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold uppercase ${s.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                                                    }`}>
                                                    {s.status}
                                                </span>
                                            </div>
                                            <p className="text-xs text-text-secondary mt-1">
                                                {s.class_name} - {s.section}
                                            </p>
                                            <p className="text-[10px] text-text-secondary mt-1">
                                                {s.start_time.split(' ')[1]}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-sm text-text-secondary py-8 text-center border border-dashed rounded-lg">
                                    No sessions found for this date.
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Right Column: Details & Stats */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Summary Stats */}
                        <div className="card">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="section-header mb-0">Session Summary</h3>
                                {selectedSession && (
                                    <button
                                        onClick={() => handleExport(selectedSession.session.session_id)}
                                        className="btn-secondary text-sm py-1 px-3 flex items-center gap-2"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        Export Excel
                                    </button>
                                )}
                            </div>

                            {detailsLoading ? (
                                <p className="text-text-secondary py-8 text-center">Loading details...</p>
                            ) : selectedSession ? (
                                <div className="animate-in fade-in duration-300">
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                        <div className="bg-gray-50 p-3 rounded-lg border border-border">
                                            <p className="text-[10px] text-text-secondary uppercase">Status</p>
                                            <p className="font-bold text-lg capitalize">{selectedSession.session.status}</p>
                                        </div>
                                        <div className="bg-green-50 p-3 rounded-lg border border-green-100">
                                            <p className="text-[10px] text-green-600 uppercase">Present</p>
                                            <p className="font-bold text-lg text-green-700">{selectedSession.total_present}</p>
                                        </div>
                                        <div className="bg-red-50 p-3 rounded-lg border border-red-100">
                                            <p className="text-[10px] text-red-600 uppercase">Absent</p>
                                            <p className="font-bold text-lg text-red-700">{selectedSession.total_absent}</p>
                                        </div>
                                        <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
                                            <p className="text-[10px] text-blue-600 uppercase">Total</p>
                                            <p className="font-bold text-lg text-blue-700">
                                                {selectedSession.total_present + selectedSession.total_absent}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="text-sm text-text-secondary space-y-1">
                                        <p><span className="w-24 inline-block font-medium">Class:</span> {selectedSession.session.class_name} ({selectedSession.session.section})</p>
                                        <p><span className="w-24 inline-block font-medium">Subject:</span> {selectedSession.session.subject}</p>
                                        <p><span className="w-24 inline-block font-medium">Session ID:</span> <span className="text-[10px] font-mono">{selectedSession.session.session_id}</span></p>
                                    </div>

                                    {!detailedAttendance && (
                                        <div className="mt-4 p-4 bg-gray-50 border border-dashed border-gray-300 rounded-lg text-center">
                                            <p className="text-xs text-text-secondary italic">Double-click the session in the list to reveal student details</p>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center py-16 text-text-secondary">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                                    </svg>
                                    <p>Select a session record to analyze attendance.</p>
                                    <p className="text-xs mt-2 font-medium">Single-click for stats • Double-click for full list</p>
                                </div>
                            )}
                        </div>

                        {/* Detailed Attendance List */}
                        {detailedAttendance && (
                            <div className="card transform transition-all duration-300">
                                <h3 className="section-header flex justify-between items-center">
                                    <span>Detailed Roster</span>
                                    <span className="text-xs font-normal text-text-secondary uppercase tracking-widest">
                                        {detailedAttendance.length} Records
                                    </span>
                                </h3>
                                <div className="max-h-96 overflow-y-auto">
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <th>Student ID</th>
                                                <th>Check-in Time</th>
                                                <th>Method</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {detailedAttendance.map((a) => (
                                                <tr key={a.student_id}>
                                                    <td className="font-medium">{a.student_id}</td>
                                                    <td>{a.timestamp.split(' ')[1]}</td>
                                                    <td>
                                                        <span className={`badge ${a.marked_by === 'qr' ? 'badge-success' : 'badge-warning'}`}>
                                                            {a.marked_by.toUpperCase()}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                            {detailedAttendance.length === 0 && (
                                                <tr>
                                                    <td colSpan="3" className="text-center py-8 text-text-secondary border-dashed border">
                                                        No students marked attendance yet.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
}
