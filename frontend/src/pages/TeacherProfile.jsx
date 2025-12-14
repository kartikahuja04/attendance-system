import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getProfile, updateProfile } from '../services/api';
import Layout from '../components/Layout';

export default function TeacherProfile() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [formData, setFormData] = useState({});
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }

        const fetchProfile = async () => {
            try {
                const response = await getProfile();
                setProfile(response.data);
                setFormData(response.data);
            } catch (error) {
                console.error('Error fetching profile:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, [user, navigate]);

    const handleSave = async () => {
        setSaving(true);
        try {
            await updateProfile(formData);
            setProfile(formData);
            setEditing(false);
        } catch (error) {
            console.error('Error saving profile:', error);
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (field, value) => {
        setFormData({ ...formData, [field]: value });
    };

    if (loading) {
        return (
            <Layout>
                <p className="text-text-secondary">Loading profile...</p>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="max-w-2xl">
                <div className="mb-6 flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-semibold text-text-primary">Profile</h2>
                        <p className="text-sm text-text-secondary">Manage your account information</p>
                    </div>
                    {!editing && (
                        <button onClick={() => setEditing(true)} className="btn-secondary">
                            Edit
                        </button>
                    )}
                </div>

                <div className="card">
                    {editing ? (
                        <form onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
                            <div className="space-y-4">
                                <div>
                                    <label className="label">Full Name</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={formData.full_name || ''}
                                        onChange={(e) => handleChange('full_name', e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="label">Employee ID</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={formData.employee_id || ''}
                                        onChange={(e) => handleChange('employee_id', e.target.value)}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="label">Department</label>
                                        <input
                                            type="text"
                                            className="input"
                                            value={formData.department || ''}
                                            onChange={(e) => handleChange('department', e.target.value)}
                                        />
                                    </div>
                                    <div>
                                        <label className="label">Designation</label>
                                        <input
                                            type="text"
                                            className="input"
                                            value={formData.designation || ''}
                                            onChange={(e) => handleChange('designation', e.target.value)}
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="label">Email</label>
                                    <input
                                        type="email"
                                        className="input"
                                        value={formData.email || ''}
                                        onChange={(e) => handleChange('email', e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="label">Phone</label>
                                    <input
                                        type="tel"
                                        className="input"
                                        value={formData.phone || ''}
                                        onChange={(e) => handleChange('phone', e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="label">Qualification</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={formData.qualification || ''}
                                        onChange={(e) => handleChange('qualification', e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="mt-6 pt-4 border-t border-border flex gap-3">
                                <button type="submit" className="btn-primary" disabled={saving}>
                                    {saving ? 'Saving...' : 'Save Changes'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => { setEditing(false); setFormData(profile); }}
                                    className="btn-secondary"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    ) : (
                        <div className="space-y-4">
                            <ProfileField label="Full Name" value={profile?.full_name} />
                            <ProfileField label="Employee ID" value={profile?.employee_id} />
                            <ProfileField label="Department" value={profile?.department} />
                            <ProfileField label="Designation" value={profile?.designation} />
                            <ProfileField label="Email" value={profile?.email} />
                            <ProfileField label="Phone" value={profile?.phone} />
                            <ProfileField label="Qualification" value={profile?.qualification} />
                        </div>
                    )}
                </div>
            </div>
        </Layout>
    );
}

function ProfileField({ label, value }) {
    return (
        <div className="py-2 border-b border-border last:border-0">
            <div className="text-xs text-text-secondary uppercase tracking-wider">{label}</div>
            <div className="text-sm text-text-primary mt-1">{value || '-'}</div>
        </div>
    );
}
