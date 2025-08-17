import React, { useState, useEffect, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { ToasterProvider } from './components/ui/Toaster';
import Layout from './components/Layout';
import Auth from './components/Auth';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import ProposalList from './pages/ProposalList';
import ProposalDetail from './pages/ProposalDetail';
import ProposalNew from './pages/ProposalNew';
import PrinciplesList from './pages/PrinciplesList';
import ActionsList from './pages/ActionsList';
import TopicPage from './pages/TopicPage';
import TopicsRouteWrapper from './components/TopicsRouteWrapper';
import ActivityFeed from './components/ActivityFeed';
import DebugOverlay from './components/DebugOverlay';
const DelegationsPage = React.lazy(() => import('./pages/DelegationsPage'));
import { flags } from './config/flags';

// Lazy load the WhyTwoLevels page
const WhyTwoLevels = React.lazy(() => import('./pages/WhyTwoLevels'));

// Lazy load the CompassPage
const CompassPage = React.lazy(() => import('./pages/CompassPage'));

// Lazy load the PrincipleDocPage
const PrincipleDocPage = React.lazy(() => import('./pages/PrincipleDocPage'));

// Lazy load the PrincipleDiffPage
const PrincipleDiffPage = React.lazy(() => import('./pages/PrincipleDiffPage'));

// Dev-only accessibility check page
const A11yCheck = React.lazy(() => import('./pages/_A11yCheck'));



export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isValidating, setIsValidating] = useState(true);

  // Validate token on app start
  useEffect(() => {
    const validateToken = async () => {
      console.log('[AUTH DEBUG] Starting token validation...');
      const token = localStorage.getItem('token');
      console.log('[AUTH DEBUG] App initialization - Token found in storage:', !!token);

      if (!token) {
        console.log('[AUTH DEBUG] No token found, user not authenticated');
        setIsAuthenticated(false);
        setIsValidating(false);
        return;
      }

      try {
        // First check if token is expired
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
          setIsAuthenticated(false);
          setIsValidating(false);
          return;
        }

        // Test token against backend
        console.log('[AUTH DEBUG] Testing token against backend...');
        const { getCurrentUser } = await import('./lib/api');
        await getCurrentUser();

        console.log('[AUTH DEBUG] Token is valid, user authenticated');
        setIsAuthenticated(true);
      } catch (error) {
        console.error('[AUTH DEBUG] Token validation failed:', error);
        console.log('[AUTH DEBUG] Removing invalid token from storage');
        localStorage.removeItem('token');
        setIsAuthenticated(false);
              } finally {
          console.log('[AUTH DEBUG] Token validation completed, isValidating set to false');
          setIsValidating(false);
        }
      };

    validateToken();
  }, []);

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

  // Show loading screen while validating token
  if (isValidating) {
    return (
      <ToasterProvider>
        <div className="min-h-screen bg-bg flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted">Loading...</p>
          </div>
        </div>
      </ToasterProvider>
    );
  }

  return (
    <ToasterProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" /> : <LandingPage />} />
          <Route path="/why" element={
            <Suspense fallback={<div className="min-h-screen bg-bg flex items-center justify-center"><div className="p-8 text-muted">Loading…</div></div>}>
              <WhyTwoLevels />
            </Suspense>
          } />


          {/* Dev-only accessibility check route */}
          {import.meta.env.DEV && (
            <Route path="/_a11y" element={
              <Suspense fallback={<div className="min-h-screen bg-neutral-50 flex items-center justify-center"><div className="p-8 text-neutral-600">Loading…</div></div>}>
                <A11yCheck />
              </Suspense>
            } />
          )}



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
                    <div className="text-center mt-6">
                      <Link to="/why" className="text-sm text-muted hover:text-white underline">
                        What's "two levels"? Read the 2‑min explainer
                      </Link>
                    </div>
                  </div>
                </div>
              ) : (
                <Navigate to="/dashboard" replace />
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
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/principles" element={<PrinciplesList />} />
                    <Route path="/actions" element={<ActionsList />} />
                    <Route path="/proposals" element={<ProposalList />} />
                    <Route path="/proposals/:id" element={<ProposalDetail />} />
                    <Route path="/proposals/new" element={<ProposalNew />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/activity" element={<ActivityFeed />} />
                    <Route path="/delegations" element={<DelegationsPage />} />
                    <Route path="/t/:slug" element={<TopicPage />} />
                    <Route path="/topics" element={<TopicsRouteWrapper />} />
                    <Route path="/topics/disabled" element={<TopicsRouteWrapper />} />
                    {flags.compassEnabled && (
                      flags.principlesDocMode ? (
                        <>
                          <Route path="/compass/:id" element={<PrincipleDocPage />} />
                          <Route path="/compass/:id/diff" element={<PrincipleDiffPage />} />
                        </>
                      ) : (
                        <Route path="/compass/:id" element={<CompassPage />} />
                      )
                    )}
                    {!flags.compassEnabled && (
                      <Route path="/compass/:id" element={<Navigate to="/proposals" replace />} />
                    )}
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
