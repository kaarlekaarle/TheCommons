import { useState, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Activity, 
  FilePlus2, 
  ListChecks, 
  LogOut,
  Menu,
  X,
  Search
} from 'lucide-react';
import clsx from 'clsx';
import Button from './ui/Button';
import DelegationStatus from './delegation/DelegationStatus';
import DelegationOnboarding from './delegation/DelegationOnboarding';
import ManageDelegationModal from './delegation/ManageDelegationModal';
import { canUseDelegation } from '../lib/featureAccess';
import { useCurrentUser } from '../hooks/useCurrentUser';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [delegationModalOpen, setDelegationModalOpen] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const delegationStatusRef = useRef<HTMLDivElement | null>(null);
  const { user } = useCurrentUser();

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.reload();
  };

  // Check if user should see onboarding
  useEffect(() => {
    if (canUseDelegation(user?.email) && !localStorage.getItem('commons.delegation.onboarded')) {
      const timer = setTimeout(() => {
        setShowOnboarding(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [user?.email]);

  const handleLearnMore = () => {
    window.location.href = '/why';
  };

  const navigation = [
    { name: 'Community Ideas', href: '/proposals', icon: ListChecks },
    { name: 'Share Your Idea', href: '/proposals/new', icon: FilePlus2 },
  ];

  const isActive = (href: string) => {
    if (href === '/proposals' && location.pathname.startsWith('/proposals/') && !location.pathname.includes('/new')) {
      return true;
    }
    return location.pathname === href;
  };

  return (
    <div className="min-h-screen bg-gov-background">
      {/* Government Header */}
      <header className="gov-header">
        <div className="gov-container">
          <div className="flex items-center justify-between h-16">
            {/* Government Logo */}
            <Link to="/dashboard" className="flex items-center space-x-3">
              <span className="text-xl font-bold text-white">The Commons</span>
            </Link>

            {/* Search Bar */}
            <div className="hidden md:flex items-center flex-1 max-w-md mx-8">
              <div className="relative w-full">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gov-text-muted w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search proposals..."
                  className="gov-search pl-10"
                />
              </div>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={clsx(
                      'gov-nav-link',
                      isActive(item.href) && 'active'
                    )}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
              
              {/* Community Activity button */}
              <Link
                to="/activity"
                className={clsx(
                  'gov-nav-link text-sm opacity-80 hover:opacity-100',
                  isActive('/activity') && 'active'
                )}
                title="Community Activity"
              >
                <Activity className="w-3.5 h-3.5 mr-1.5" />
                <span>Activity</span>
              </Link>
            </div>

            {/* User Menu */}
            <div className="hidden md:flex items-center space-x-4">
              {(() => {
                const allowed = canUseDelegation(user?.email);
                return allowed ? (
                  <div ref={delegationStatusRef} className="w-48">
                    <DelegationStatus 
                      compact={true}
                      className="text-xs"
                      onOpenModal={() => setDelegationModalOpen(true)}
                    />
                  </div>
                ) : null;
              })()}
              <Button
                onClick={handleLogout}
                variant="ghost"
                size="sm"
                className="text-white hover:text-gov-secondary"
              >
                <LogOut className="w-4 h-4 mr-2" />
                <span>Log out</span>
              </Button>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <Button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                variant="ghost"
                size="sm"
                className="text-white hover:text-gov-secondary"
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5" />
                ) : (
                  <Menu className="w-5 h-5" />
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-white/20">
            <div className="gov-container py-4 space-y-2">
              {/* Mobile Search */}
              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gov-text-muted w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search proposals..."
                  className="gov-search pl-10 w-full"
                />
              </div>
              
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={clsx(
                      'gov-nav-link block',
                      isActive(item.href) && 'active'
                    )}
                  >
                    <Icon className="w-5 h-5 mr-2" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
              
              <Link
                to="/activity"
                onClick={() => setMobileMenuOpen(false)}
                className={clsx(
                  'gov-nav-link block',
                  isActive('/activity') && 'active'
                )}
              >
                <Activity className="w-4 h-4 mr-2" />
                <span>Community Activity</span>
              </Link>
              
              <Button
                onClick={() => {
                  handleLogout();
                  setMobileMenuOpen(false);
                }}
                variant="ghost"
                className="w-full justify-start text-white hover:text-gov-secondary"
              >
                <LogOut className="w-5 h-5 mr-2" />
                <span>Log out</span>
              </Button>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Government Footer */}
      <footer className="gov-footer">
        <div className="gov-container">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <span className="text-lg font-bold text-white">The Commons</span>
            </div>
            <div className="flex items-center space-x-6 text-sm">
              <Link to="/why" className="text-gray-300 hover:text-white transition-colors">
                Why Two Levels?
              </Link>
              <span className="text-gray-400">Deciding together, openly.</span>
            </div>
          </div>
        </div>
      </footer>

      {/* Delegation Modal */}
      {(() => {
        const allowed = canUseDelegation(user?.email);
        return allowed ? (
          <ManageDelegationModal
            open={delegationModalOpen}
            onClose={() => setDelegationModalOpen(false)}
          />
        ) : null;
      })()}

      {/* Onboarding Tooltip */}
      {(() => {
        const allowed = canUseDelegation(user?.email);
        return allowed && showOnboarding && delegationStatusRef.current ? (
          <DelegationOnboarding
            anchorRef={delegationStatusRef}
            onClose={() => setShowOnboarding(false)}
            onLearnMore={handleLearnMore}
          />
        ) : null;
      })()}
    </div>
  );
}
