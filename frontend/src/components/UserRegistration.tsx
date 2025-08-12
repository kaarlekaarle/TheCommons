import { useState } from 'react';
import api from '../lib/api';
import Button from './ui/Button';

interface UserRegistrationProps {
  onSuccess?: (token: string) => void;
}

export default function UserRegistration({ onSuccess }: UserRegistrationProps) {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      // Create user
      await api.post('/api/users/', {
        email: formData.email,
        username: formData.username,
        password: formData.password
      });

      // Login to get token
      const loginResponse = await api.post('/api/token', 
        `username=${encodeURIComponent(formData.username)}&password=${encodeURIComponent(formData.password)}`,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );

      const token = loginResponse.data.access_token;
      localStorage.setItem('token', token);
      
      setSuccess('User created and logged in successfully!');
      onSuccess?.(token);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(error.response?.data?.detail || error.message || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h1 className="card-title">Create Account</h1>
      </div>
      <div className="card-content">
        <form onSubmit={handleSubmit} className="space-y-4">
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
              required
            />
          </div>

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
              placeholder="Choose a username"
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
              required
            />
          </div>

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
            Create Account
          </Button>
        </form>
      </div>
    </div>
  );
}
