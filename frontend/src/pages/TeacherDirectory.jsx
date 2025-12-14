import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getTeachersDirectory } from '../services/api';
import Layout from '../components/Layout';

export default function TeacherDirectory() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [teachers, setTeachers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }

        const fetchTeachers = async () => {
            try {
                const response = await getTeachersDirectory();
                setTeachers(response.data.teachers || []);
            } catch (error) {
                console.error('Error fetching teachers:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchTeachers();
    }, [user, navigate]);

    const filteredTeachers = teachers.filter(teacher =>
        teacher.name?.toLowerCase().includes(search.toLowerCase()) ||
        teacher.department?.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <Layout>
            <div className="max-w-4xl">
                <div className="mb-6">
                    <h2 className="text-xl font-semibold text-text-primary">Teacher Directory</h2>
                    <p className="text-sm text-text-secondary">Search and view teacher profiles</p>
                </div>

                {/* Search */}
                <div className="card mb-6">
                    <div className="flex gap-4">
                        <input
                            type="text"
                            placeholder="Search by name or department..."
                            className="input flex-1"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                {/* Results */}
                <div className="card">
                    {loading ? (
                        <p className="text-text-secondary">Loading...</p>
                    ) : filteredTeachers.length > 0 ? (
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Department</th>
                                    <th>Designation</th>
                                    <th>Email</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredTeachers.map((teacher) => (
                                    <tr key={teacher.id}>
                                        <td className="font-medium">{teacher.name || teacher.username}</td>
                                        <td>{teacher.department || '-'}</td>
                                        <td>{teacher.designation || '-'}</td>
                                        <td>{teacher.email || '-'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <p className="text-text-secondary text-sm">
                            No teachers found matching your search.
                        </p>
                    )}
                </div>
            </div>
        </Layout>
    );
}
