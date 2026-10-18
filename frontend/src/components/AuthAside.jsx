import React from 'react';
import Icon from './Icon';

export default function AuthAside() {
  return (
    <aside className="auth-aside auth-story" aria-label="About AquaWise">
      <div className="auth-story-copy"><span className="auth-aside-eyebrow">A BETTER RELATIONSHIP WITH WATER</span><h2>See the system.<br/><em>Change the story.</em></h2><p>Bring household routines and everyday water use into focus. AquaWise helps make the next step understandable.</p><div className="story-principles"><span><i>01</i>Measure with context</span><span><i>02</i>Find where it matters</span><span><i>03</i>Make progress visible</span></div></div>
      <div className="story-art" aria-hidden="true"><div className="story-art-grid"/><div className="story-waterline line-one"/><div className="story-waterline line-two"/><div className="story-waterline line-three"/><span className="story-art-drop"><Icon name="water" size={46}/></span><span className="story-art-caption">AQUAWISE / WATER INTELLIGENCE</span></div>
    </aside>
  );
}
