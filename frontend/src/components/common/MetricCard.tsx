import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  icon: LucideIcon;
  variant?: 'cyan' | 'lime' | 'amber' | 'coral' | 'teal';
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  sublabel,
  icon: Icon,
  variant = 'cyan',
  onClick,
}) => {
  const variantStyles = {
    cyan: {
      border: 'border-cyan-neon/30 hover:border-cyan-neon/60',
      text: 'text-cyan-neon',
      glow: 'shadow-neon-cyan',
      bg: 'bg-cyan-neon/5',
    },
    lime: {
      border: 'border-lime-acid/30 hover:border-lime-acid/60',
      text: 'text-lime-acid',
      glow: 'shadow-neon-lime',
      bg: 'bg-lime-acid/5',
    },
    amber: {
      border: 'border-amber-neon/30 hover:border-amber-neon/60',
      text: 'text-amber-neon',
      glow: '',
      bg: 'bg-amber-neon/5',
    },
    coral: {
      border: 'border-coral-neon/30 hover:border-coral-neon/60',
      text: 'text-coral-neon',
      glow: 'shadow-neon-coral',
      bg: 'bg-coral-neon/5',
    },
    teal: {
      border: 'border-teal-light/40 hover:border-cyan-neon/40',
      text: 'text-ivory',
      glow: '',
      bg: 'bg-teal-brand/10',
    },
  }[variant];

  return (
    <div
      onClick={onClick}
      className={`relative p-4 rounded-lg bg-charcoal border ${variantStyles.border} transition-all duration-200 select-none ${
        onClick ? 'cursor-pointer hover:-translate-y-0.5' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-mono tracking-wider text-sage uppercase">
          {label}
        </span>
        <div className={`p-1.5 rounded ${variantStyles.bg} ${variantStyles.text}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className={`text-2xl font-mono font-bold tracking-tight ${variantStyles.text}`}>
        {value}
      </div>

      {sublabel && (
        <div className="mt-1 text-[11px] font-mono text-sage/80 truncate">
          {sublabel}
        </div>
      )}
    </div>
  );
};
