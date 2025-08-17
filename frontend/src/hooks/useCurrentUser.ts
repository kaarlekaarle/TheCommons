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
        console.log('[DEBUG] useCurrentUser: Token present:', !!token);

        if (!token) {
          console.log('[DEBUG] useCurrentUser: No token, setting user to null');
          setUser(null);
          return;
        }

        console.log('[DEBUG] useCurrentUser: Making API call to get current user');
        const userData = await getCurrentUser();
        console.log('[DEBUG] useCurrentUser: API call successful, user data:', userData);
        setUser(userData);
      } catch (err: unknown) {
        const error = err as { status?: number; message?: string };
        console.error('Failed to fetch current user:', error);

        // Handle authentication errors gracefully
        if (error.status === 401) {
          console.log('[DEBUG] Authentication error - removing invalid token');
          localStorage.removeItem('token');
          setUser(null);
          setError(null); // Don't show error for auth issues
        } else {
          setError(error.message || 'Failed to fetch user data');
          setUser(null);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  return { user, loading, error };
}
