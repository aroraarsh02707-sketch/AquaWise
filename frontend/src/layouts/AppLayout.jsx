import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import '../App.css'; // Will use index.css for global layout styles

// Basic inline SVGs to avoid extra dependencies
const Icons = {
  Dashboard: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>,
  Assessment: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>,
  Recommendations: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>,
  Assistant: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>,
  Profile: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>,
  Logout: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>,
  Menu: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>,
  Close: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
};

const AppLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navLinks = [
    { name: 'Dashboard', path: '/dashboard', icon: <Icons.Dashboard /> },
    { name: 'Assessment', path: '/assessment', icon: <Icons.Assessment /> },
    { name: 'Recommendations', path: '/recommendations', icon: <Icons.Recommendations /> },
    { name: 'AI Assistant', path: '/assistant', icon: <Icons.Assistant /> },
    { name: 'Profile', path: '/profile', icon: <Icons.Profile /> },
  ];

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <div className="app-layout">
      {/* Mobile Header */}
      <div className="mobile-header">
        <h1 className="logo">AquaWise</h1>
        <button className="icon-btn" onClick={() => setMobileMenuOpen(true)}>
          <Icons.Menu />
        </button>
      </div>

      {/* Sidebar Navigation */}
      <AnimatePresence>
        {(mobileMenuOpen || window.innerWidth > 768) && (
          <>
            {mobileMenuOpen && (
              <motion.div 
                className="mobile-overlay"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={closeMobileMenu}
              />
            )}
            <motion.aside 
              className={`sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}
              initial={mobileMenuOpen ? { x: '-100%' } : false}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'tween', duration: 0.3 }}
            >
              <div className="sidebar-header">
                <h1 className="logo">AquaWise</h1>
                {mobileMenuOpen && (
                  <button className="icon-btn close-btn" onClick={closeMobileMenu}>
                    <Icons.Close />
                  </button>
                )}
              </div>
              
              <nav className="sidebar-nav">
                {navLinks.map((link) => (
                  <NavLink 
                    key={link.name}
                    to={link.path} 
                    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                    onClick={closeMobileMenu}
                  >
                    {link.icon}
                    <span>{link.name}</span>
                  </NavLink>
                ))}
              </nav>

              <div className="sidebar-footer">
                <div className="user-info">
                  <div className="avatar">{user?.name?.charAt(0).toUpperCase()}</div>
                  <div className="user-details">
                    <span className="user-name">{user?.name}</span>
                    <span className="user-type">{user?.user_type}</span>
                  </div>
                </div>
                <button onClick={handleLogout} className="logout-btn nav-link">
                  <Icons.Logout />
                  <span>Log Out</span>
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
