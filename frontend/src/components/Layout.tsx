import { useState } from 'react';
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Activity, 
  FilePlus2, 
  ListChecks, 
  User, 
  LogOut,
  Menu,
  X
} from 'lucide-react';
import clsx from 'clsx';
import Button from './ui/Button';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.reload();
  };

  const navigation = [
    { name: 'Community Activity', href: '/activity', icon: Activity },
    { name: 'Proposals', href: '/proposals', icon: ListChecks },
    { name: 'Start a Proposal', href: '/proposals/new', icon: FilePlus2 },
    { name: 'Home', href: '/dashboard', icon: User },
  ];

  const isActive = (href: string) => {
    if (href === '/proposals' && location.pathname.startsWith('/proposals/') && !location.pathname.includes('/new')) {
      return true;
    }
    return location.pathname === href;
  };

  return (
    <div className="min-h-screen bg-bg">
      {/* Navigation */}
      <nav className="sticky top-0 z-40 bg-surface border-b border-border">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-bold text-white">The Commons</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={clsx(
                      'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive(item.href)
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted hover:text-white hover:bg-border'
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>

            {/* User Menu */}
            <div className="hidden md:flex items-center space-x-2">
              {import.meta.env.VITE_DEBUG_OVERLAY === 'true' && (
                <Button
                  onClick={() => {
                    localStorage.removeItem('token');
                    window.location.href = '/auth';
                  }}
                  variant="ghost"
                  size="sm"
                  className="flex items-center space-x-2 text-yellow-400"
                >
                  <span>🔧 Debug: Clear Token</span>
                </Button>
              )}
              <Button
                onClick={handleLogout}
                variant="ghost"
                size="sm"
                className="flex items-center space-x-2"
              >
                <LogOut className="w-4 h-4" />
                <span>Log out</span>
              </Button>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <Button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                variant="ghost"
                size="sm"
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
          <div className="md:hidden border-t border-border">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={clsx(
                      'flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium transition-colors',
                      isActive(item.href)
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted hover:text-white hover:bg-border'
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
              <Button
                onClick={() => {
                  handleLogout();
                  setMobileMenuOpen(false);
                }}
                variant="ghost"
                className="w-full justify-start"
              >
                <LogOut className="w-5 h-5 mr-2" />
                <span>Log out</span>
              </Button>
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-xs">C</span>
              </div>
              <span className="text-sm text-muted">The Commons</span>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <Link to="/why" className="text-muted hover:text-white transition-colors">
                Why Two Levels?
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
