import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';
import axios from 'axios';

export default function SessionPage() {
    const { id } = useParams();
    const { user } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [qrCode, setQrCode] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }

        setLoading(true);
        setError(null);
        setQrCode(null);

        const fetchQR = async () => {
            try {
                const response = await axios.get(`/api/qr/${id}`, { withCredentials: true });
                if (response.data && response.data.qr_code) {
                    setQrCode(response.data.qr_code);
                } else {
                    setError('Invalid QR code response');
                }
            } catch (err) {
                console.error('Failed to fetch QR code:', err);
                setError('Failed to load QR code');
            } finally {
                setLoading(false);
            }
        };

        fetchQR();
    }, [id, user, navigate]);

    return (
        <Layout>
            <div className="max-w-2xl">
                <div className="mb-6">
                    <h2 className="text-xl font-semibold text-text-primary">Session QR Code</h2>
                    <p className="text-sm text-text-secondary">Display for students to mark attendance</p>
                </div>

                <div className="card text-center">
                    {loading ? (
                        <p className="text-text-secondary py-8">Loading QR code...</p>
                    ) : error ? (
                        <div className="py-8">
                            <p className="text-error mb-4">{error}</p>
                            <button onClick={() => window.location.reload()} className="btn-secondary">
                                Retry
                            </button>
                        </div>
                    ) : qrCode ? (
                        <div>
                            <div className="inline-block p-4 bg-white border border-border rounded-lg mb-6">
                                <img src={qrCode} alt="Session QR Code" className="w-64 h-64" />
                            </div>
                            <div className="text-sm text-text-secondary space-y-2">
                                <p>Students can scan this QR code using the attendance app.</p>
                                <p>Session ID: {id}</p>
                            </div>
                        </div>
                    ) : (
                        <p className="text-text-secondary py-8">No QR code available</p>
                    )}

                    <div className="mt-6 pt-4 border-t border-border">
                        <button onClick={() => navigate('/mark-attendance')} className="btn-secondary">
                            Back to Sessions
                        </button>
                    </div>
                </div>
            </div>
        </Layout>
    );
}
