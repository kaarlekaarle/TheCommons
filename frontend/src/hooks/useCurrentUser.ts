import { useState, useEffect } from 'react';
import { getCurrentUser } from '../lib/api';
import type { User } from '../types';

export function useCurrentUser() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Check if user is authenticated
        const token = localStorage.getItem('token');
        if (!token) {
          setUser(null);
          return;
        }

        const userData = await getCurrentUser();
        setUser(userData);
      } catch (err: unknown) {
        const error = err as { status?: number; message?: string };
        console.error('Failed to fetch current user:', error);
        setError(error.message || 'Failed to fetch user data');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  return { user, loading, error };
}
