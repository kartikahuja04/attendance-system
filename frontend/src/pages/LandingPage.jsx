/**
 * Professional Landing/Welcome Page
 * Beautiful welcome screen with features and CTA
 */

import React from "react";
import { useNavigate } from "react-router-dom";

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-0 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-pink-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20"></div>
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-4 md:px-12">
        <div className="flex items-center space-x-2">
          <span className="text-3xl">📋</span>
          <h1 className="text-2xl font-bold">AttendanceHub</h1>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate("/login")}
            className="px-6 py-2 rounded-lg border-2 border-purple-400 text-purple-300 hover:bg-purple-400 hover:text-white transition"
          >
            Sign In
          </button>
          <button
            onClick={() => navigate("/signup")}
            className="px-6 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 transition font-semibold"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="space-y-8">
            <h2 className="text-5xl md:text-6xl font-bold leading-tight">
              Attendance <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400">
                Made Simple
              </span>
            </h2>

            <p className="text-xl text-purple-200">
              Manage student attendance efficiently with our modern, intuitive platform. Designed for educators and institutions.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={() => navigate("/signup")}
                className="px-8 py-4 rounded-lg bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 font-bold text-lg transition transform hover:scale-105 active:scale-95"
              >
                🚀 Start Free Trial
              </button>
              <button
                onClick={() => navigate("/login")}
                className="px-8 py-4 rounded-lg border-2 border-purple-400 text-purple-300 hover:bg-purple-400 hover:text-white font-bold text-lg transition"
              >
                Sign In
              </button>
            </div>

            <div className="text-purple-200 text-sm">
              ✓ No credit card required • ✓ Free forever plan • ✓ 30 min setup
            </div>
          </div>

          {/* Right Illustration */}
          <div className="hidden md:block">
            <div className="relative w-full h-96 rounded-2xl bg-gradient-to-br from-purple-500 to-blue-500 p-1">
              <div className="w-full h-full rounded-xl bg-slate-900 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-6xl mb-4">📊</p>
                  <p className="text-purple-300">Dashboard Preview</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 py-20">
        <h3 className="text-4xl font-bold text-center mb-16">
          Powerful Features for Modern Education
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white bg-opacity-5 backdrop-blur-md rounded-xl p-8 border border-purple-400 border-opacity-30 hover:border-opacity-100 transition">
            <div className="text-5xl mb-4">⚡</div>
            <h4 className="text-xl font-bold mb-3">Quick & Easy</h4>
            <p className="text-purple-200">
              Mark attendance in seconds. Our intuitive interface makes it effortless for teachers and administrators.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white bg-opacity-5 backdrop-blur-md rounded-xl p-8 border border-purple-400 border-opacity-30 hover:border-opacity-100 transition">
            <div className="text-5xl mb-4">📈</div>
            <h4 className="text-xl font-bold mb-3">Detailed Analytics</h4>
            <p className="text-purple-200">
              Get insights with comprehensive reports and statistics. Track trends and improve attendance rates.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white bg-opacity-5 backdrop-blur-md rounded-xl p-8 border border-purple-400 border-opacity-30 hover:border-opacity-100 transition">
            <div className="text-5xl mb-4">🔒</div>
            <h4 className="text-xl font-bold mb-3">Secure & Private</h4>
            <p className="text-purple-200">
              End-to-end encrypted with role-based access control. Your data is always protected.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="bg-white bg-opacity-5 backdrop-blur-md rounded-xl p-8 border border-purple-400 border-opacity-30 hover:border-opacity-100 transition">
            <div className="text-5xl mb-4">📱</div>
            <h4 className="text-xl font-bold mb-3">Mobile Friendly</h4>
            <p className="text-purple-200">
              Works seamlessly on all devices. Mark attendance from your smartphone or desktop.
            </p>
          </div>

          {/* Feature 5 */}
          <div className="bg-white bg-opacity-5 backdrop-blur-md rounded-xl p-8 border border-purple-400 border-opacity-30 hover:border-opacity-100 transition">
            <div className="text-5xl mb-4">👥</div>
            <h4 className="text-xl font-bold mb-3">Multi-Role Support</h4>
            <p className="text-purple-200">
              Support for students, faculty, and administrators. Each with custom permissions and features.
            </p>
          </div>

          {/* Feature 6 */}
          <div className="bg-white bg-opacity-5 backdrop-blur-md rounded-xl p-8 border border-purple-400 border-opacity-30 hover:border-opacity-100 transition">
            <div className="text-5xl mb-4">🔄</div>
            <h4 className="text-xl font-bold mb-3">Real-time Sync</h4>
            <p className="text-purple-200">
              All data syncs in real-time across devices. Stay updated with instant notifications.
            </p>
          </div>
        </div>
      </div>

      {/* Pricing Section */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-12 py-20">
        <h3 className="text-4xl font-bold text-center mb-16">
          Simple, Transparent Pricing
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Free Plan */}
          <div className="rounded-xl p-8 border border-purple-400 border-opacity-30 bg-white bg-opacity-5 backdrop-blur-md">
            <h4 className="text-2xl font-bold mb-2">Free</h4>
            <p className="text-purple-200 mb-6">Perfect for getting started</p>
            <p className="text-4xl font-bold mb-6">$0<span className="text-lg text-purple-200">/month</span></p>
            <div className="space-y-3 mb-8">
              <p>✓ Up to 100 students</p>
              <p>✓ Basic reports</p>
              <p>✓ Email support</p>
              <p>✗ Advanced analytics</p>
            </div>
            <button
              onClick={() => navigate("/signup")}
              className="w-full px-6 py-3 rounded-lg border border-purple-400 text-purple-300 hover:bg-purple-400 hover:text-white transition font-semibold"
            >
              Get Started
            </button>
          </div>

          {/* Pro Plan - Highlighted */}
          <div className="rounded-xl p-8 bg-gradient-to-br from-purple-600 to-purple-700 border-2 border-purple-400 relative transform scale-105">
            <div className="absolute top-0 left-0 right-0 bg-gradient-to-r from-pink-500 to-purple-500 text-white text-sm font-bold py-1 text-center rounded-t-lg">
              MOST POPULAR
            </div>
            <h4 className="text-2xl font-bold mb-2 mt-2">Professional</h4>
            <p className="text-purple-100 mb-6">Best for institutions</p>
            <p className="text-4xl font-bold mb-6">$29<span className="text-lg text-purple-100">/month</span></p>
            <div className="space-y-3 mb-8">
              <p>✓ Up to 5,000 students</p>
              <p>✓ Advanced analytics</p>
              <p>✓ Priority support</p>
              <p>✓ Custom reports</p>
            </div>
            <button
              onClick={() => navigate("/signup")}
              className="w-full px-6 py-3 rounded-lg bg-white text-purple-600 hover:bg-gray-100 transition font-semibold"
            >
              Start Free Trial
            </button>
          </div>

          {/* Enterprise Plan */}
          <div className="rounded-xl p-8 border border-purple-400 border-opacity-30 bg-white bg-opacity-5 backdrop-blur-md">
            <h4 className="text-2xl font-bold mb-2">Enterprise</h4>
            <p className="text-purple-200 mb-6">For large organizations</p>
            <p className="text-4xl font-bold mb-6">Custom</p>
            <div className="space-y-3 mb-8">
              <p>✓ Unlimited students</p>
              <p>✓ Dedicated support</p>
              <p>✓ Custom integration</p>
              <p>✓ SLA guarantee</p>
            </div>
            <button
              onClick={() => navigate("/signup")}
              className="w-full px-6 py-3 rounded-lg bg-purple-600 hover:bg-purple-700 transition font-semibold"
            >
              Contact Sales
            </button>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative z-10 max-w-4xl mx-auto px-6 md:px-12 py-20 text-center">
        <h3 className="text-4xl font-bold mb-6">Ready to Get Started?</h3>
        <p className="text-xl text-purple-200 mb-8">
          Join thousands of educators using AttendanceHub to manage attendance efficiently.
        </p>
        <button
          onClick={() => navigate("/signup")}
          className="px-10 py-4 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 rounded-lg font-bold text-lg transition transform hover:scale-105 active:scale-95"
        >
          🚀 Start Free Trial Now
        </button>
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-purple-400 border-opacity-30 bg-white bg-opacity-5 backdrop-blur-md py-12">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="font-bold mb-4">Product</h4>
              <ul className="space-y-2 text-purple-200">
                <li><a href="#" className="hover:text-white transition">Features</a></li>
                <li><a href="#" className="hover:text-white transition">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition">Security</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Company</h4>
              <ul className="space-y-2 text-purple-200">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Blog</a></li>
                <li><a href="#" className="hover:text-white transition">Careers</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Legal</h4>
              <ul className="space-y-2 text-purple-200">
                <li><a href="#" className="hover:text-white transition">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition">Terms</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Follow Us</h4>
              <div className="flex space-x-4">
                <a href="#" className="text-2xl hover:text-purple-400 transition">f</a>
                <a href="#" className="text-2xl hover:text-purple-400 transition">𝕏</a>
                <a href="#" className="text-2xl hover:text-purple-400 transition">in</a>
              </div>
            </div>
          </div>

          <div className="border-t border-purple-400 border-opacity-30 pt-8 text-center text-purple-200">
            <p>&copy; 2025 AttendanceHub. All rights reserved. | Built for educators, by educators.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
