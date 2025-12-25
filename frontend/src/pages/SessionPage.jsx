import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getQRCode, getSessionAttendance, endSession } from '../services/api';
import Layout from '../components/Layout';

export default function SessionPage() {
    const { id } = useParams();
    const { user } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [qrCode, setQrCode] = useState(null);
    const [attendance, setAttendance] = useState([]);
    const [error, setError] = useState(null);
    const [ending, setEnding] = useState(false);

    const fetchQR = useCallback(async () => {
        try {
            const response = await getQRCode(id);
            if (response.data && response.data.qr_code) {
                setQrCode(response.data.qr_code);
                setError(null);
            }
        } catch (err) {
            console.error('Failed to fetch QR code:', err);
            setError('Failed to load QR code');
        } finally {
            setLoading(false);
        }
    }, [id]);

    const fetchAttendance = useCallback(async () => {
        try {
            const response = await getSessionAttendance(id);
            setAttendance(response.data.records || []);
        } catch (err) {
            console.error('Failed to fetch attendance:', err);
        }
    }, [id]);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }

        // Initial fetch
        fetchQR();
        fetchAttendance();

        // Auto-refresh QR every 10 seconds
        const qrInterval = setInterval(fetchQR, 10000);
        // Auto-refresh attendance every 5 seconds
        const attendanceInterval = setInterval(fetchAttendance, 5000);

        return () => {
            clearInterval(qrInterval);
            clearInterval(attendanceInterval);
        };
    }, [id, user, navigate, fetchQR, fetchAttendance]);

    const handleEndSession = async () => {
        if (!confirm('Are you sure you want to end this session?')) return;

        setEnding(true);
        try {
            await endSession(id);
            navigate('/view-attendance');
        } catch (err) {
            console.error('Failed to end session:', err);
            alert('Failed to end session');
        } finally {
            setEnding(false);
        }
    };

    return (
        <Layout>
            <div className="max-w-4xl">
                <div className="mb-6 flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-semibold text-text-primary">Session QR Code</h2>
                        <p className="text-sm text-text-secondary">Session ID: {id}</p>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => navigate('/mark-attendance')} className="btn-secondary">
                            Back
                        </button>
                        <button
                            onClick={handleEndSession}
                            disabled={ending}
                            className="btn-primary bg-red-600 hover:bg-red-700"
                        >
                            {ending ? 'Ending...' : 'End Session'}
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* QR Code Card */}
                    <div className="card text-center">
                        <h3 className="section-header">Scan to Mark Attendance</h3>
                        {loading ? (
                            <p className="text-text-secondary py-8">Loading QR code...</p>
                        ) : error ? (
                            <div className="py-8">
                                <p className="text-error mb-4">{error}</p>
                                <button onClick={fetchQR} className="btn-secondary">
                                    Retry
                                </button>
                            </div>
                        ) : qrCode ? (
                            <div>
                                <div className="inline-block p-4 bg-white border border-border rounded-lg">
                                    <img src={qrCode} alt="Session QR Code" className="w-64 h-64" />
                                </div>
                                <p className="text-xs text-text-secondary mt-4">
                                    QR refreshes every 10 seconds for security
                                </p>
                            </div>
                        ) : (
                            <p className="text-text-secondary py-8">No QR code available</p>
                        )}
                    </div>

                    {/* Attendance List Card */}
                    <div className="card">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="section-header mb-0">Live Attendance</h3>
                            <span className="badge badge-success">{attendance.length} Present</span>
                        </div>

                        {attendance.length > 0 ? (
                            <div className="max-h-80 overflow-y-auto">
                                <table className="table text-sm">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Student ID</th>
                                            <th>Time</th>
                                            <th>Method</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {attendance.map((record, idx) => (
                                            <tr key={record.student_id}>
                                                <td>{idx + 1}</td>
                                                <td className="font-medium">{record.student_id}</td>
                                                <td>{record.timestamp?.split(' ')[1] || record.timestamp}</td>
                                                <td>
                                                    <span className={`badge ${record.marked_by === 'qr' ? 'badge-success' : 'badge-warning'}`}>
                                                        {record.marked_by?.toUpperCase()}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p className="text-text-secondary text-center py-8">
                                No students have marked attendance yet
                            </p>
                        )}
                        <p className="text-xs text-text-secondary mt-4 text-center">
                            Updates every 5 seconds
                        </p>
                    </div>
                </div>
            </div>
        </Layout>
    );
}

