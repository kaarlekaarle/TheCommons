import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToasterProvider } from './components/ui/Toaster';
import Layout from './components/Layout';
import Auth from './components/Auth';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import ProposalList from './pages/ProposalList';
import ProposalDetail from './pages/ProposalDetail';
import ProposalNew from './pages/ProposalNew';
import ActivityFeed from './components/ActivityFeed';
import DebugOverlay from './components/DebugOverlay';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    const token = localStorage.getItem('token');
    console.log('[AUTH DEBUG] App initialization - Token found in storage:', !!token);
    
    if (token) {
      try {
        // Decode JWT to check expiration
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expirationTime = payload.exp * 1000; // Convert to milliseconds
        const currentTime = Date.now();
        const isExpired = currentTime > expirationTime;
        
        console.log('[AUTH DEBUG] Token validation:', {
          expirationTime: new Date(expirationTime).toISOString(),
          currentTime: new Date(currentTime).toISOString(),
          isExpired,
          timeUntilExpiry: Math.floor((expirationTime - currentTime) / 1000) + ' seconds'
        });
        
        if (isExpired) {
          console.log('[AUTH DEBUG] Token is expired, removing from storage');
          localStorage.removeItem('token');
          return false;
        }
        
        console.log('[AUTH DEBUG] Token is valid, user authenticated');
        return true;
      } catch (error) {
        console.error('[AUTH DEBUG] Error parsing token:', error);
        console.log('[AUTH DEBUG] Removing invalid token from storage');
        localStorage.removeItem('token');
        return false;
      }
    }
    
    console.log('[AUTH DEBUG] No token found, user not authenticated');
    return false;
  });

  // Check if debug overlay should be shown
  const isDebugOverlayVisible = import.meta.env.VITE_DEBUG_OVERLAY === 'true';

  // Listen for storage changes (when token is removed by API interceptor)
  useEffect(() => {
    const handleStorageChange = () => {
      const token = localStorage.getItem('token');
      console.log('[AUTH DEBUG] Storage change detected - Token present:', !!token);
      setIsAuthenticated(!!token);
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const handleRegistrationSuccess = (token: string) => {
    console.log('[AUTH DEBUG] Registration success callback - Setting token and updating auth state');
    localStorage.setItem('token', token);
    setIsAuthenticated(true);
    console.log('[AUTH DEBUG] Auth state updated to authenticated');
  };

  // Note: handleLogout is kept for potential future use in Layout component
  const handleLogout = () => {
    console.log('[AUTH DEBUG] Logout initiated - Removing token and updating auth state');
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    console.log('[AUTH DEBUG] Auth state updated to not authenticated');
  };
  // Suppress unused variable warning
  void handleLogout;

  return (
    <ToasterProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          
          {/* Authentication route */}
          <Route 
            path="/auth" 
            element={
              !isAuthenticated ? (
                <div className="min-h-screen bg-bg flex items-center justify-center p-4">
                  <div className="w-full max-w-md">
                    <div className="text-center mb-8">
                      <h1 className="text-3xl font-bold text-white mb-2">The Commons</h1>
                      <p className="text-muted">Join the conversation</p>
                    </div>
                    <div className="card">
                      <div className="card-content">
                        <Auth onSuccess={handleRegistrationSuccess} />
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <Navigate to="/proposals" replace />
              )
            } 
          />
          
          {/* Protected routes - redirect to auth if not authenticated */}
          <Route 
            path="/*" 
            element={
              isAuthenticated ? (
                <Layout>
                  <Routes>
                    <Route path="/" element={<Navigate to="/proposals" replace />} />
                    <Route path="/proposals" element={<ProposalList />} />
                    <Route path="/proposals/:id" element={<ProposalDetail />} />
                    <Route path="/proposals/new" element={<ProposalNew />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/activity" element={<ActivityFeed />} />
                  </Routes>
                </Layout>
              ) : (
                <Navigate to="/auth" replace />
              )
            } 
          />
        </Routes>
      </Router>
      <DebugOverlay isVisible={isDebugOverlayVisible} />
    </ToasterProvider>
  );
}
