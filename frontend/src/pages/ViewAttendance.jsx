import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';

export default function ViewAttendance() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filters, setFilters] = useState({
        subject: '',
        date: '',
        class: ''
    });

    useEffect(() => {
        if (!user) {
            navigate('/login');
        }
    }, [user, navigate]);

    const handleSearch = async () => {
        setLoading(true);
        // Simulate API call - replace with actual API
        setTimeout(() => {
            setRecords([
                { id: 1, student: 'John Doe', rollNo: '101', subject: 'Mathematics', date: '2025-12-12', status: 'Present' },
                { id: 2, student: 'Jane Smith', rollNo: '102', subject: 'Mathematics', date: '2025-12-12', status: 'Present' },
                { id: 3, student: 'Bob Wilson', rollNo: '103', subject: 'Mathematics', date: '2025-12-12', status: 'Absent' },
            ]);
            setLoading(false);
        }, 500);
    };

    return (
        <Layout>
            <div className="max-w-6xl">
                <div className="mb-6">
                    <h2 className="text-xl font-semibold text-text-primary">View Attendance</h2>
                    <p className="text-sm text-text-secondary">Search and view attendance records</p>
                </div>

                {/* Filters */}
                <div className="card mb-6">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                            <label className="label">Subject</label>
                            <select
                                className="input"
                                value={filters.subject}
                                onChange={(e) => setFilters({ ...filters, subject: e.target.value })}
                            >
                                <option value="">All Subjects</option>
                                <option value="math">Mathematics</option>
                                <option value="physics">Physics</option>
                                <option value="chemistry">Chemistry</option>
                            </select>
                        </div>
                        <div>
                            <label className="label">Class</label>
                            <select
                                className="input"
                                value={filters.class}
                                onChange={(e) => setFilters({ ...filters, class: e.target.value })}
                            >
                                <option value="">All Classes</option>
                                <option value="11">Class 11</option>
                                <option value="12">Class 12</option>
                            </select>
                        </div>
                        <div>
                            <label className="label">Date</label>
                            <input
                                type="date"
                                className="input"
                                value={filters.date}
                                onChange={(e) => setFilters({ ...filters, date: e.target.value })}
                            />
                        </div>
                        <div className="flex items-end">
                            <button onClick={handleSearch} className="btn-primary w-full">
                                Search
                            </button>
                        </div>
                    </div>
                </div>

                {/* Results */}
                <div className="card">
                    <h3 className="section-header">Attendance Records</h3>
                    {loading ? (
                        <p className="text-text-secondary">Loading...</p>
                    ) : records.length > 0 ? (
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Roll No</th>
                                    <th>Student Name</th>
                                    <th>Subject</th>
                                    <th>Date</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {records.map((record) => (
                                    <tr key={record.id}>
                                        <td>{record.rollNo}</td>
                                        <td className="font-medium">{record.student}</td>
                                        <td>{record.subject}</td>
                                        <td>{record.date}</td>
                                        <td>
                                            <span className={`badge ${record.status === 'Present' ? 'badge-success' : 'badge-error'}`}>
                                                {record.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <p className="text-text-secondary text-sm">
                            Use the filters above to search for attendance records.
                        </p>
                    )}
                </div>
            </div>
        </Layout>
    );
}
