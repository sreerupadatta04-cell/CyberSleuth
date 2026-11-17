import React from 'react';

interface SeverityBadgeProps {
  severity: string;
  size?: 'sm' | 'md';
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, size = 'md' }) => {
  const sev = (severity || 'INFO').toUpperCase();
  const sizeClasses = size === 'sm' ? 'px-1.5 py-0.5 text-[9px]' : 'px-2 py-0.5 text-[10px]';

  switch (sev) {
    case 'CRITICAL':
      return (
        <span
          className={`font-mono font-bold tracking-wider rounded border border-coral-neon/50 bg-coral-neon/10 text-coral-neon shadow-neon-coral ${sizeClasses}`}
        >
          CRITICAL
        </span>
      );
    case 'HIGH':
      return (
        <span
          className={`font-mono font-bold tracking-wider rounded border border-amber-neon/50 bg-amber-neon/10 text-amber-neon ${sizeClasses}`}
        >
          HIGH
        </span>
      );
    case 'MEDIUM':
      return (
        <span
          className={`font-mono font-semibold tracking-wider rounded border border-cyan-neon/40 bg-cyan-neon/10 text-cyan-neon ${sizeClasses}`}
        >
          MEDIUM
        </span>
      );
    case 'LOW':
      return (
        <span
          className={`font-mono font-medium tracking-wider rounded border border-sage/40 bg-sage/10 text-sage ${sizeClasses}`}
        >
          LOW
        </span>
      );
    default:
      return (
        <span
          className={`font-mono font-normal tracking-wider rounded border border-teal-light/50 bg-teal-brand/20 text-sage ${sizeClasses}`}
        >
          INFO
        </span>
      );
  }
};

interface ProvenanceBadgeProps {
  category: 'OBSERVED' | 'INFERRED' | 'UNKNOWN' | string;
  confidence?: number;
}

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({ category, confidence }) => {
  const cat = (category || 'OBSERVED').toUpperCase();
  const confText = confidence !== undefined ? ` ${Math.round(confidence * 100)}%` : '';

  if (cat === 'OBSERVED') {
    return (
      <span className="font-mono text-[9px] font-bold px-1.5 py-0.5 rounded border border-cyan-neon/40 bg-cyan-neon/15 text-cyan-neon tracking-wide">
        ● OBSERVED{confText}
      </span>
    );
  }
  if (cat === 'INFERRED') {
    return (
      <span className="font-mono text-[9px] font-bold px-1.5 py-0.5 rounded border border-amber-neon/40 bg-amber-neon/15 text-amber-neon tracking-wide">
        ◆ INFERRED{confText}
      </span>
    );
  }
  return (
    <span className="font-mono text-[9px] font-medium px-1.5 py-0.5 rounded border border-sage/40 bg-sage/10 text-sage tracking-wide">
      ? UNKNOWN
    </span>
  );
};
