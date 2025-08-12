import { useState } from 'react';
import * as Sentry from '@sentry/react';
import api from '../lib/api';
import Button from './ui/Button';

interface AuthProps {
  onSuccess?: (token: string) => void;
}

export default function Auth({ onSuccess }: AuthProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[AUTH DEBUG] Login start for username:', formData.username);
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.post('/api/token', 
        `username=${encodeURIComponent(formData.username)}&password=${encodeURIComponent(formData.password)}`,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );

      const token = response.data.access_token;
      console.log('[AUTH DEBUG] Login success, received token:', token ? `${token.substring(0, 20)}...` : 'null');
      
      localStorage.setItem('token', token);
      console.log('[AUTH DEBUG] Token saved to localStorage');
      
      // Set Sentry user context
      try {
        Sentry.setUser({
          id: formData.username,
          username: formData.username,
        });
      } catch (e) {
        console.warn('Failed to set Sentry user context:', e);
      }
      
      setSuccess('Welcome back!');
      console.log('[AUTH DEBUG] Auth state updated, calling onSuccess callback');
      onSuccess?.(token);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      console.error('[AUTH DEBUG] Login failed:', error.response?.data?.detail || error.message);
      setError(error.response?.data?.detail || error.message || 'Could not sign in');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[AUTH DEBUG] Registration start for username:', formData.username, 'email:', formData.email);
    setLoading(true);
    setError(null);
    setSuccess(null);

    if (formData.password !== formData.confirmPassword) {
      console.error('[AUTH DEBUG] Registration failed: Passwords do not match');
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      // Create user
      console.log('[AUTH DEBUG] Creating user account...');
      await api.post('/api/users/', {
        email: formData.email,
        username: formData.username,
        password: formData.password
      });
      console.log('[AUTH DEBUG] User account created successfully');

      // Login to get token
      console.log('[AUTH DEBUG] Logging in with new account...');
      const loginResponse = await api.post('/api/token', 
        `username=${encodeURIComponent(formData.username)}&password=${encodeURIComponent(formData.password)}`,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );

      const token = loginResponse.data.access_token;
      console.log('[AUTH DEBUG] Registration login success, received token:', token ? `${token.substring(0, 20)}...` : 'null');
      
      localStorage.setItem('token', token);
      console.log('[AUTH DEBUG] Token saved to localStorage');
      
      // Set Sentry user context
      try {
        Sentry.setUser({
          id: formData.username,
          username: formData.username,
        });
      } catch (e) {
        console.warn('Failed to set Sentry user context:', e);
      }
      
      setSuccess('Account created — you\'re in!');
      console.log('[AUTH DEBUG] Auth state updated, calling onSuccess callback');
      onSuccess?.(token);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      console.error('[AUTH DEBUG] Registration failed:', error.response?.data?.detail || error.message);
      setError(error.response?.data?.detail || error.message || 'Could not create account');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = isLogin ? handleLogin : handleRegister;

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    setSuccess(null);
    setFormData({
      email: '',
      username: '',
      password: '',
      confirmPassword: ''
    });
  };

  return (
    <div className="card">
      <div className="card-header">
        <h1 className="card-title">
          {isLogin ? 'Welcome Back' : 'Join Your Community'}
        </h1>
        <p className="text-muted mt-2">
          {isLogin 
            ? 'Sign in to take part in decisions that shape our shared life.' 
            : 'Create your account and have your say in the choices we make together.'
          }
        </p>
      </div>
      <div className="card-content">
        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-muted mb-1">
                Email
              </label>
              <input
                type="email"
                id="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 bg-bg border border-border rounded-md text-white placeholder-muted focus:ring-2 focus:ring-primary/50 focus:border-transparent"
                placeholder="Enter your email"
                required={!isLogin}
              />
            </div>
          )}

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-muted mb-1">
              Username
            </label>
            <input
              type="text"
              id="username"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              className="w-full px-3 py-2 bg-bg border border-border rounded-md text-white placeholder-muted focus:ring-2 focus:ring-primary/50 focus:border-transparent"
              placeholder="Pick a username"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-muted mb-1">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-3 py-2 bg-bg border border-border rounded-md text-white placeholder-muted focus:ring-2 focus:ring-primary/50 focus:border-transparent"
              placeholder="Enter your password"
              required
            />
          </div>

          {!isLogin && (
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-muted mb-1">
                Confirm Password
              </label>
              <input
                type="password"
                id="confirmPassword"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                className="w-full px-3 py-2 bg-bg border border-border rounded-md text-white placeholder-muted focus:ring-2 focus:ring-primary/50 focus:border-transparent"
                placeholder="Confirm your password"
                required={!isLogin}
              />
            </div>
          )}

          {error && (
            <div className="p-3 bg-danger/10 border border-danger/20 rounded-md">
              <p className="text-sm text-danger">{error}</p>
            </div>
          )}

          {success && (
            <div className="p-3 bg-success/10 border border-success/20 rounded-md">
              <p className="text-sm text-success">{success}</p>
            </div>
          )}

          <Button 
            type="submit"
            loading={loading}
            className="w-full"
          >
            {isLogin ? 'Sign In' : 'Join'}
          </Button>

          <div className="text-center">
            <button
              type="button"
              onClick={toggleMode}
              className="text-sm text-muted hover:text-white transition-colors"
            >
              {isLogin ? "New here? Create an account" : "Already here? Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
