import React from 'react';
import Icon from './Icon';

export function PageHeading({ eyebrow, title, description, action, meta }) {
  return <header className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{description && <p className="page-description">{description}</p>}</div><div className="page-heading-trailing">{meta}{action}</div></header>;
}

export function StatePanel({ title, description, action, tone = 'neutral', icon = 'water' }) {
  return <section className={`state-panel state-${tone}`} role={tone === 'error' ? 'alert' : undefined}><span className="state-icon"><Icon name={icon} size={21} /></span><div><h2>{title}</h2><p>{description}</p></div>{action && <div className="state-action">{action}</div>}</section>;
}

export function SectionTitle({ eyebrow, title, aside }) {
  return <div className="section-title"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>{aside}</div>;
}
