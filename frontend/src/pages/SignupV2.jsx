/**
 * Professional Sign Up Page
 * Modern, responsive design with validation and role selection
 */

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/apiV2";

const SignupV2 = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    fullName: "",
    password: "",
    confirmPassword: "",
    role: "student",
    organizationId: "org_123",
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [focusedField, setFocusedField] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  // Calculate password strength
  const calculatePasswordStrength = (password) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[!@#$%^&*]/.test(password)) strength++;
    return strength;
  };

  const validateEmail = (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!validateEmail(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!formData.fullName.trim()) {
      newErrors.fullName = "Full name is required";
    } else if (formData.fullName.trim().length < 3) {
      newErrors.fullName = "Full name must be at least 3 characters";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    } else if (passwordStrength < 3) {
      newErrors.password = "Password is too weak. Use uppercase, lowercase, numbers, and symbols";
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    if (name === "password") {
      setPasswordStrength(calculatePasswordStrength(value));
    }

    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: "",
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccess("");

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      
      // Call signup API
      const response = await api.apiCall("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: formData.email,
          full_name: formData.fullName,
          password: formData.password,
          role: formData.role,
          organization_id: formData.organizationId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess("Account created successfully! Redirecting to login...");
        
        setTimeout(() => {
          navigate("/login");
        }, 2000);
      } else {
        const errorData = await response.json();
        setErrors({ general: errorData.detail || "Registration failed" });
      }
    } catch (error) {
      setErrors({ general: "An error occurred. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  const roleDescriptions = {
    student: "Access attendance records and academic information",
    faculty: "Mark attendance and manage class sessions",
    org_admin: "Manage students, faculty, and organization settings",
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-0 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse animation-delay-2000"></div>
      </div>

      {/* Main Container */}
      <div className="relative z-10 w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        
        {/* Left Side - Information */}
        <div className="hidden md:block text-white mt-12">
          <div className="space-y-6">
            <div>
              <h1 className="text-5xl font-bold mb-4 leading-tight">
                Join Our <br />
                <span className="text-purple-400">Community</span>
              </h1>
              <p className="text-xl text-purple-200">
                Create an account to start managing attendance with our modern platform.
              </p>
            </div>

            <div className="space-y-4 mt-8">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 rounded-lg bg-purple-600 flex items-center justify-center flex-shrink-0">
                  <span className="text-xl">🎓</span>
                </div>
                <div>
                  <h3 className="font-semibold text-lg">For Students</h3>
                  <p className="text-purple-200">Track your attendance and maintain eligibility</p>
                </div>
              </div>
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 rounded-lg bg-purple-600 flex items-center justify-center flex-shrink-0">
                  <span className="text-xl">👨‍🏫</span>
                </div>
                <div>
                  <h3 className="font-semibold text-lg">For Faculty</h3>
                  <p className="text-purple-200">Manage student attendance efficiently</p>
                </div>
              </div>
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 rounded-lg bg-purple-600 flex items-center justify-center flex-shrink-0">
                  <span className="text-xl">⚙️</span>
                </div>
                <div>
                  <h3 className="font-semibold text-lg">For Administrators</h3>
                  <p className="text-purple-200">Full control and insights over the system</p>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 pt-8 border-t border-purple-400">
              <div>
                <p className="text-3xl font-bold text-purple-300">100+</p>
                <p className="text-purple-200">Institutions</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-purple-300">50K+</p>
                <p className="text-purple-200">Active Users</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Signup Form */}
        <div className="relative">
          <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-10">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-block p-3 bg-purple-100 rounded-full mb-4">
                <span className="text-4xl">✍️</span>
              </div>
              <h2 className="text-3xl font-bold text-gray-800 mb-2">Create Account</h2>
              <p className="text-gray-600">Sign up to get started</p>
            </div>

            {/* Success Alert */}
            {success && (
              <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-500 rounded">
                <div className="flex items-center">
                  <span className="text-green-600 mr-3">✓</span>
                  <p className="text-green-700">{success}</p>
                </div>
              </div>
            )}

            {/* General Error */}
            {errors.general && (
              <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded">
                <div className="flex items-center">
                  <span className="text-red-600 mr-3">⚠️</span>
                  <p className="text-red-700">{errors.general}</p>
                </div>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Full Name */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Full Name
                </label>
                <div className={`relative transition-all ${focusedField === "fullName" ? "ring-2 ring-purple-500 rounded-lg" : ""}`}>
                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    onFocus={() => setFocusedField("fullName")}
                    onBlur={() => setFocusedField(null)}
                    placeholder="John Doe"
                    className={`w-full px-4 py-3 border-2 rounded-lg focus:outline-none transition ${
                      errors.fullName ? "border-red-500 focus:border-red-600" : "border-gray-300 focus:border-purple-600"
                    }`}
                    disabled={loading}
                  />
                  <span className="absolute right-3 top-3 text-2xl">👤</span>
                </div>
                {errors.fullName && <p className="text-red-600 text-sm mt-1">{errors.fullName}</p>}
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Email Address
                </label>
                <div className={`relative transition-all ${focusedField === "email" ? "ring-2 ring-purple-500 rounded-lg" : ""}`}>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    onFocus={() => setFocusedField("email")}
                    onBlur={() => setFocusedField(null)}
                    placeholder="you@university.edu"
                    className={`w-full px-4 py-3 border-2 rounded-lg focus:outline-none transition ${
                      errors.email ? "border-red-500 focus:border-red-600" : "border-gray-300 focus:border-purple-600"
                    }`}
                    disabled={loading}
                  />
                  <span className="absolute right-3 top-3 text-2xl">📧</span>
                </div>
                {errors.email && <p className="text-red-600 text-sm mt-1">{errors.email}</p>}
              </div>

              {/* Role Selection */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Account Type
                </label>
                <select
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-600 transition"
                  disabled={loading}
                >
                  <option value="student">👨‍🎓 Student</option>
                  <option value="faculty">👨‍🏫 Faculty</option>
                  <option value="org_admin">⚙️ Organization Admin</option>
                </select>
                <p className="text-gray-600 text-sm mt-2">
                  {roleDescriptions[formData.role]}
                </p>
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Password
                </label>
                <div className={`relative transition-all ${focusedField === "password" ? "ring-2 ring-purple-500 rounded-lg" : ""}`}>
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    onFocus={() => setFocusedField("password")}
                    onBlur={() => setFocusedField(null)}
                    placeholder="••••••••"
                    className={`w-full px-4 py-3 border-2 rounded-lg focus:outline-none transition ${
                      errors.password ? "border-red-500 focus:border-red-600" : "border-gray-300 focus:border-purple-600"
                    }`}
                    disabled={loading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-2xl"
                    disabled={loading}
                  >
                    {showPassword ? "👁️" : "👁️‍🗨️"}
                  </button>
                </div>

                {/* Password Strength Indicator */}
                {formData.password && (
                  <div className="mt-2">
                    <div className="flex space-x-1 mb-1">
                      {[...Array(5)].map((_, i) => (
                        <div
                          key={i}
                          className={`h-2 flex-1 rounded-full ${
                            i < passwordStrength
                              ? passwordStrength <= 2
                                ? "bg-red-500"
                                : passwordStrength <= 3
                                ? "bg-yellow-500"
                                : "bg-green-500"
                              : "bg-gray-200"
                          }`}
                        ></div>
                      ))}
                    </div>
                    <p className="text-xs text-gray-600">
                      {passwordStrength <= 2
                        ? "❌ Weak"
                        : passwordStrength <= 3
                        ? "⚠️ Fair"
                        : "✓ Strong"} password
                    </p>
                  </div>
                )}
                {errors.password && <p className="text-red-600 text-sm mt-1">{errors.password}</p>}
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Confirm Password
                </label>
                <div className={`relative transition-all ${focusedField === "confirmPassword" ? "ring-2 ring-purple-500 rounded-lg" : ""}`}>
                  <input
                    type="password"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    onFocus={() => setFocusedField("confirmPassword")}
                    onBlur={() => setFocusedField(null)}
                    placeholder="••••••••"
                    className={`w-full px-4 py-3 border-2 rounded-lg focus:outline-none transition ${
                      errors.confirmPassword ? "border-red-500 focus:border-red-600" : "border-gray-300 focus:border-purple-600"
                    }`}
                    disabled={loading}
                  />
                  <span className="absolute right-3 top-3 text-2xl">🔒</span>
                </div>
                {errors.confirmPassword && <p className="text-red-600 text-sm mt-1">{errors.confirmPassword}</p>}
              </div>

              {/* Terms & Conditions */}
              <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <input
                  type="checkbox"
                  id="terms"
                  className="w-5 h-5 text-purple-600 rounded mt-0.5"
                  disabled={loading}
                />
                <label htmlFor="terms" className="text-sm text-gray-700">
                  I agree to the <a href="#" className="text-purple-600 font-semibold hover:underline">Terms of Service</a> and{" "}
                  <a href="#" className="text-purple-600 font-semibold hover:underline">Privacy Policy</a>
                </label>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-400 disabled:to-gray-400 text-white font-bold py-3 rounded-lg transition transform hover:scale-105 active:scale-95 flex items-center justify-center space-x-2"
              >
                {loading ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    <span>Creating Account...</span>
                  </>
                ) : (
                  <>
                    <span>✍️</span>
                    <span>Create Account</span>
                  </>
                )}
              </button>
            </form>

            {/* Sign In Link */}
            <div className="text-center mt-6 text-gray-600">
              <p>
                Already have an account?{" "}
                <a href="/login" className="text-purple-600 hover:text-purple-700 font-semibold">
                  Sign In
                </a>
              </p>
            </div>
          </div>

          {/* Security Badge */}
          <div className="text-center mt-6 text-purple-200 text-xs space-y-1">
            <p>🔒 End-to-End Encrypted • Your data is always secure</p>
            <p>© 2025 University Attendance System. All rights reserved.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupV2;
