import React from 'react';

const paths = {
  dashboard: <><rect x="3.5" y="3.5" width="7" height="7" rx="1" /><rect x="13.5" y="3.5" width="7" height="4" rx="1" /><rect x="13.5" y="10.5" width="7" height="10" rx="1" /><rect x="3.5" y="13.5" width="7" height="7" rx="1" /></>,
  assessment: <><path d="M12 3v18" /><path d="M17 6H9a3 3 0 0 0 0 6h6a3 3 0 0 1 0 6H6" /></>,
  recommendations: <><path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z" /></>,
  history: <><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l3 2" /></>,
  assistant: <><path d="M20 11.5a6.5 6.5 0 0 1-6.5 6.5H8l-4 3v-9.5A6.5 6.5 0 0 1 10.5 5h3A6.5 6.5 0 0 1 20 11.5Z" /><path d="M8 11h8M8 14h5" /></>,
  profile: <><circle cx="12" cy="8" r="3.5" /><path d="M5 21v-1a7 7 0 0 1 14 0v1" /></>,
  logout: <><path d="M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5" /><path d="m16 16 4-4-4-4M20 12H9" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  close: <><path d="m6 6 12 12M18 6 6 18" /></>,
  water: <><path d="M12 3.5S6.5 10 6.5 14.5a5.5 5.5 0 0 0 11 0C17.5 10 12 3.5 12 3.5Z" /><path d="M9.5 15.5a2.5 2.5 0 0 0 2.5 2" /></>,
  calendar: <><rect x="3.5" y="5" width="17" height="16" rx="2" /><path d="M7.5 3v4M16.5 3v4M3.5 10h17" /></>,
  score: <><circle cx="12" cy="9" r="6" /><path d="m9 14-1 7 4-2 4 2-1-7M12 6.5l.8 1.6 1.7.2-1.2 1.2.3 1.7-1.6-.8-1.5.8.3-1.7-1.3-1.2 1.7-.2.8-1.6Z" /></>,
  trend: <><path d="m4 16 5-5 4 3 7-8" /><path d="M14 6h6v6" /></>,
  kitchen: <><path d="M4 4v7M7 4v7M10 4v7M7 11v9M16 4v16M16 4c3 2 4 5 4 8h-4" /></>,
  shower: <><path d="M4 8a8 8 0 0 1 16 0M12 8v2" /><path d="m7 13 .01 0M11 15 .01 0M15 13 .01 0M19 15 .01 0" /></>,
  toilet: <><path d="M6 4h10v6H6zM5 10h14l-1.5 6a4 4 0 0 1-4 3h-3a4 4 0 0 1-4-3L5 10Z" /><path d="M9 22h6" /></>,
  leak: <><path d="M12 3.5S6.5 10 6.5 14.5a5.5 5.5 0 0 0 11 0C17.5 10 12 3.5 12 3.5Z" /><path d="M4 20c1.4-1 2.6-1 4 0s2.6 1 4 0 2.6-1 4 0 2.6 1 4 0" /></>,
  leaf: <><path d="M20 4C11 4 5 7 5 14a6 6 0 0 0 6 6c7 0 9-7 9-16Z" /><path d="M4 21c3-5 7-8 12-11" /></>,
  arrowRight: <><path d="M4 12h15M13 6l6 6-6 6" /></>,
  arrowLeft: <><path d="M20 12H5M11 18l-6-6 6-6" /></>,
  warning: <><path d="M10.3 4.5 2.9 17.2a2 2 0 0 0 1.7 3h14.8a2 2 0 0 0 1.7-3L13.7 4.5a2 2 0 0 0-3.4 0Z" /><path d="M12 9v4M12 17h.01" /></>,
};

export default function Icon({ name, size = 20, strokeWidth = 1.8, className = '' }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      focusable="false"
    >
      {paths[name] || null}
    </svg>
  );
}
