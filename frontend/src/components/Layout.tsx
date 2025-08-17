import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  FilePlus2,
  ListChecks,
  LogOut,
  Menu,
  X,
  Search,
  Hash,
  Users
} from 'lucide-react';
import clsx from 'clsx';
import Button from './ui/Button';
import { listLabels } from '../lib/api';
import type { Label } from '../types';
import { flags } from '../config/flags';


interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [labels, setLabels] = useState<Label[]>([]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.reload();
  };

  useEffect(() => {
    if (flags.labelsEnabled) {
      const fetchLabels = async () => {
        try {
          console.log('Fetching labels...');
          const labelsData = await listLabels();
          console.log('Labels loaded:', labelsData.length, labelsData);
          setLabels(labelsData);
        } catch (err) {
          console.error('Failed to load labels:', err);
        }
      };
      fetchLabels();
    } else {
      console.log('Labels disabled by flag');
    }
  }, []);

  const navigation = [
    { name: 'Principles', href: '/principles', icon: ListChecks },
    { name: 'Actions', href: '/actions', icon: ListChecks },
    { name: 'Share Your Idea', href: '/proposals/new', icon: FilePlus2 },
    ...(flags.labelsEnabled ? [{ name: 'Topics', href: '/topics', icon: Hash }] : []),
    { name: 'Delegations', href: '/delegations', icon: Users },
  ];

  const isActive = (href: string) => {
    if (href === '/proposals' && location.pathname.startsWith('/proposals/') && !location.pathname.includes('/new')) {
      return true;
    }
    if (href === '/principles' && location.pathname === '/principles') {
      return true;
    }
    if (href === '/actions' && location.pathname === '/actions') {
      return true;
    }
    if (href === '/delegations' && location.pathname === '/delegations') {
      return true;
    }
    if (href === '/topics' && (location.pathname === '/topics' || location.pathname.startsWith('/t/'))) {
      return true;
    }
    return location.pathname === href;
  };

  const isTopicPage = () => {
    return location.pathname.startsWith('/t/');
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* USWDS-inspired Header */}
      <header className="bg-white border-b border-neutral-200 shadow-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link
              to="/dashboard"
              className="flex items-center space-x-3"
            >
              <span className="text-xl font-bold text-neutral-900">The Commons</span>
            </Link>

            {/* Search Bar */}
            <div className="hidden md:flex items-center flex-1 max-w-md mx-8">
              <div className="relative w-full">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-500 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search proposals..."
                  className="w-full px-3 py-2 pl-10 border border-neutral-300 rounded-lg bg-white text-neutral-900 placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500"
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
                      'flex items-center px-3 py-2 text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors duration-200 rounded-md',
                      isActive(item.href) && 'text-primary-700 border-b-2 border-primary-700'
                    )}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>

            {/* User Menu */}
            <div className="hidden md:flex items-center space-x-4">
              <Button
                onClick={handleLogout}
                variant="ghost"
                size="sm"
                className="text-neutral-600 hover:text-neutral-900"
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
                className="text-neutral-600 hover:text-neutral-900"
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
          <div className="md:hidden border-t border-neutral-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 space-y-2">
              {/* Mobile Search */}
              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-500 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search proposals..."
                  className="w-full px-3 py-2 pl-10 border border-neutral-300 rounded-lg bg-white text-neutral-900 placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500"
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
                      'flex items-center px-3 py-2 text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors duration-200 rounded-md block',
                      isActive(item.href) && 'text-primary-700 bg-primary-50'
                    )}
                  >
                    <Icon className="w-5 h-5 mr-2" />
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
                className="w-full justify-start text-neutral-600 hover:text-neutral-900"
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




    </div>
  );
}
