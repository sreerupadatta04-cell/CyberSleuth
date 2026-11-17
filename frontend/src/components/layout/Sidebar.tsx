import React from 'react';
import {
  LayoutDashboard,
  ShieldAlert,
  Search,
  Network,
  CheckCircle2,
  FileText,
  Database,
  Sliders,
  ChevronLeft,
  ChevronRight,
  Terminal,
  Activity
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  collapsed,
  onToggleCollapse,
}) => {
  const menuItems = [
    { id: 'command-center', label: 'Command Center', icon: LayoutDashboard, badge: null },
    { id: 'threat-detection', label: 'Threat Detection', icon: ShieldAlert, badge: 'RULES+ML' },
    { id: 'investigations', label: 'Investigations', icon: Search, badge: 'GRAPH' },
    { id: 'evidence-explorer', label: 'Evidence Explorer', icon: Network, badge: null },
    { id: 'response-center', label: 'Response Center', icon: CheckCircle2, badge: 'HITL' },
    { id: 'reports', label: 'Reports', icon: FileText, badge: 'PDF' },
    { id: 'telemetry', label: 'Telemetry', icon: Database, badge: null },
    { id: 'settings', label: 'System Settings', icon: Sliders, badge: null },
  ];

  return (
    <aside
      className={`h-screen bg-charcoal border-r border-teal-light/40 flex flex-col transition-all duration-200 z-30 select-none ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-teal-light/30">
        {!collapsed && (
          <div className="flex items-center space-x-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded bg-teal-brand border border-cyan-neon/40 flex items-center justify-center shadow-neon-cyan">
              <Terminal className="w-4 h-4 text-cyan-neon" />
            </div>
            <div>
              <div className="font-heading font-bold text-sm tracking-wide text-ivory flex items-center gap-1.5">
                CYBER<span className="text-cyan-neon">SLEUTH</span>
              </div>
              <div className="text-[10px] font-mono tracking-wider text-sage uppercase">
                v1.0 // SOC AGENT
              </div>
            </div>
          </div>
        )}

        {collapsed && (
          <div className="w-full flex justify-center">
            <div className="w-8 h-8 rounded bg-teal-brand border border-cyan-neon/40 flex items-center justify-center shadow-neon-cyan">
              <Terminal className="w-4 h-4 text-cyan-neon" />
            </div>
          </div>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-4 px-2 space-y-1.5 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              title={collapsed ? item.label : undefined}
              className={`w-full flex items-center rounded px-3 py-2.5 text-xs font-medium transition-all group relative ${
                isActive
                  ? 'bg-teal-brand text-cyan-neon border-l-2 border-cyan-neon shadow-panel'
                  : 'text-sage hover:text-ivory hover:bg-teal-dark/50'
              }`}
            >
              <Icon
                className={`w-4 h-4 shrink-0 transition-transform ${
                  isActive ? 'text-cyan-neon' : 'text-sage group-hover:text-cyan-neon'
                } ${collapsed ? 'mx-auto' : 'mr-3'}`}
              />

              {!collapsed && (
                <span className="flex-1 text-left truncate tracking-tight">{item.label}</span>
              )}

              {!collapsed && item.badge && (
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase tracking-wider ${
                    isActive
                      ? 'border-cyan-neon/40 text-cyan-neon bg-cyan-neon/10'
                      : 'border-teal-light text-sage/70'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Controls */}
      <div className="p-3 border-t border-teal-light/30">
        <button
          onClick={onToggleCollapse}
          className="w-full flex items-center justify-center p-2 rounded text-sage hover:text-cyan-neon hover:bg-teal-dark/50 transition-colors"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          {!collapsed && <span className="ml-2 text-xs font-mono">COLLAPSE</span>}
        </button>
      </div>
    </aside>
  );
};
