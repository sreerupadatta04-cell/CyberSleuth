import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  Cpu,
  Search,
  Filter,
  Play,
  Info,
  CheckCircle2,
  Clock,
  ArrowRight,
  Terminal,
  Zap
} from 'lucide-react';
import { fetchAlerts, triggerDetectionRun, createInvestigation } from '../services/api';
import { Alert } from '../types';
import { SeverityBadge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';

interface ThreatDetectionProps {
  onNavigate: (tab: string, state?: any) => void;
  initialFilter?: { severity?: string; method?: string };
}

export const ThreatDetection: React.FC<ThreatDetectionProps> = ({ onNavigate, initialFilter }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [invoking, setInvoking] = useState<boolean>(false);
  
  const [methodFilter, setMethodFilter] = useState<string>(initialFilter?.method || 'ALL');
  const [severityFilter, setSeverityFilter] = useState<string>(initialFilter?.severity || 'ALL');
  const [envFilter, setEnvFilter] = useState<string>('ALL'); // ALL, DEMO, LIVE

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (methodFilter !== 'ALL') params.detection_method = methodFilter;
      if (severityFilter !== 'ALL') params.severity = severityFilter;
      if (envFilter === 'DEMO') params.is_demo = true;
      if (envFilter === 'LIVE') params.is_demo = false;

      const res = await fetchAlerts(params);
      setAlerts(res);
      if (res.length > 0 && !selectedAlert) {
        setSelectedAlert(res[0]);
      } else if (res.length === 0) {
        setSelectedAlert(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [methodFilter, severityFilter, envFilter]);

  const handleRunDetection = async () => {
    try {
      setAnalyzing(true);
      await triggerDetectionRun(true);
      await triggerDetectionRun(false);
      await loadAlerts();
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleStartInvestigation = async (alertId: string) => {
    try {
      setInvoking(true);
      const inv = await createInvestigation(alertId);
      onNavigate('investigations', { investigationId: inv.id });
    } catch (err) {
      console.error(err);
      alert('Failed to launch LangGraph investigation: ' + err);
    } finally {
      setInvoking(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-teal-light/40 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-cyan-neon" />
            <h1 className="text-xl md:text-2xl font-bold font-heading tracking-tight text-ivory">
              THREAT DETECTION & ANOMALY SURVEILLANCE
            </h1>
          </div>
          <p className="text-xs font-mono text-sage mt-1">
            Deterministic Rule-Based Correlation + Scikit-Learn Isolation Forest Engine
          </p>
        </div>

        <button
          onClick={handleRunDetection}
          disabled={analyzing}
          className="flex items-center space-x-1.5 px-4 py-2 rounded bg-teal-brand border border-cyan-neon/40 hover:bg-teal-light text-xs font-mono font-bold text-cyan-neon shadow-neon-cyan transition-colors"
        >
          <Play className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
          <span>{analyzing ? 'SCANNING TELEMETRY...' : 'EXECUTE HYBRID DETECTION'}</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between p-3 rounded-lg bg-charcoal border border-teal-light/30 gap-3 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-1.5 text-sage">
            <Filter className="w-3.5 h-3.5" />
            <span>METHOD:</span>
            <select
              value={methodFilter}
              onChange={(e) => setMethodFilter(e.target.value)}
              className="bg-obsidian border border-teal-light/40 rounded px-2 py-1 text-ivory focus:outline-none focus:border-cyan-neon"
            >
              <option value="ALL">All Methods</option>
              <option value="RULE_BASED">Rule-Based Engine</option>
              <option value="ISOLATION_FOREST">Isolation Forest (ML)</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 text-sage">
            <span>SEVERITY:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-obsidian border border-teal-light/40 rounded px-2 py-1 text-ivory focus:outline-none focus:border-cyan-neon"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 text-sage">
            <span>DATASET:</span>
            <select
              value={envFilter}
              onChange={(e) => setEnvFilter(e.target.value)}
              className="bg-obsidian border border-teal-light/40 rounded px-2 py-1 text-ivory focus:outline-none focus:border-cyan-neon"
            >
              <option value="ALL">All Partitions</option>
              <option value="DEMO">Demo Only</option>
              <option value="LIVE">Live Only</option>
            </select>
          </div>
        </div>

        <div className="text-sage text-[11px]">
          Showing <span className="text-cyan-neon font-bold">{alerts.length}</span> detected alert signatures
        </div>
      </div>

      {alerts.length === 0 && !loading && (
        <EmptyState
          icon={ShieldAlert}
          title="No Threat Signatures Detected"
          description="Either telemetry has not yet been ingested, or current events do not breach detection thresholds. Ingest telemetry or run hybrid detection to scan."
          actionLabel="RUN DETECTION ENGINE"
          onAction={handleRunDetection}
        />
      )}

      {/* Main Split View: Alerts List on Left, Detail on Right */}
      {alerts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Alerts List */}
          <div className="lg:col-span-5 space-y-2.5 max-h-[720px] overflow-y-auto pr-1">
            {alerts.map((alt) => {
              const isSelected = selectedAlert?.id === alt.id;
              const isML = alt.detection_method === 'ISOLATION_FOREST';

              return (
                <div
                  key={alt.id}
                  onClick={() => setSelectedAlert(alt)}
                  className={`p-3.5 rounded-lg border transition-all cursor-pointer relative ${
                    isSelected
                      ? 'bg-teal-brand/30 border-cyan-neon shadow-neon-cyan'
                      : 'bg-charcoal border-teal-light/30 hover:border-teal-light/70'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-xs font-bold text-cyan-neon">
                      {alt.id}
                    </span>
                    <div className="flex items-center space-x-1.5">
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase ${
                          isML
                            ? 'border-lime-acid/50 text-lime-acid bg-lime-acid/10'
                            : 'border-cyan-neon/50 text-cyan-neon bg-cyan-neon/10'
                        }`}
                      >
                        {isML ? 'ISOLATION FOREST' : 'RULE ENGINE'}
                      </span>
                      <SeverityBadge severity={alt.severity} size="sm" />
                    </div>
                  </div>

                  <h3 className="font-heading font-semibold text-sm text-ivory line-clamp-1 mb-1">
                    {alt.title}
                  </h3>

                  <p className="text-xs text-sage line-clamp-2 mb-2 font-sans">
                    {alt.description}
                  </p>

                  <div className="flex items-center justify-between text-[10px] font-mono text-sage/70 pt-2 border-t border-teal-light/20">
                    <span>
                      Primary: <code className="text-ivory">{alt.primary_event_id || 'N/A'}</code>
                    </span>
                    {isML && alt.anomaly_score !== undefined && (
                      <span className="text-lime-acid font-bold">
                        Score: {alt.anomaly_score}
                      </span>
                    )}
                    <span>{alt.is_demo ? 'DEMO' : 'LIVE'}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Alert Detail Inspection Panel */}
          {selectedAlert && (
            <div className="lg:col-span-7 p-6 rounded-lg bg-charcoal border border-cyan-neon/30 flex flex-col space-y-4">
              {/* Detail Header */}
              <div className="flex items-start justify-between pb-3 border-b border-teal-light/30">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-mono text-xs text-cyan-neon font-bold">
                      {selectedAlert.id}
                    </span>
                    <SeverityBadge severity={selectedAlert.severity} />
                    <span className="text-xs font-mono text-sage">
                      [{selectedAlert.detection_method}]
                    </span>
                  </div>
                  <h2 className="text-lg font-heading font-bold text-ivory">
                    {selectedAlert.title}
                  </h2>
                </div>

                {/* Primary Action Button */}
                <button
                  onClick={() => handleStartInvestigation(selectedAlert.id)}
                  disabled={invoking}
                  className="flex items-center space-x-1.5 px-4 py-2 rounded bg-cyan-neon text-obsidian font-mono text-xs font-bold hover:bg-cyan-neon/90 shadow-neon-cyan transition-all"
                >
                  <Zap className={`w-3.5 h-3.5 ${invoking ? 'animate-spin' : ''}`} />
                  <span>{invoking ? 'LAUNCHING...' : 'INVESTIGATE WITH LANGGRAPH'}</span>
                </button>
              </div>

              {/* Technical Metadata Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 p-3 rounded bg-obsidian/70 border border-teal-light/30 font-mono text-xs">
                <div>
                  <div className="text-[10px] text-sage uppercase">Trigger Rule</div>
                  <div className="text-ivory font-bold truncate">
                    {selectedAlert.rule_name || 'N/A (Unsupervised)'}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-sage uppercase">Anomaly Score</div>
                  <div className="text-lime-acid font-bold">
                    {selectedAlert.anomaly_score !== null && selectedAlert.anomaly_score !== undefined
                      ? selectedAlert.anomaly_score
                      : 'N/A (Rule Match)'}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-sage uppercase">Supporting Event</div>
                  <div className="text-cyan-neon font-bold">
                    {selectedAlert.primary_event_id || 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-sage uppercase">Investigation</div>
                  <div className="text-ivory font-bold">
                    {selectedAlert.investigation_id ? (
                      <span className="text-cyan-neon cursor-pointer hover:underline" onClick={() => onNavigate('investigations', { investigationId: selectedAlert.investigation_id })}>
                        {selectedAlert.investigation_id}
                      </span>
                    ) : (
                      'NOT STARTED'
                    )}
                  </div>
                </div>
              </div>

              {/* Forensic Explanation */}
              <div>
                <h4 className="text-xs font-mono font-bold text-sage uppercase tracking-wider mb-1 flex items-center">
                  <Info className="w-3.5 h-3.5 mr-1 text-cyan-neon" />
                  Technical Explanation
                </h4>
                <div className="p-3 rounded bg-obsidian/50 border border-teal-light/30 text-xs text-ivory font-sans leading-relaxed">
                  {selectedAlert.explanation || selectedAlert.description}
                </div>
              </div>

              {/* Affected Entities */}
              {selectedAlert.affected_entities && selectedAlert.affected_entities.length > 0 && (
                <div>
                  <h4 className="text-xs font-mono font-bold text-sage uppercase tracking-wider mb-2">
                    Target Entities Involved
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedAlert.affected_entities.map((ent, idx) => (
                      <div
                        key={idx}
                        className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-teal-brand/40 border border-teal-light text-xs font-mono"
                      >
                        <span className="text-sage uppercase text-[10px]">{ent.type}:</span>
                        <span className="text-cyan-neon font-semibold">{ent.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Unsupervised Anomaly Disclaimer if Isolation Forest */}
              {selectedAlert.detection_method === 'ISOLATION_FOREST' && (
                <div className="p-3 rounded bg-lime-acid/5 border border-lime-acid/30 text-[11px] font-mono text-lime-acid flex items-start space-x-2">
                  <Cpu className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">ISOLATION FOREST ML NOTICE:</span> Statistical outlierness indicates that this event deviates from baseline feature patterns (e.g. port, payload entropy, execution time). Statistically anomalous behavior is not automatically malicious and requires multi-agent LangGraph correlation to verify.
                  </div>
                </div>
              )}

              {/* Action Banner */}
              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => handleStartInvestigation(selectedAlert.id)}
                  disabled={invoking}
                  className="flex items-center space-x-2 px-5 py-2.5 rounded bg-teal-brand border border-cyan-neon/40 text-cyan-neon font-mono text-xs font-bold hover:bg-cyan-neon hover:text-obsidian shadow-neon-cyan transition-all"
                >
                  <span>PROCEED TO AUTONOMOUS INVESTIGATION</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
