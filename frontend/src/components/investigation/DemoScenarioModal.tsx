import React, { useEffect, useState } from 'react';
import {
  Layers,
  ShieldAlert,
  Zap,
  Play,
  ArrowRight,
  Database,
  CheckCircle2,
  X,
  FileCode,
  Flame,
  Radio,
  Activity
} from 'lucide-react';
import { fetchDemoScenarios, loadDemoScenario, createInvestigation } from '../../services/api';
import { DemoScenario } from '../../types';
import { SeverityBadge } from '../common/Badge';

interface DemoScenarioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLaunchInvestigation: (invId: string) => void;
  onGoToTelemetry: () => void;
}

export const DemoScenarioModal: React.FC<DemoScenarioModalProps> = ({
  isOpen,
  onClose,
  onLaunchInvestigation,
  onGoToTelemetry,
}) => {
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingDataset, setLoadingDataset] = useState<boolean>(false);
  const [loadResult, setLoadResult] = useState<any>(null);
  const [resetFirst, setResetFirst] = useState<boolean>(true);

  useEffect(() => {
    if (!isOpen) return;
    async function init() {
      try {
        setLoading(true);
        const list = await fetchDemoScenarios();
        setScenarios(list);
        if (list.length > 0) setSelectedScenario(list[0]);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleLoadOnly = async () => {
    if (!selectedScenario) return;
    try {
      setLoadingDataset(true);
      setLoadResult(null);

      const res = await loadDemoScenario(selectedScenario.id, {
        reset_first: resetFirst,
        freshen_timestamps: true,
      });
      setLoadResult(res);

      // Trigger global synchronization across all open views
      window.dispatchEvent(new CustomEvent('cybersleuth-sync'));
    } catch (err: any) {
      alert('Error loading scenario: ' + (err.message || err));
    } finally {
      setLoadingDataset(false);
    }
  };

  const handleExecuteScenario = async () => {
    if (!selectedScenario) return;
    try {
      setLoadingDataset(true);
      setLoadResult(null);

      // 1. Load dataset into DEMO partition and run detection
      const res = await loadDemoScenario(selectedScenario.id, {
        reset_first: resetFirst,
        freshen_timestamps: true,
      });
      setLoadResult(res);

      // Trigger global synchronization
      window.dispatchEvent(new CustomEvent('cybersleuth-sync'));

      // 2. Automatically launch LangGraph investigation on the primary alert
      const primaryAlertId = res.primary_alert_id || (res.alerts && res.alerts.length > 0 ? res.alerts[0].id : null);
      if (primaryAlertId) {
        const inv = await createInvestigation(primaryAlertId);
        window.dispatchEvent(new CustomEvent('cybersleuth-sync'));
        onClose();
        onLaunchInvestigation(inv.id);
      } else {
        alert('Scenario telemetry loaded into DEMO partition. Run threat detection to explore.');
      }
    } catch (err: any) {
      alert('Error launching scenario: ' + (err.message || err));
    } finally {
      setLoadingDataset(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-obsidian/85 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl rounded-xl bg-charcoal border border-cyan-neon shadow-neon-cyan font-mono text-xs overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-obsidian/90 border-b border-teal-light/40 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded bg-teal-brand text-cyan-neon border border-cyan-neon/40 shadow-neon-cyan">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-heading font-bold text-ivory tracking-wide flex items-center gap-2">
                CYBERSLEUTH DEMO SCENARIO LABORATORY
              </h2>
              <p className="text-[10px] text-sage">
                End-to-End Autonomous Multi-Agent Investigation Sandbox
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-sage hover:text-ivory hover:bg-teal-brand/30 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* First-Run Mode Picker */}
        <div className="p-4 bg-teal-brand/10 border-b border-teal-light/30 flex items-center justify-between">
          <div className="text-sage text-xs font-sans">
            Choose whether to explore synthetic pre-built cyberattacks or ingest your own telemetry:
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                onClose();
                onGoToTelemetry();
              }}
              className="px-3 py-1.5 rounded bg-obsidian border border-teal-light text-sage hover:text-cyan-neon transition-colors"
            >
              USE MY TELEMETRY
            </button>
            <button
              className="px-3 py-1.5 rounded bg-cyan-neon text-obsidian font-bold shadow-neon-cyan"
            >
              EXPLORE DEMO SCENARIOS
            </button>
          </div>
        </div>

        {/* Main Content Split */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-12 gap-6 overflow-y-auto flex-1">
          {/* Left: 4 Scenarios List */}
          <div className="md:col-span-5 space-y-2.5">
            <span className="text-[10px] text-sage uppercase tracking-wider block">
              Pre-Configured Cyberattack Scenarios:
            </span>
            {scenarios.map((sc) => {
              const isSelected = selectedScenario?.id === sc.id;
              return (
                <div
                  key={sc.id}
                  onClick={() => setSelectedScenario(sc)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-teal-brand/30 border-cyan-neon shadow-neon-cyan'
                      : 'bg-obsidian border-teal-light/30 hover:border-teal-light/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-cyan-neon text-xs">{sc.category}</span>
                    <SeverityBadge severity={sc.severity} size="sm" />
                  </div>
                  <h3 className="font-heading font-semibold text-sm text-ivory mb-1">
                    {sc.title}
                  </h3>
                  <div className="text-[10px] text-sage font-sans line-clamp-2">
                    {sc.description}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right: Selected Scenario Preview & Launch Details */}
          {selectedScenario && (
            <div className="md:col-span-7 p-5 rounded-lg bg-obsidian border border-teal-light/40 space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-teal-light/30">
                  <div className="text-base font-heading font-bold text-ivory">
                    {selectedScenario.title}
                  </div>
                  <SeverityBadge severity={selectedScenario.severity} />
                </div>

                <p className="text-xs text-sage font-sans leading-relaxed">
                  {selectedScenario.description}
                </p>

                {/* MITRE ATT&CK Targets */}
                <div>
                  <span className="text-[10px] text-sage uppercase block mb-1.5">
                    Targeted MITRE ATT&CK Techniques:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedScenario.mitre_techniques.map((tech, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-teal-brand/30 border border-teal-light text-cyan-neon text-[10px]"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Telemetry Preview */}
                <div>
                  <span className="text-[10px] text-sage uppercase block mb-1.5">
                    Synthetic Telemetry Sample ({selectedScenario.preview_events?.length || 0} Events Previewed):
                  </span>
                  <div className="p-3 rounded bg-charcoal border border-teal-light/30 text-[10px] font-mono text-lime-acid/90 space-y-1 max-h-36 overflow-y-auto">
                    {(selectedScenario.preview_events || []).map((ev: any, idx: number) => (
                      <div key={idx} className="truncate">
                        [{ev.event_id}] {ev.timestamp} | {ev.event_type} | {ev.user || ev.host || 'N/A'} {ev.command_line ? `| ${ev.command_line}` : ''}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Result Feedback Banner if Loaded to Dashboard */}
                {loadResult && (
                  <div className="p-3 rounded-lg bg-teal-brand/40 border border-cyan-neon space-y-1.5 animate-fadeIn">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-1.5 text-cyan-neon font-bold text-xs">
                        <CheckCircle2 className="w-4 h-4 text-cyan-neon" />
                        <span>Scenario Ingested & Dashboard Synchronized!</span>
                      </div>
                      <span className="text-[10px] text-sage">Partition: DEMO</span>
                    </div>
                    <div className="text-[11px] text-ivory">
                      Ingested <strong>{loadResult.events_ingested}</strong> events • Triggered <strong>{loadResult.rule_alerts_generated}</strong> rule alerts & <strong>{loadResult.ml_anomalies_detected}</strong> ML anomalies.
                    </div>
                    <div className="text-[10px] text-cyan-neon/80 truncate">
                      Primary Alert: <strong>{loadResult.primary_alert_title}</strong>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Controls & Isolation Toggle */}
              <div className="pt-4 border-t border-teal-light/30 space-y-3">
                <div className="flex items-center justify-between">
                  <label className="flex items-center space-x-2 text-sage text-[11px] cursor-pointer hover:text-ivory transition-colors">
                    <input
                      type="checkbox"
                      checked={resetFirst}
                      onChange={(e) => setResetFirst(e.target.checked)}
                      className="accent-cyan-neon rounded"
                    />
                    <span>Clean Scenario Isolation (Reset prior demo records before loading)</span>
                  </label>
                </div>

                <div className="flex items-center justify-end space-x-3">
                  <button
                    onClick={handleLoadOnly}
                    disabled={loadingDataset}
                    className="flex items-center space-x-1.5 px-3.5 py-2 rounded bg-charcoal border border-teal-light hover:border-cyan-neon text-ivory hover:text-cyan-neon text-xs font-mono transition-colors"
                    title="Ingests scenario telemetry, updates Command Center dashboard, and remains on current view"
                  >
                    <Database className="w-3.5 h-3.5" />
                    <span>{loadingDataset ? 'SYNCING...' : 'LOAD TO DASHBOARD ONLY'}</span>
                  </button>

                  <button
                    onClick={handleExecuteScenario}
                    disabled={loadingDataset}
                    className="flex items-center space-x-2 px-5 py-2 rounded bg-cyan-neon text-obsidian font-bold text-xs hover:bg-cyan-neon/90 shadow-neon-cyan transition-all"
                    title="Ingests scenario telemetry, launches autonomous LangGraph investigation, and opens workflow graph"
                  >
                    <Play className={`w-3.5 h-3.5 ${loadingDataset ? 'animate-spin' : ''}`} />
                    <span>
                      {loadingDataset
                        ? 'ORCHESTRATING...'
                        : 'LOAD & LAUNCH INVESTIGATION'}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
