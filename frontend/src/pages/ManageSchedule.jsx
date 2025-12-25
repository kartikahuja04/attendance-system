import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getSchedules, createScheduleEntry, deleteScheduleEntry } from '../services/api';
import Layout from '../components/Layout';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function ManageSchedule() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [schedule, setSchedule] = useState([]);
    const [loading, setLoading] = useState(true);
    const [adding, setAdding] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        day_of_week: 'Monday',
        subject: '',
        subject_code: '',
        class_name: '',
        section: '',
        start_time: '09:00',
        end_time: '10:00',
        room: ''
    });

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }
        fetchSchedule();
    }, [user, navigate]);

    const fetchSchedule = async () => {
        try {
            const response = await getSchedules();
            setSchedule(response.data.schedules || []);
        } catch (error) {
            console.error('Error fetching schedule:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleAddEntry = async (e) => {
        e.preventDefault();
        setAdding(true);
        setError('');
        try {
            await createScheduleEntry(formData);
            setFormData({
                day_of_week: formData.day_of_week,
                subject: '',
                subject_code: '',
                class_name: '',
                section: '',
                start_time: '09:00',
                end_time: '10:00',
                room: ''
            });
            fetchSchedule();
        } catch (err) {
            setError('Failed to add schedule entry');
        } finally {
            setAdding(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this entry?')) return;
        try {
            await deleteScheduleEntry(id);
            fetchSchedule();
        } catch (error) {
            console.error('Delete failed:', error);
        }
    };

    const groupedSchedule = DAYS.reduce((acc, day) => {
        const slots = schedule.filter(s => s.day_of_week === day);
        if (slots.length > 0) acc[day] = slots;
        return acc;
    }, {});

    return (
        <Layout>
            <div className="max-w-6xl">
                <div className="mb-6">
                    <h2 className="text-xl font-semibold text-text-primary">Manage Timetable</h2>
                    <p className="text-sm text-text-secondary">Set your recurring weekly class schedule</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Add Entry Form */}
                    <div className="lg:col-span-1">
                        <div className="card sticky top-6">
                            <h3 className="section-header">Add Class Slot</h3>
                            {error && <div className="text-red-600 text-xs mb-4">{error}</div>}
                            <form onSubmit={handleAddEntry} className="space-y-4">
                                <div>
                                    <label className="label">Day of Week</label>
                                    <select
                                        name="day_of_week"
                                        className="input"
                                        value={formData.day_of_week}
                                        onChange={handleInputChange}
                                        required
                                    >
                                        {DAYS.map(day => <option key={day} value={day}>{day}</option>)}
                                    </select>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="label">Start Time</label>
                                        <input
                                            type="time"
                                            name="start_time"
                                            className="input"
                                            value={formData.start_time}
                                            onChange={handleInputChange}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="label">End Time</label>
                                        <input
                                            type="time"
                                            name="end_time"
                                            className="input"
                                            value={formData.end_time}
                                            onChange={handleInputChange}
                                            required
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="label">Subject</label>
                                    <input
                                        type="text"
                                        name="subject"
                                        className="input"
                                        placeholder="e.g., Computer Networks"
                                        value={formData.subject}
                                        onChange={handleInputChange}
                                        required
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="label">Class</label>
                                        <input
                                            type="text"
                                            name="class_name"
                                            className="input"
                                            placeholder="e.g., CSE-3"
                                            value={formData.class_name}
                                            onChange={handleInputChange}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="label">Section</label>
                                        <input
                                            type="text"
                                            name="section"
                                            className="input"
                                            placeholder="e.g., A"
                                            value={formData.section}
                                            onChange={handleInputChange}
                                            required
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="label">Room (Optional)</label>
                                    <input
                                        type="text"
                                        name="room"
                                        className="input"
                                        placeholder="e.g., Room 302"
                                        value={formData.room}
                                        onChange={handleInputChange}
                                    />
                                </div>
                                <button type="submit" disabled={adding} className="btn-primary w-full mt-2">
                                    {adding ? 'Adding...' : 'Add to Timetable'}
                                </button>
                            </form>
                        </div>
                    </div>

                    {/* Schedule List */}
                    <div className="lg:col-span-2 space-y-6">
                        {loading ? (
                            <p className="text-text-secondary">Loading timetable...</p>
                        ) : Object.keys(groupedSchedule).length > 0 ? (
                            DAYS.map(day => groupedSchedule[day] && (
                                <div key={day} className="card">
                                    <h3 className="section-header border-b pb-2 mb-4">{day}</h3>
                                    <div className="space-y-3">
                                        {groupedSchedule[day].map((slot) => (
                                            <div key={slot.id} className="flex justify-between items-center p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs font-bold text-primary uppercase">{slot.start_time} - {slot.end_time}</span>
                                                        <span className="text-sm font-semibold text-text-primary">{slot.subject}</span>
                                                    </div>
                                                    <p className="text-xs text-text-secondary mt-1">
                                                        {slot.class_name} ({slot.section}) {slot.room && `• ${slot.room}`}
                                                    </p>
                                                </div>
                                                <button
                                                    onClick={() => handleDelete(slot.id)}
                                                    className="text-red-500 hover:text-red-700 p-2"
                                                    title="Delete"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                    </svg>
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="card py-16 text-center">
                                <p className="text-text-secondary">Your timetable is empty.</p>
                                <p className="text-xs text-text-secondary mt-2">Add your class schedule using the form on the left.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
}
