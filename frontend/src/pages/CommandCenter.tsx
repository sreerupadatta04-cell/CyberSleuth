import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  Flame,
  Search,
  CheckCircle2,
  Cpu,
  Database,
  ArrowRight,
  Upload,
  Play,
  Terminal,
  Activity,
  Layers,
  RefreshCw
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { fetchOverview, triggerDetectionRun } from '../services/api';
import { OverviewData } from '../types';
import { MetricCard } from '../components/common/MetricCard';
import { SeverityBadge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';

interface CommandCenterProps {
  onNavigate: (tab: string, state?: any) => void;
  onOpenDemoWizard: () => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({ onNavigate, onOpenDemoWizard }) => {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [detecting, setDetecting] = useState<boolean>(false);

  const loadData = async (silent: boolean = false) => {
    try {
      if (!silent) setLoading(true);
      const res = await fetchOverview();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Continuous 4-second synchronization with loaded scenarios & background investigations
    const interval = setInterval(() => {
      fetchOverview()
        .then((res) => setData(res))
        .catch(() => {});
    }, 4000);

    const handleSync = () => loadData(true);
    window.addEventListener('cybersleuth-sync', handleSync);

    return () => {
      clearInterval(interval);
      window.removeEventListener('cybersleuth-sync', handleSync);
    };
  }, []);

  const handleRunDetection = async () => {
    try {
      setDetecting(true);
      await triggerDetectionRun(true);
      await triggerDetectionRun(false);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setDetecting(false);
    }
  };

  const SEVERITY_COLORS: Record<string, string> = {
    CRITICAL: '#FF626C',
    HIGH: '#FFB454',
    MEDIUM: '#00D5C5',
    LOW: '#91AAA5',
  };

  const TYPE_COLORS = ['#00D5C5', '#B6FF5C'];

  if (loading && !data) {
    return (
      <div className="flex h-64 items-center justify-center font-mono text-cyan-neon text-sm">
        <Activity className="w-5 h-5 mr-2 animate-spin" />
        INITIALIZING COMMAND CENTER METRICS...
      </div>
    );
  }

  const metrics = data?.metrics || {
    total_events: 0,
    live_events: 0,
    demo_events: 0,
    total_alerts: 0,
    active_alerts: 0,
    critical_threats: 0,
    investigations_running: 0,
    investigations_completed: 0,
    detected_anomalies: 0,
    rule_detections: 0,
  };

  const hasData = metrics.total_events > 0;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-teal-light/40 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-cyan-neon animate-pulse" />
            <h1 className="text-xl md:text-2xl font-bold font-heading tracking-tight text-ivory">
              SOC COMMAND CENTER
            </h1>
          </div>
          <p className="text-xs font-mono text-sage mt-1">
            Autonomous multi-agent investigation & real-time telemetry surveillance
          </p>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center space-x-2.5 shrink-0">
          <button
            onClick={() => onNavigate('telemetry')}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-charcoal border border-teal-light hover:border-cyan-neon/50 text-xs font-mono text-ivory hover:text-cyan-neon transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>UPLOAD TELEMETRY</span>
          </button>

          <button
            onClick={onOpenDemoWizard}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-teal-brand border border-cyan-neon/40 hover:bg-teal-light text-xs font-mono text-cyan-neon shadow-neon-cyan transition-colors"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>DEMO SCENARIOS</span>
          </button>

          <button
            onClick={async () => {
              setRefreshing(true);
              await loadData(true);
              setRefreshing(false);
            }}
            disabled={refreshing}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-charcoal border border-teal-light hover:border-cyan-neon text-xs font-mono text-sage hover:text-cyan-neon transition-colors"
            title="Synchronize dashboard metrics with latest scenario telemetry"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-cyan-neon' : ''}`} />
            <span>SYNC</span>
          </button>

          <button
            onClick={handleRunDetection}
            disabled={detecting}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-lime-acid/15 border border-lime-acid/40 hover:bg-lime-acid/25 text-xs font-mono text-lime-acid transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${detecting ? 'animate-spin' : ''}`} />
            <span>{detecting ? 'ANALYZING...' : 'RUN DETECTION'}</span>
          </button>
        </div>
      </div>

      {!hasData && (
        <EmptyState
          title="No Telemetry Data Ingested"
          description="CyberSleuth is currently idle. Ingest live network/system telemetry via JSON or CSV, or load one of our 4 pre-packaged realistic cyberattack scenarios to witness autonomous multi-agent LangGraph investigation."
          actionLabel="EXPLORE DEMO SCENARIOS"
          onAction={onOpenDemoWizard}
        />
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          label="Telemetry Events"
          value={metrics.total_events}
          sublabel={`${metrics.live_events} Live / ${metrics.demo_events} Demo`}
          icon={Database}
          variant="teal"
          onClick={() => onNavigate('telemetry')}
        />

        <MetricCard
          label="Active Alerts"
          value={metrics.active_alerts}
          sublabel={`${metrics.total_alerts} Total Detected`}
          icon={ShieldAlert}
          variant="amber"
          onClick={() => onNavigate('threat-detection')}
        />

        <MetricCard
          label="Critical Threats"
          value={metrics.critical_threats}
          sublabel="Immediate Containment"
          icon={Flame}
          variant="coral"
          onClick={() => onNavigate('threat-detection', { severity: 'CRITICAL' })}
        />

        <MetricCard
          label="Running Invs"
          value={metrics.investigations_running}
          sublabel="LangGraph Agents"
          icon={Search}
          variant="cyan"
          onClick={() => onNavigate('investigations')}
        />

        <MetricCard
          label="Completed Invs"
          value={metrics.investigations_completed}
          sublabel="Evidence-Grounded"
          icon={CheckCircle2}
          variant="lime"
          onClick={() => onNavigate('investigations')}
        />

        <MetricCard
          label="ML Anomalies"
          value={metrics.detected_anomalies}
          sublabel="Isolation Forest"
          icon={Cpu}
          variant="teal"
          onClick={() => onNavigate('threat-detection', { method: 'ISOLATION_FOREST' })}
        />
      </div>

      {/* Charts & Analytics Row */}
      {hasData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Severity Distribution */}
          <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 flex flex-col">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-teal-light/20">
              <span className="text-xs font-mono font-bold text-ivory uppercase tracking-wider">
                Threat Severity Distribution
              </span>
              <span className="text-[10px] font-mono text-sage">SOC ALERTS</span>
            </div>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.severity_distribution || []}>
                  <XAxis dataKey="name" stroke="#91AAA5" fontSize={10} tickLine={false} />
                  <YAxis stroke="#91AAA5" fontSize={10} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#101C1D',
                      borderColor: '#00D5C5',
                      borderRadius: 4,
                      fontSize: 11,
                      fontFamily: 'IBM Plex Mono',
                    }}
                  />
                  <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                    {(data?.severity_distribution || []).map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={SEVERITY_COLORS[entry.name] || '#00D5C5'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Detection Engine Comparison */}
          <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 flex flex-col">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-teal-light/20">
              <span className="text-xs font-mono font-bold text-ivory uppercase tracking-wider">
                Detection Paradigm Split
              </span>
              <span className="text-[10px] font-mono text-sage">HYBRID ENGINE</span>
            </div>
            <div className="h-56 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data?.detection_types || []}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {(data?.detection_types || []).map((entry, index) => (
                      <Cell key={`type-${index}`} fill={TYPE_COLORS[index % TYPE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#101C1D',
                      borderColor: '#00D5C5',
                      borderRadius: 4,
                      fontSize: 11,
                      fontFamily: 'IBM Plex Mono',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center space-x-6 text-[11px] font-mono mt-1">
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-neon" />
                <span className="text-sage">Rule Engine ({metrics.rule_detections})</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-lime-acid" />
                <span className="text-sage">Isolation Forest ({metrics.detected_anomalies})</span>
              </div>
            </div>
          </div>

          {/* Recent Investigations List */}
          <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 flex flex-col">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-teal-light/20">
              <span className="text-xs font-mono font-bold text-ivory uppercase tracking-wider">
                Active & Recent Investigations
              </span>
              <button
                onClick={() => onNavigate('investigations')}
                className="text-[10px] font-mono text-cyan-neon hover:underline flex items-center"
              >
                VIEW ALL <ArrowRight className="w-2.5 h-2.5 ml-1" />
              </button>
            </div>

            <div className="space-y-2 overflow-y-auto flex-1 max-h-56">
              {(data?.recent_investigations || []).length === 0 ? (
                <div className="text-xs font-mono text-sage/70 py-8 text-center">
                  No investigations launched yet.
                </div>
              ) : (
                data?.recent_investigations.map((inv) => (
                  <div
                    key={inv.id}
                    onClick={() => onNavigate('investigations', { investigationId: inv.id })}
                    className="p-2 rounded bg-obsidian/70 border border-teal-light/30 hover:border-cyan-neon/40 cursor-pointer transition-colors flex items-center justify-between"
                  >
                    <div>
                      <div className="font-mono text-xs font-bold text-cyan-neon">
                        {inv.id}
                      </div>
                      <div className="text-[10px] font-mono text-sage">
                        Stage: <span className="text-ivory">{inv.stage}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span
                        className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                          inv.status === 'COMPLETED'
                            ? 'border-lime-acid/40 text-lime-acid bg-lime-acid/10'
                            : 'border-cyan-neon/40 text-cyan-neon bg-cyan-neon/10'
                        }`}
                      >
                        {inv.status} ({inv.progress}%)
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Recent Telemetry Activity Stream */}
      {hasData && (
        <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-teal-light/20">
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-cyan-neon" />
              <span className="text-xs font-mono font-bold text-ivory uppercase tracking-wider">
                Live Telemetry Ingestion Feed
              </span>
            </div>
            <button
              onClick={() => onNavigate('telemetry')}
              className="text-[10px] font-mono text-cyan-neon hover:underline flex items-center"
            >
              EXPLORE FULL TELEMETRY <ArrowRight className="w-2.5 h-2.5 ml-1" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-teal-light/20 text-[10px] text-sage uppercase">
                  <th className="pb-2">Event ID</th>
                  <th className="pb-2">Timestamp</th>
                  <th className="pb-2">Type</th>
                  <th className="pb-2">Severity</th>
                  <th className="pb-2">User / Host</th>
                  <th className="pb-2">Environment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-teal-light/10">
                {(data?.recent_events || []).map((ev) => (
                  <tr key={ev.id} className="hover:bg-teal-brand/10 transition-colors">
                    <td className="py-2 text-cyan-neon font-semibold">{ev.id}</td>
                    <td className="py-2 text-sage/80">{ev.timestamp.substring(0, 19).replace('T', ' ')}</td>
                    <td className="py-2 text-ivory font-medium">{ev.type}</td>
                    <td className="py-2">
                      <SeverityBadge severity={ev.severity} size="sm" />
                    </td>
                    <td className="py-2 text-sage">
                      {ev.user || ev.host || 'N/A'}
                    </td>
                    <td className="py-2">
                      <span
                        className={`text-[9px] px-1.5 py-0.2 rounded border ${
                          ev.is_demo
                            ? 'border-amber-neon/30 text-amber-neon'
                            : 'border-cyan-neon/30 text-cyan-neon'
                        }`}
                      >
                        {ev.is_demo ? 'DEMO' : 'LIVE'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
