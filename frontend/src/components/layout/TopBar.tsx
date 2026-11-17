import React, { useEffect, useState } from 'react';
import {
  Activity,
  Cpu,
  Brain,
  Workflow,
  Database,
  Radio,
  Settings as SettingsIcon,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import { fetchSystemSettingsHealth } from '../../services/api';
import { SystemHealth } from '../../types';

interface TopBarProps {
  onOpenSettings: () => void;
  activeScenario?: string | null;
}

export const TopBar: React.FC<TopBarProps> = ({ onOpenSettings, activeScenario }) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [time, setTime] = useState<string>('');

  const loadHealth = async () => {
    setLoading(true);
    try {
      const data = await fetchSystemSettingsHealth();
      setHealth(data);
    } catch (err) {
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 10000); // 10s polling
    const handleSync = () => loadHealth();
    window.addEventListener('cybersleuth-sync', handleSync);
    return () => {
      clearInterval(interval);
      window.removeEventListener('cybersleuth-sync', handleSync);
    };
  }, []);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toISOString().substring(11, 19) + ' UTC');
    };
    updateTime();
    const tInterval = setInterval(updateTime, 1000);
    return () => clearInterval(tInterval);
  }, []);

  const isDemo = health ? health.events_count_demo > 0 : false;

  return (
    <header className="h-14 bg-charcoal/90 backdrop-blur border-b border-teal-light/40 px-4 flex items-center justify-between text-xs font-mono select-none z-20">
      {/* Left: SOC Status Indicators */}
      <div className="flex items-center space-x-4 overflow-x-auto">
        {/* Backend status */}
        <div className="flex items-center space-x-1.5" title="FastAPI Engine">
          <Activity
            className={`w-3.5 h-3.5 ${
              health?.backend_health === 'HEALTHY' ? 'text-cyan-neon' : 'text-coral-neon'
            }`}
          />
          <span className="text-[11px] text-sage">API:</span>
          <span
            className={`font-semibold ${
              health?.backend_health === 'HEALTHY' ? 'text-cyan-neon' : 'text-coral-neon'
            }`}
          >
            {health?.backend_health || 'OFFLINE'}
          </span>
        </div>

        <div className="h-3 w-px bg-teal-light/40" />

        {/* Detection Engine status */}
        <div className="flex items-center space-x-1.5" title="Rule Engine & Scikit-learn Isolation Forest">
          <Cpu className="w-3.5 h-3.5 text-lime-acid" />
          <span className="text-[11px] text-sage">DETECTION:</span>
          <span className="text-lime-acid font-semibold">RULES + ML</span>
        </div>

        <div className="h-3 w-px bg-teal-light/40" />

        {/* LLM Status */}
        <div className="flex items-center space-x-1.5" title="Forensic Reasoning Provider">
          <Brain
            className={`w-3.5 h-3.5 ${
              health?.degraded_mode ? 'text-amber-neon' : 'text-cyan-neon'
            }`}
          />
          <span className="text-[11px] text-sage">LLM:</span>
          <span
            className={`font-semibold ${
              health?.degraded_mode ? 'text-amber-neon' : 'text-cyan-neon'
            }`}
          >
            {health?.degraded_mode ? 'DEGRADED (FALLBACK)' : (health?.llm_provider?.toUpperCase() || 'ONLINE')}
          </span>
        </div>

        <div className="h-3 w-px bg-teal-light/40" />

        {/* LangGraph StateGraph */}
        <div className="flex items-center space-x-1.5" title="Compiled StateGraph Orchestration">
          <Workflow className="w-3.5 h-3.5 text-cyan-neon" />
          <span className="text-[11px] text-sage">LANGGRAPH:</span>
          <span className="text-cyan-neon font-semibold">ACTIVE</span>
        </div>

        <div className="h-3 w-px bg-teal-light/40" />

        {/* Ingestion count */}
        <div className="flex items-center space-x-1.5" title="Ingested Telemetry Events">
          <Database className="w-3.5 h-3.5 text-sage" />
          <span className="text-[11px] text-sage">EVENTS:</span>
          <span className="text-ivory font-semibold">
            {health ? health.events_count_live + health.events_count_demo : 0}
          </span>
        </div>
      </div>

      {/* Right: Environment Mode & Clock */}
      <div className="flex items-center space-x-3 shrink-0 ml-4">
        {/* Environment Badge */}
        <div
          className={`flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border ${
            isDemo
              ? 'bg-amber-neon/10 border-amber-neon/40 text-amber-neon'
              : 'bg-cyan-neon/10 border-cyan-neon/40 text-cyan-neon'
          }`}
        >
          <Radio className="w-2.5 h-2.5 animate-pulse" />
          <span>{isDemo ? 'DEMO ENVIRONMENT' : 'LIVE ENVIRONMENT'}</span>
        </div>

        {/* UTC Clock */}
        <div className="hidden md:block text-[11px] text-sage bg-obsidian/60 px-2 py-0.5 rounded border border-teal-light/30">
          {time}
        </div>

        {/* Refresh */}
        <button
          onClick={async () => {
            await loadHealth();
            window.dispatchEvent(new CustomEvent('cybersleuth-sync'));
          }}
          disabled={loading}
          className="p-1 rounded text-sage hover:text-cyan-neon hover:bg-teal-dark transition-colors"
          title="Synchronize All CyberSleuth Dashboards & Engine Status"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-neon' : ''}`} />
        </button>

        {/* Settings button */}
        <button
          onClick={onOpenSettings}
          className="p-1 rounded text-sage hover:text-cyan-neon hover:bg-teal-dark transition-colors"
          title="Open System Settings"
        >
          <SettingsIcon className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
