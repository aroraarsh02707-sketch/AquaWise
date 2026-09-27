import React from 'react';
import Icon from './Icon';

export default function AuthAside() {
  return (
    <aside className="auth-aside" aria-label="About AquaWise">
      <div className="auth-aside-content">
        <span className="auth-aside-mark" aria-hidden="true"><Icon name="water" size={38} /></span>
        <span className="auth-aside-eyebrow">WATER CONSERVATION WORKSPACE</span>
        <h2>Make your water use easier to understand.</h2>
        <p>Record household or farm water habits, review estimated consumption, and explore practical conservation recommendations.</p>
        <div className="auth-aside-rule" />
        <span className="auth-aside-caption">AquaWise · Measure thoughtfully. Conserve confidently.</span>
      </div>
    </aside>
  );
}
