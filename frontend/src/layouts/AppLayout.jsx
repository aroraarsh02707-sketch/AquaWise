import React, { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import Icon from '../components/Icon';

const links = [
  { label: 'Overview', path: '/dashboard', icon: 'dashboard' },
  { label: 'Assess water use', path: '/assessment', icon: 'assessment' },
  { label: 'History', path: '/recommendations', icon: 'history' },
  { label: 'Water assistant', path: '/assistant', icon: 'assistant' },
];
const titles = { '/dashboard': 'Overview', '/assessment': 'Assessment', '/recommendations': 'History', '/assistant': 'Water assistant', '/profile': 'Your profile' };

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const title = location.pathname.startsWith('/recommendations/') ? 'Action plan' : (titles[location.pathname] || 'AquaWise');
  const handleLogout = async () => { await logout(); navigate('/login'); };

  return (
    <div className="workspace-shell">
      <header className="workspace-topbar">
        <NavLink to="/dashboard" className="wordmark" aria-label="AquaWise home"><span className="wordmark-symbol"><Icon name="water" size={21} /></span><span>AquaWise</span><small>WATER INTELLIGENCE</small></NavLink>
        <button className="mobile-menu-trigger" type="button" aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}><Icon name={menuOpen ? 'close' : 'menu'} /></button>
        <AnimatePresence>
          <motion.nav className={`workspace-nav ${menuOpen ? 'is-open' : ''}`} aria-label="Main navigation" initial={false}>
            {links.map((link) => <NavLink key={link.path} to={link.path} end={link.path === '/dashboard' || link.path === '/recommendations'} className={({ isActive }) => `workspace-nav-link ${isActive ? 'active' : ''}`} onClick={() => setMenuOpen(false)}><Icon name={link.icon} size={17} /><span>{link.label}</span></NavLink>)}
          </motion.nav>
        </AnimatePresence>
        <div className="topbar-account"><span className="topbar-status"><i /> Workspace live</span><NavLink to="/profile" className="account-chip" aria-label="Open profile"><span className="account-avatar">{user?.name?.charAt(0).toUpperCase() || '?'}</span><span className="account-name">{user?.name || 'Account'}</span><Icon name="arrowRight" size={15} /></NavLink><button type="button" className="logout-control" onClick={handleLogout}>Sign out</button></div>
      </header>
      <div className="workspace-context"><div className="context-breadcrumb"><span>Workspace</span><span className="context-slash">/</span><strong>{title}</strong></div><div className="context-note"><span className="context-dot" />{user?.user_type === 'farmer' ? 'Farm water profile' : 'Household water profile'}</div></div>
      <main className="workspace-main"><div className="page-content"><Outlet /></div></main>
      <nav className="mobile-tabbar" aria-label="Mobile navigation">{links.slice(0, 4).map((link) => <NavLink key={link.path} to={link.path} end={link.path === '/dashboard' || link.path === '/recommendations'} className={({ isActive }) => `mobile-tab ${isActive ? 'active' : ''}`}><Icon name={link.icon} size={19} /><span>{link.label === 'Assess water use' ? 'Assess' : link.label === 'Water assistant' ? 'Ask' : link.label}</span></NavLink>)}</nav>
    </div>
  );
}
