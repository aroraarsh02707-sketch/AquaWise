import React from 'react';

const paths = {
  dashboard: <><rect x="3.5" y="3.5" width="7" height="7" rx="1" /><rect x="13.5" y="3.5" width="7" height="4" rx="1" /><rect x="13.5" y="10.5" width="7" height="10" rx="1" /><rect x="3.5" y="13.5" width="7" height="7" rx="1" /></>,
  assessment: <><path d="M12 3v18" /><path d="M17 6H9a3 3 0 0 0 0 6h6a3 3 0 0 1 0 6H6" /></>,
  recommendations: <><path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z" /></>,
  assistant: <><path d="M20 11.5a6.5 6.5 0 0 1-6.5 6.5H8l-4 3v-9.5A6.5 6.5 0 0 1 10.5 5h3A6.5 6.5 0 0 1 20 11.5Z" /><path d="M8 11h8M8 14h5" /></>,
  profile: <><circle cx="12" cy="8" r="3.5" /><path d="M5 21v-1a7 7 0 0 1 14 0v1" /></>,
  logout: <><path d="M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5" /><path d="m16 16 4-4-4-4M20 12H9" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  close: <><path d="m6 6 12 12M18 6 6 18" /></>,
  water: <><path d="M12 3.5S6.5 10 6.5 14.5a5.5 5.5 0 0 0 11 0C17.5 10 12 3.5 12 3.5Z" /><path d="M9.5 15.5a2.5 2.5 0 0 0 2.5 2" /></>,
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
