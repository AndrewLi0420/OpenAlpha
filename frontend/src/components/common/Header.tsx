import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import Navigation from './Navigation';

interface HeaderProps {
  className?: string;
}

/**
 * Header component with app title/logo and navigation
 * Responsive: Desktop shows full nav, mobile shows hamburger menu
 */
export default function Header({ className = '' }: HeaderProps) {
  const { user, logout, isLoggingOut } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <header className={`bg-black border-b border-gray-800 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Title */}
          <Link to="/dashboard" className="flex items-center">
            <h1 className="text-xl font-bold text-white">
              Open<span className="text-financial-blue-light">Alpha</span>
            </h1>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:gap-4">
            {user && <Navigation />}
            {user && (
              <button
                onClick={() => logout()}
                disabled={isLoggingOut}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
              >
                {isLoggingOut ? 'Logging out...' : 'Logout'}
              </button>
            )}
          </div>

          {/* Mobile Menu Button */}
          {user && (
            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-2 text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
              aria-label="Toggle menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                {mobileMenuOpen ? (
                  <path d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          )}
        </div>

        {/* Mobile Navigation */}
        {user && mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-800">
            <Navigation onLinkClick={closeMobileMenu} />
            <div className="mt-4">
              <button
                onClick={() => {
                  closeMobileMenu();
                  logout();
                }}
                disabled={isLoggingOut}
                className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
              >
                {isLoggingOut ? 'Logging out...' : 'Logout'}
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

