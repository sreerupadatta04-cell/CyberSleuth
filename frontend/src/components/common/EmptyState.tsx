import React from 'react';
import { LucideIcon, Database } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = Database,
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-teal-light/40 rounded-xl bg-charcoal/40 my-4">
      <div className="w-12 h-12 rounded-lg bg-teal-brand/30 border border-teal-light flex items-center justify-center mb-4 text-cyan-neon shadow-neon-cyan">
        <Icon className="w-6 h-6" />
      </div>

      <h3 className="font-heading font-semibold text-lg text-ivory tracking-tight mb-1">
        {title}
      </h3>

      <p className="text-sm text-sage max-w-md font-sans mb-6">
        {description}
      </p>

      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 rounded bg-teal-brand border border-cyan-neon/40 text-cyan-neon font-mono text-xs font-semibold hover:bg-cyan-neon hover:text-obsidian transition-colors shadow-neon-cyan"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};
