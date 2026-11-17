import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  Terminal,
  AlertTriangle,
  UserCheck,
  Play,
  RotateCcw,
  Activity,
  Layers
} from 'lucide-react';
import {
  fetchResponseActions,
  approveAction,
  rejectAction,
  fetchInvestigations
} from '../services/api';
import { ResponseAction, Investigation } from '../types';
import { EmptyState } from '../components/common/EmptyState';

interface ResponseCenterProps {
  initialInvestigationId?: string | null;
}

export const ResponseCenter: React.FC<ResponseCenterProps> = ({ initialInvestigationId }) => {
  const [actions, setActions] = useState<ResponseAction[]>([]);
  const [selectedAction, setSelectedAction] = useState<ResponseAction | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  
  // Human approval modal state
  const [showApprovalModal, setShowApprovalModal] = useState<boolean>(false);
  const [analystName, setAnalystName] = useState<string>('soc_lead_analyst');
  const [decisionComments, setDecisionComments] = useState<string>('Authorized simulated containment after multi-agent correlation review.');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isRejectMode, setIsRejectMode] = useState<boolean>(false);

  const loadActions = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (initialInvestigationId) params.investigation_id = initialInvestigationId;
      if (statusFilter !== 'ALL') params.status = statusFilter;

      const data = await fetchResponseActions(params);
      setActions(data);
      if (data.length > 0 && !selectedAction) {
        setSelectedAction(data[0]);
      } else if (data.length === 0) {
        setSelectedAction(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActions();
  }, [initialInvestigationId, statusFilter]);

  const handleOpenApprove = (action: ResponseAction) => {
    setSelectedAction(action);
    setIsRejectMode(false);
    setShowApprovalModal(true);
  };

  const handleOpenReject = (action: ResponseAction) => {
    setSelectedAction(action);
    setIsRejectMode(true);
    setShowApprovalModal(true);
  };

  const handleSubmitDecision = async () => {
    if (!selectedAction) return;
    try {
      setIsSubmitting(true);
      if (isRejectMode) {
        await rejectAction(selectedAction.id, analystName, decisionComments);
      } else {
        await approveAction(selectedAction.id, analystName, decisionComments);
      }
      setShowApprovalModal(false);
      await loadActions();
    } catch (err) {
      console.error(err);
      alert('Failed to process response decision: ' + err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'EXECUTED':
      case 'APPROVED':
        return (
          <span className="font-mono text-[9px] font-bold px-2 py-0.5 rounded border border-lime-acid/50 bg-lime-acid/15 text-lime-acid">
            ✓ {status} (SIMULATED)
          </span>
        );
      case 'REJECTED':
        return (
          <span className="font-mono text-[9px] font-bold px-2 py-0.5 rounded border border-coral-neon/50 bg-coral-neon/15 text-coral-neon">
            ✗ REJECTED
          </span>
        );
      case 'PENDING_APPROVAL':
        return (
          <span className="font-mono text-[9px] font-bold px-2 py-0.5 rounded border border-amber-neon/50 bg-amber-neon/15 text-amber-neon animate-pulse">
            ⏱ PENDING APPROVAL
          </span>
        );
      default:
        return (
          <span className="font-mono text-[9px] px-2 py-0.5 rounded border border-teal-light text-sage">
            {status}
          </span>
        );
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
              INCIDENT RESPONSE CENTER
            </h1>
          </div>
          <p className="text-xs font-mono text-sage mt-1">
            Human-in-the-Loop Incident Response Authorization • Guardrailed Virtual Containment
          </p>
        </div>

        {/* Status Filter */}
        <div className="flex items-center space-x-2 font-mono text-xs">
          <span className="text-sage">STATUS:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-charcoal border border-cyan-neon/40 rounded px-2.5 py-1 text-cyan-neon focus:outline-none"
          >
            <option value="ALL">All Actions</option>
            <option value="PENDING_APPROVAL">Pending Approval</option>
            <option value="EXECUTED">Executed</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Safety Policy Notice */}
      <div className="p-3.5 rounded-lg bg-teal-brand/20 border border-cyan-neon/30 text-xs font-mono text-ivory flex items-start space-x-2.5">
        <AlertTriangle className="w-4 h-4 text-cyan-neon shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-cyan-neon">HUMAN-IN-THE-LOOP SAFETY MANDATE:</span> Autonomous containment execution is prohibited. All actions recommended by multi-agent investigation (Isolate Host, Reset Credentials, Block IP) require explicit human authorization before virtual dispatch. All actions are simulated safely.
        </div>
      </div>

      {actions.length === 0 && !loading && (
        <EmptyState
          icon={CheckCircle2}
          title="No Response Actions Staged"
          description="Response recommendations are automatically synthesized and staged when a LangGraph investigation concludes. Launch an investigation to generate containment actions."
        />
      )}

      {/* Main Split Grid */}
      {actions.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Actions List */}
          <div className="lg:col-span-5 space-y-2.5 max-h-[640px] overflow-y-auto pr-1">
            {actions.map((act) => {
              const isSelected = selectedAction?.id === act.id;

              return (
                <div
                  key={act.id}
                  onClick={() => setSelectedAction(act)}
                  className={`p-4 rounded-lg border transition-all cursor-pointer relative ${
                    isSelected
                      ? 'bg-teal-brand/30 border-cyan-neon shadow-neon-cyan'
                      : 'bg-charcoal border-teal-light/30 hover:border-teal-light/70'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-xs font-bold text-cyan-neon">
                      {act.id}
                    </span>
                    {getStatusBadge(act.status)}
                  </div>

                  <div className="font-heading font-semibold text-sm text-ivory mb-1">
                    {act.action_type}
                  </div>

                  <div className="text-xs font-mono text-sage mb-2">
                    Target: <span className="text-ivory font-bold">{act.target_entity}</span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] font-mono text-sage/70 pt-2 border-t border-teal-light/20">
                    <span>Inv: {act.investigation_id}</span>
                    <span>{act.is_demo ? 'DEMO' : 'LIVE'}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action Details & Execution Log Drawer */}
          {selectedAction && (
            <div className="lg:col-span-7 p-6 rounded-lg bg-charcoal border border-cyan-neon/30 flex flex-col space-y-4 font-mono text-xs">
              {/* Header */}
              <div className="flex items-start justify-between pb-3 border-b border-teal-light/30">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-cyan-neon font-bold text-sm">{selectedAction.id}</span>
                    {getStatusBadge(selectedAction.status)}
                  </div>
                  <h2 className="text-base font-heading font-bold text-ivory">
                    {selectedAction.action_type} on {selectedAction.target_entity}
                  </h2>
                </div>

                {/* Approval buttons if pending */}
                {selectedAction.status === 'PENDING_APPROVAL' && (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleOpenApprove(selectedAction)}
                      className="flex items-center space-x-1 px-3 py-1.5 rounded bg-lime-acid text-obsidian font-bold text-xs hover:bg-lime-acid/90 shadow-neon-lime transition-all"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>APPROVE ACTION</span>
                    </button>
                    <button
                      onClick={() => handleOpenReject(selectedAction)}
                      className="flex items-center space-x-1 px-3 py-1.5 rounded bg-coral-neon/20 border border-coral-neon/40 text-coral-neon font-bold text-xs hover:bg-coral-neon hover:text-obsidian transition-all"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>REJECT</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Technical Specifications */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 p-3 rounded bg-obsidian/70 border border-teal-light/30">
                <div>
                  <div className="text-[10px] text-sage uppercase">Action Type</div>
                  <div className="text-ivory font-bold">{selectedAction.action_type}</div>
                </div>
                <div>
                  <div className="text-[10px] text-sage uppercase">Target Asset/User</div>
                  <div className="text-cyan-neon font-bold">{selectedAction.target_entity}</div>
                </div>
                <div>
                  <div className="text-[10px] text-sage uppercase">Associated Investigation</div>
                  <div className="text-ivory font-bold">{selectedAction.investigation_id}</div>
                </div>
              </div>

              {/* Rationale */}
              <div>
                <div className="text-[10px] text-sage uppercase mb-1">Multi-Agent Forensic Rationale</div>
                <div className="p-3 rounded bg-obsidian/50 border border-teal-light/30 text-ivory font-sans leading-relaxed">
                  {selectedAction.rationale}
                </div>
              </div>

              {/* Risk Assessment */}
              {selectedAction.risk_assessment && (
                <div>
                  <div className="text-[10px] text-sage uppercase mb-1">Operational Impact Evaluation</div>
                  <div className="p-3 rounded bg-obsidian/50 border border-teal-light/30 text-sage font-sans">
                    {selectedAction.risk_assessment}
                  </div>
                </div>
              )}

              {/* Simulated Execution Log Terminal */}
              <div>
                <div className="text-[10px] text-sage uppercase mb-1 flex items-center space-x-1">
                  <Terminal className="w-3.5 h-3.5 text-cyan-neon" />
                  <span>Simulated Containment Dispatch Log</span>
                </div>
                <div className="p-3 rounded bg-obsidian border border-teal-light/40 font-mono text-[11px] text-lime-acid/90 whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed">
                  {selectedAction.execution_log || 'Awaiting human authorization for simulated containment dispatch.'}
                </div>
              </div>

              {/* Audit Provenance */}
              {selectedAction.decided_by && (
                <div className="p-2.5 rounded bg-teal-brand/20 border border-teal-light/40 text-[11px] flex justify-between items-center text-sage">
                  <span>
                    Authorized By: <strong className="text-ivory">{selectedAction.decided_by}</strong>
                  </span>
                  <span>
                    Timestamp: <strong className="text-ivory">{selectedAction.decision_timestamp?.substring(0, 19).replace('T', ' ')} UTC</strong>
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Human Approval / Rejection Modal */}
      {showApprovalModal && selectedAction && (
        <div className="fixed inset-0 bg-obsidian/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md p-6 rounded-xl bg-charcoal border border-cyan-neon shadow-neon-cyan font-mono text-xs space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-teal-light/30">
              <h3 className="font-heading font-bold text-base text-ivory flex items-center space-x-2">
                <UserCheck className="w-4 h-4 text-cyan-neon" />
                <span>
                  {isRejectMode ? 'CONFIRM ACTION REJECTION' : 'AUTHORIZE SIMULATED CONTAINMENT'}
                </span>
              </h3>
              <button
                onClick={() => setShowApprovalModal(false)}
                className="text-sage hover:text-ivory"
              >
                ✕
              </button>
            </div>

            <div>
              <p className="text-sage mb-2 font-sans">
                You are about to {isRejectMode ? 'reject' : 'authorize simulated containment for'}:
              </p>
              <div className="p-2.5 rounded bg-obsidian border border-teal-light/30 font-bold text-cyan-neon">
                {selectedAction.action_type} on {selectedAction.target_entity}
              </div>
            </div>

            <div>
              <label className="block text-[10px] text-sage uppercase mb-1">
                Authorizing Analyst Name:
              </label>
              <input
                type="text"
                value={analystName}
                onChange={(e) => setAnalystName(e.target.value)}
                className="w-full p-2 rounded bg-obsidian border border-teal-light/40 text-ivory focus:outline-none focus:border-cyan-neon"
              />
            </div>

            <div>
              <label className="block text-[10px] text-sage uppercase mb-1">
                Justification / Audit Comment:
              </label>
              <textarea
                rows={3}
                value={decisionComments}
                onChange={(e) => setDecisionComments(e.target.value)}
                className="w-full p-2 rounded bg-obsidian border border-teal-light/40 text-ivory focus:outline-none focus:border-cyan-neon font-sans"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setShowApprovalModal(false)}
                className="px-4 py-2 rounded bg-obsidian border border-teal-light text-sage hover:text-ivory"
              >
                CANCEL
              </button>
              <button
                onClick={handleSubmitDecision}
                disabled={isSubmitting}
                className={`px-4 py-2 rounded font-bold transition-all ${
                  isRejectMode
                    ? 'bg-coral-neon text-obsidian hover:bg-coral-neon/90'
                    : 'bg-lime-acid text-obsidian hover:bg-lime-acid/90 shadow-neon-lime'
                }`}
              >
                {isSubmitting ? 'PROCESSING...' : isRejectMode ? 'REJECT ACTION' : 'EXECUTE AUTHORIZATION'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
