import React, { useEffect, useState } from 'react';
import {
  Workflow,
  Search,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Brain,
  Shield,
  Network,
  FileText,
  ArrowRight,
  Layers,
  RotateCw,
  Zap,
  Terminal,
  Activity
} from 'lucide-react';
import { fetchInvestigations, fetchInvestigationById } from '../services/api';
import { Investigation, InvestigationStep } from '../types';
import { SeverityBadge, ProvenanceBadge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';

interface InvestigationsProps {
  onNavigate: (tab: string, state?: any) => void;
  targetInvestigationId?: string | null;
}

export const Investigations: React.FC<InvestigationsProps> = ({
  onNavigate,
  targetInvestigationId,
}) => {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [selectedInv, setSelectedInv] = useState<Investigation | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'findings' | 'hypotheses' | 'timeline' | 'mitre' | 'steps'>('findings');

  const STAGES = [
    { key: 'alert_intake', label: '1. Alert Intake' },
    { key: 'investigation_planning', label: '2. Planning' },
    { key: 'evidence_collection', label: '3. Evidence Collection' },
    { key: 'correlation_and_validation', label: '4. Correlation' },
    { key: 'evidence_sufficiency_assessment', label: '5. Sufficiency Loop' },
    { key: 'attack_reconstruction', label: '6. Attack Reconstruction' },
    { key: 'mitre_mapping', label: '7. MITRE Mapping' },
    { key: 'risk_assessment', label: '8. Risk Assessment' },
    { key: 'investigation_closure', label: '9. Response Staging & Closure' },
  ];

  const loadInvestigations = async () => {
    try {
      setLoading(true);
      const list = await fetchInvestigations();
      setInvestigations(list);

      if (targetInvestigationId) {
        const found = list.find((i) => i.id === targetInvestigationId);
        if (found) setSelectedInv(found);
        else if (list.length > 0) setSelectedInv(list[0]);
      } else if (list.length > 0 && !selectedInv) {
        setSelectedInv(list[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvestigations();
    const handleSync = () => loadInvestigations();
    window.addEventListener('cybersleuth-sync', handleSync);
    return () => {
      window.removeEventListener('cybersleuth-sync', handleSync);
    };
  }, [targetInvestigationId]);

  // Polling if active investigation is running
  useEffect(() => {
    if (!selectedInv || selectedInv.status === 'COMPLETED' || selectedInv.status === 'CLOSED') {
      return;
    }
    const interval = setInterval(async () => {
      try {
        const updated = await fetchInvestigationById(selectedInv.id);
        setSelectedInv(updated);
        if (updated.status === 'COMPLETED') {
          loadInvestigations();
        }
      } catch (err) {
        console.error(err);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [selectedInv?.id, selectedInv?.status]);

  if (loading && investigations.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center font-mono text-cyan-neon text-sm">
        <Activity className="w-5 h-5 mr-2 animate-spin" />
        LOADING LANGGRAPH INVESTIGATIONS...
      </div>
    );
  }

  if (investigations.length === 0 && !loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <EmptyState
          icon={Search}
          title="No Active Investigations"
          description="Investigations are automatically orchestrated via the LangGraph StateGraph engine when an alert is triaged. Head to Threat Detection to launch an investigation, or load a demo scenario."
          actionLabel="GO TO THREAT DETECTION"
          onAction={() => onNavigate('threat-detection')}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-teal-light/40 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Workflow className="w-5 h-5 text-cyan-neon" />
            <h1 className="text-xl md:text-2xl font-bold font-heading tracking-tight text-ivory">
              LANGGRAPH INVESTIGATION ENGINE
            </h1>
          </div>
          <p className="text-xs font-mono text-sage mt-1">
            Stateful Multi-Agent Forensic Workflow Orchestration & Hypothesis Validation
          </p>
        </div>

        {/* Quick switcher */}
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-sage">INVESTIGATION:</span>
          <select
            value={selectedInv?.id || ''}
            onChange={(e) => {
              const inv = investigations.find((i) => i.id === e.target.value);
              if (inv) setSelectedInv(inv);
            }}
            className="bg-charcoal border border-cyan-neon/40 rounded px-2.5 py-1.5 font-mono text-xs text-cyan-neon focus:outline-none"
          >
            {investigations.map((i) => (
              <option key={i.id} value={i.id}>
                {i.id} ({i.status}) - Alert {i.alert_id}
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedInv && (
        <div className="space-y-6">
          {/* Top Banner: Status, Provider & Actions */}
          <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 font-mono">
                <span className="text-sm font-bold text-cyan-neon">{selectedInv.id}</span>
                <span className="text-xs text-sage">Triggered by:</span>
                <span className="text-xs font-bold text-ivory">{selectedInv.alert_id}</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                    selectedInv.status === 'COMPLETED'
                      ? 'border-lime-acid/40 text-lime-acid bg-lime-acid/10'
                      : 'border-cyan-neon/40 text-cyan-neon bg-cyan-neon/10'
                  }`}
                >
                  {selectedInv.status}
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded border border-teal-light text-sage">
                  {selectedInv.is_demo ? 'DEMO' : 'LIVE'}
                </span>
              </div>
              <div className="text-xs text-sage font-mono flex items-center space-x-3">
                <span>Iterations: {selectedInv.iteration_count}</span>
                <span>•</span>
                <span className="flex items-center space-x-1">
                  <Brain className="w-3.5 h-3.5 text-cyan-neon" />
                  <span>Provider:</span>
                  <span
                    className={`font-bold ${
                      selectedInv.degraded_mode ? 'text-amber-neon' : 'text-cyan-neon'
                    }`}
                  >
                    {selectedInv.degraded_mode
                      ? 'DETERMINISTIC FALLBACK (DEGRADED)'
                      : selectedInv.llm_provider || 'LIVE LLM'}
                  </span>
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2.5">
              <button
                onClick={() => onNavigate('evidence-explorer', { investigationId: selectedInv.id })}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-teal-brand border border-cyan-neon/40 text-cyan-neon font-mono text-xs hover:bg-teal-light transition-colors shadow-neon-cyan"
              >
                <Network className="w-3.5 h-3.5" />
                <span>EXPLORE EVIDENCE GRAPH</span>
              </button>

              <button
                onClick={() => onNavigate('response-center', { investigationId: selectedInv.id })}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-lime-acid/15 border border-lime-acid/40 text-lime-acid font-mono text-xs hover:bg-lime-acid/25 transition-colors"
              >
                <Shield className="w-3.5 h-3.5" />
                <span>RESPONSE ACTIONS</span>
              </button>

              <button
                onClick={() => onNavigate('reports', { investigationId: selectedInv.id })}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-obsidian border border-teal-light text-ivory font-mono text-xs hover:border-cyan-neon transition-colors"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>GENERATE PDF</span>
              </button>
            </div>
          </div>

          {/* LangGraph Visual Workflow Pipeline */}
          <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-ivory uppercase tracking-wider flex items-center space-x-2">
                <Workflow className="w-4 h-4 text-cyan-neon" />
                <span>LangGraph StateGraph Execution Pipeline</span>
              </span>
              <span className="text-xs font-mono text-cyan-neon font-bold">
                {selectedInv.progress}% COMPLETE
              </span>
            </div>

            {/* Pipeline Step Nodes */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-9 gap-2">
              {STAGES.map((stg, idx) => {
                const isCurrent = selectedInv.current_stage === stg.key;
                const isFinished = selectedInv.progress === 100 || idx < 8; // Past or completed

                return (
                  <div
                    key={stg.key}
                    className={`p-2 rounded border text-center font-mono text-[10px] transition-all relative ${
                      isCurrent
                        ? 'border-cyan-neon bg-cyan-neon/15 text-cyan-neon shadow-neon-cyan font-bold animate-pulse'
                        : isFinished
                        ? 'border-lime-acid/40 bg-lime-acid/5 text-lime-acid'
                        : 'border-teal-light/30 bg-obsidian/40 text-sage/60'
                    }`}
                  >
                    <div className="truncate">{stg.label}</div>
                    <div className="text-[9px] mt-0.5 opacity-80">
                      {isCurrent ? 'ACTIVE' : isFinished ? 'DONE' : 'PENDING'}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Sufficiency Assessment Alert if iterative loop triggered */}
            {selectedInv.iteration_count > 1 && (
              <div className="p-2.5 rounded bg-cyan-neon/5 border border-cyan-neon/30 text-xs font-mono text-cyan-neon flex items-center space-x-2">
                <RotateCw className="w-4 h-4 shrink-0" />
                <span>
                  Multi-Agent Iteration Loop: Initial evidence sufficiency check detected missing telemetry gaps. StateGraph triggered Refined Evidence Collection (Iteration {selectedInv.iteration_count} of 2).
                </span>
              </div>
            )}
          </div>

          {/* Executive Summary */}
          {selectedInv.executive_summary && (
            <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40">
              <h3 className="text-xs font-mono font-bold text-sage uppercase tracking-wider mb-1.5 flex items-center space-x-1.5">
                <Terminal className="w-3.5 h-3.5 text-cyan-neon" />
                <span>Executive Forensic Brief</span>
              </h3>
              <p className="text-sm font-sans text-ivory leading-relaxed">
                {selectedInv.executive_summary}
              </p>
            </div>
          )}

          {/* Detail Tabs Bar */}
          <div className="border-b border-teal-light/30 flex space-x-2 font-mono text-xs">
            <button
              onClick={() => setActiveTab('findings')}
              className={`pb-2 px-3 border-b-2 font-semibold transition-colors ${
                activeTab === 'findings'
                  ? 'border-cyan-neon text-cyan-neon'
                  : 'border-transparent text-sage hover:text-ivory'
              }`}
            >
              STRUCTURED FINDINGS ({selectedInv.findings?.length || 0})
            </button>

            <button
              onClick={() => setActiveTab('hypotheses')}
              className={`pb-2 px-3 border-b-2 font-semibold transition-colors ${
                activeTab === 'hypotheses'
                  ? 'border-cyan-neon text-cyan-neon'
                  : 'border-transparent text-sage hover:text-ivory'
              }`}
            >
              HYPOTHESES ({selectedInv.hypotheses?.length || 0})
            </button>

            <button
              onClick={() => setActiveTab('timeline')}
              className={`pb-2 px-3 border-b-2 font-semibold transition-colors ${
                activeTab === 'timeline'
                  ? 'border-cyan-neon text-cyan-neon'
                  : 'border-transparent text-sage hover:text-ivory'
              }`}
            >
              ATTACK RECONSTRUCTION
            </button>

            <button
              onClick={() => setActiveTab('mitre')}
              className={`pb-2 px-3 border-b-2 font-semibold transition-colors ${
                activeTab === 'mitre'
                  ? 'border-cyan-neon text-cyan-neon'
                  : 'border-transparent text-sage hover:text-ivory'
              }`}
            >
              MITRE ATT&CK ({selectedInv.mitre_mappings?.length || 0})
            </button>

            <button
              onClick={() => setActiveTab('steps')}
              className={`pb-2 px-3 border-b-2 font-semibold transition-colors ${
                activeTab === 'steps'
                  ? 'border-cyan-neon text-cyan-neon'
                  : 'border-transparent text-sage hover:text-ivory'
              }`}
            >
              EXECUTION LOGS ({selectedInv.steps?.length || 0})
            </button>
          </div>

          {/* TAB 1: Structured Findings (OBSERVED vs INFERRED) */}
          {activeTab === 'findings' && (
            <div className="space-y-3">
              {(selectedInv.findings || []).map((fnd) => (
                <div
                  key={fnd.id}
                  className="p-4 rounded-lg bg-charcoal border border-teal-light/30 space-y-2 font-mono text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-cyan-neon">{fnd.id}</span>
                      <ProvenanceBadge category={fnd.status} confidence={fnd.confidence} />
                    </div>
                    <div className="text-[11px] text-sage">
                      Supporting Events:{' '}
                      <span className="text-ivory font-bold">
                        {fnd.supporting_events?.join(', ') || 'Direct Telemetry'}
                      </span>
                    </div>
                  </div>

                  <p className="text-sm font-sans text-ivory">{fnd.statement}</p>

                  <div className="text-[11px] text-sage/90 pt-1 border-t border-teal-light/20">
                    <span className="text-cyan-neon uppercase font-bold text-[10px] mr-1">RATIONALE:</span>
                    {fnd.rationale}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 2: Hypotheses */}
          {activeTab === 'hypotheses' && (
            <div className="space-y-3">
              {(selectedInv.hypotheses || []).map((hyp) => (
                <div
                  key={hyp.id}
                  className="p-4 rounded-lg bg-charcoal border border-teal-light/30 space-y-2 font-mono text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-cyan-neon">{hyp.id}</span>
                      <span
                        className={`text-[9px] px-1.5 py-0.5 rounded border ${
                          hyp.supported
                            ? 'border-lime-acid/50 text-lime-acid bg-lime-acid/10'
                            : 'border-sage/40 text-sage bg-sage/10'
                        }`}
                      >
                        {hyp.supported ? 'SUPPORTED BY EVIDENCE' : 'TESTED / UNCONFIRMED'}
                      </span>
                    </div>
                    <span className="text-[10px] text-sage">
                      PRIOR LIKELIHOOD: <span className="text-ivory font-bold">{hyp.likelihood}</span>
                    </span>
                  </div>
                  <p className="text-sm font-sans text-ivory">{hyp.hypothesis}</p>
                </div>
              ))}
            </div>
          )}

          {/* TAB 3: Attack Reconstruction */}
          {activeTab === 'timeline' && (
            <div className="p-5 rounded-lg bg-charcoal border border-teal-light/40 space-y-4">
              <h4 className="text-xs font-mono font-bold text-cyan-neon uppercase tracking-wider">
                Forensic Sequence & Progression Lineage
              </h4>
              <div className="p-4 rounded bg-obsidian/70 border border-teal-light/30 text-xs font-mono text-ivory whitespace-pre-wrap leading-relaxed">
                {selectedInv.attack_reconstruction?.narrative || 'Attack narrative synthesized from correlated events.'}
              </div>

              {selectedInv.risk_assessment && (
                <div className="p-4 rounded bg-teal-brand/20 border border-teal-light/40 space-y-2 text-xs font-mono">
                  <div className="text-cyan-neon font-bold uppercase text-[11px]">
                    Risk Assessment & Blast Radius Evaluation
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                    <div>
                      <span className="text-sage block text-[10px]">SEVERITY:</span>
                      <span className="text-ivory font-bold">{selectedInv.risk_assessment.overall_severity}</span>
                    </div>
                    <div>
                      <span className="text-sage block text-[10px]">IMPACT SCORE:</span>
                      <span className="text-coral-neon font-bold">{selectedInv.risk_assessment.impact_score} / 10</span>
                    </div>
                    <div>
                      <span className="text-sage block text-[10px]">BLAST RADIUS:</span>
                      <span className="text-ivory font-bold">{selectedInv.risk_assessment.blast_radius}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: MITRE ATT&CK */}
          {activeTab === 'mitre' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(selectedInv.mitre_mappings || []).map((m, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-lg bg-charcoal border border-teal-light/30 space-y-2 font-mono text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-cyan-neon font-bold text-sm">{m.technique_id}</span>
                    <span className="text-[10px] text-sage uppercase px-1.5 py-0.5 rounded border border-teal-light">
                      {m.tactic}
                    </span>
                  </div>
                  <div className="text-sm font-heading font-semibold text-ivory">{m.name}</div>
                  <p className="text-xs font-sans text-sage">{m.explanation}</p>
                  <div className="text-[10px] text-sage/80 pt-2 border-t border-teal-light/20">
                    Citations: <span className="text-cyan-neon">{m.supporting_events?.join(', ')}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 5: Steps */}
          {activeTab === 'steps' && (
            <div className="space-y-2">
              {(selectedInv.steps || []).map((stp) => (
                <div
                  key={stp.id}
                  className="p-3 rounded bg-obsidian/70 border border-teal-light/30 flex items-start justify-between font-mono text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-cyan-neon font-bold">[{stp.step_order}] {stp.stage_name}</span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-lime-acid/10 text-lime-acid border border-lime-acid/30">
                        {stp.status}
                      </span>
                    </div>
                    <div className="text-ivory text-xs font-sans">{stp.output_summary}</div>
                  </div>
                  <div className="text-[10px] text-sage/70 shrink-0 ml-4">
                    {stp.timestamp?.substring(11, 19)} UTC
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
