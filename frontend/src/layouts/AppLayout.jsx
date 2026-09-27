import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AnimatePresence, motion } from 'framer-motion';
import Icon from '../components/Icon';

const primaryLinks = [
  { name: 'Overview', path: '/dashboard', icon: 'dashboard' },
  { name: 'Assessment', path: '/assessment', icon: 'assessment' },
  { name: 'Recommendations', path: '/recommendations', icon: 'recommendations' },
  { name: 'Water assistant', path: '/assistant', icon: 'assistant' },
];

const AppLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.matchMedia('(max-width: 768px)').matches);

  useEffect(() => {
    const media = window.matchMedia('(max-width: 768px)');
    const handleViewportChange = (event) => {
      setIsMobile(event.matches);
      if (!event.matches) setMobileMenuOpen(false);
    };
    media.addEventListener('change', handleViewportChange);
    return () => media.removeEventListener('change', handleViewportChange);
  }, []);

  useEffect(() => {
    if (!mobileMenuOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setMobileMenuOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [mobileMenuOpen]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <div className="app-layout">
      <header className="mobile-header">
        <div className="mobile-brand">
          <Icon name="water" size={23} />
          <span className="logo">AquaWise</span>
        </div>
        <button
          type="button"
          className="icon-btn"
          aria-label={mobileMenuOpen ? 'Close navigation' : 'Open navigation'}
          aria-expanded={mobileMenuOpen}
          aria-controls="app-sidebar"
          onClick={() => setMobileMenuOpen((open) => !open)}
        >
          <Icon name={mobileMenuOpen ? 'close' : 'menu'} />
        </button>
      </header>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.button
            type="button"
            aria-label="Close navigation"
            className="mobile-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeMobileMenu}
          />
        )}
      </AnimatePresence>

      <aside
        id="app-sidebar"
        className={`sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}
        aria-label="Main navigation"
        aria-hidden={isMobile && !mobileMenuOpen}
        inert={isMobile && !mobileMenuOpen}
      >
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <span className="brand-mark"><Icon name="water" size={21} /></span>
            <span className="sidebar-wordmark">AquaWise</span>
          </div>
          <span className="brand-caption">WATER CONSERVATION</span>
        </div>

        <nav className="sidebar-nav">
          <span className="nav-section-label">Workspace</span>
          {primaryLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              end={link.path === '/dashboard' || link.path === '/recommendations'}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              onClick={closeMobileMenu}
            >
              <Icon name={link.icon} className="icon" />
              <span>{link.name}</span>
            </NavLink>
          ))}
          <span className="nav-section-label account-label">Account</span>
          <NavLink
            to="/profile"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <Icon name="profile" className="icon" />
            <span>Profile</span>
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="avatar" aria-hidden="true">{user?.name?.charAt(0).toUpperCase() || '?'}</div>
            <div className="user-details">
              <span className="user-name">{user?.name || 'AquaWise user'}</span>
              <span className="user-type">{user?.user_type || 'Account'}</span>
            </div>
          </div>
          <button onClick={handleLogout} className="logout-btn nav-link" type="button">
            <Icon name="logout" className="icon" />
            <span>Log out</span>
          </button>
        </div>
      </aside>

      <main className="main-content">
        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AppLayout;
