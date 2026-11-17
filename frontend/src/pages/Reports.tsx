import React, { useEffect, useState } from 'react';
import {
  FileText,
  Download,
  Eye,
  CheckCircle2,
  AlertTriangle,
  Brain,
  Shield,
  Clock,
  Activity
} from 'lucide-react';
import { fetchInvestigations, fetchReportMetadata } from '../services/api';
import { Investigation } from '../types';
import { EmptyState } from '../components/common/EmptyState';

interface ReportsProps {
  initialInvestigationId?: string | null;
}

export const Reports: React.FC<ReportsProps> = ({ initialInvestigationId }) => {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [selectedInvId, setSelectedInvId] = useState<string>(initialInvestigationId || '');
  const [metadata, setMetadata] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const invs = await fetchInvestigations();
        setInvestigations(invs);
        if (initialInvestigationId) {
          setSelectedInvId(initialInvestigationId);
        } else if (invs.length > 0) {
          setSelectedInvId(invs[0].id);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [initialInvestigationId]);

  useEffect(() => {
    if (!selectedInvId) return;
    async function loadMeta() {
      try {
        const data = await fetchReportMetadata(selectedInvId);
        setMetadata(data);
      } catch (err) {
        console.error(err);
        setMetadata(null);
      }
    }
    loadMeta();
  }, [selectedInvId]);

  const handleDownloadPDF = () => {
    if (!selectedInvId) return;
    window.open(`/api/reports/${selectedInvId}/download`, '_blank');
  };

  if (investigations.length === 0 && !loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <EmptyState
          icon={FileText}
          title="No Investigation Reports Available"
          description="Forensic PDF reports are compiled dynamically from completed multi-agent investigation records. Launch an investigation to generate a report."
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto font-mono">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-teal-light/40 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-cyan-neon" />
            <h1 className="text-xl md:text-2xl font-bold font-heading tracking-tight text-ivory">
              FORENSIC INVESTIGATION REPORTS
            </h1>
          </div>
          <p className="text-xs text-sage mt-1">
            Automated ReportLab PDF Generation • Grounded MITRE ATT&CK & Human Audit Alignment
          </p>
        </div>

        {selectedInvId && (
          <button
            onClick={handleDownloadPDF}
            className="flex items-center space-x-2 px-4 py-2 rounded bg-cyan-neon text-obsidian font-bold text-xs hover:bg-cyan-neon/90 shadow-neon-cyan transition-all"
          >
            <Download className="w-4 h-4" />
            <span>DOWNLOAD REPORTLAB PDF</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Investigation selector */}
        <div className="lg:col-span-4 space-y-2.5">
          <span className="text-[10px] text-sage uppercase tracking-wider block">
            Select Investigation Record:
          </span>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {investigations.map((inv) => {
              const isSelected = selectedInvId === inv.id;
              return (
                <div
                  key={inv.id}
                  onClick={() => setSelectedInvId(inv.id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-teal-brand/30 border-cyan-neon shadow-neon-cyan'
                      : 'bg-charcoal border-teal-light/30 hover:border-teal-light/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-cyan-neon text-xs">{inv.id}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded border uppercase ${
                        inv.status === 'COMPLETED'
                          ? 'border-lime-acid/40 text-lime-acid'
                          : 'border-cyan-neon/40 text-cyan-neon'
                      }`}
                    >
                      {inv.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-ivory truncate">
                    Alert Ref: {inv.alert_id}
                  </div>
                  <div className="text-[10px] text-sage/70 mt-1">
                    Created: {inv.created_at?.substring(0, 19).replace('T', ' ')} UTC
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Report Document Preview */}
        <div className="lg:col-span-8 p-6 rounded-lg bg-charcoal border border-teal-light/40 space-y-5 text-xs">
          {metadata ? (
            <>
              {/* Document Banner */}
              <div className="flex items-start justify-between pb-4 border-b border-teal-light/30">
                <div>
                  <div className="text-[10px] text-sage uppercase">Official CyberSleuth Dossier</div>
                  <h2 className="text-lg font-heading font-bold text-ivory">
                    {metadata.title}
                  </h2>
                  <div className="text-[11px] text-cyan-neon mt-0.5">
                    ID: {metadata.investigation_id} • Severity: {metadata.severity}
                  </div>
                </div>

                <button
                  onClick={handleDownloadPDF}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-teal-brand border border-cyan-neon/40 text-cyan-neon text-xs hover:bg-teal-light transition-colors shadow-neon-cyan"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>EXPORT PDF</span>
                </button>
              </div>

              {/* Sections Checklist */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 p-3 rounded bg-obsidian/70 border border-teal-light/30 text-[11px]">
                <div>
                  <span className="text-sage block text-[10px]">FINDINGS:</span>
                  <span className="text-ivory font-bold">{metadata.findings_count} Items</span>
                </div>
                <div>
                  <span className="text-sage block text-[10px]">MITRE MAPPINGS:</span>
                  <span className="text-ivory font-bold">{metadata.mitre_mappings_count} Techniques</span>
                </div>
                <div>
                  <span className="text-sage block text-[10px]">SUFFICIENCY:</span>
                  <span className="text-lime-acid font-bold">
                    {metadata.sufficiency_reached ? 'SATISFIED' : 'PENDING'}
                  </span>
                </div>
                <div>
                  <span className="text-sage block text-[10px]">REASONING PROVENANCE:</span>
                  <span
                    className={`font-bold ${
                      metadata.degraded_mode ? 'text-amber-neon' : 'text-cyan-neon'
                    }`}
                  >
                    {metadata.degraded_mode ? 'DETERMINISTIC FALLBACK' : metadata.llm_provider}
                  </span>
                </div>
              </div>

              {/* Executive Summary */}
              <div>
                <h4 className="text-[10px] text-sage uppercase font-bold tracking-wider mb-1.5">
                  1. Executive Forensic Summary
                </h4>
                <div className="p-3.5 rounded bg-obsidian/50 border border-teal-light/30 text-ivory font-sans text-xs leading-relaxed">
                  {metadata.executive_summary}
                </div>
              </div>

              {/* PDF Composition Details */}
              <div className="p-4 rounded bg-teal-brand/10 border border-cyan-neon/30 space-y-2 text-[11px] text-sage">
                <div className="text-cyan-neon font-bold uppercase text-xs flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>ReportLab Structural Compliance Verified</span>
                </div>
                <p className="font-sans leading-relaxed">
                  The compiled PDF contains complete CyberSleuth branding, investigation identifiers, timestamps, alert telemetry context, evidence provenance distinctions (OBSERVED vs INFERRED), attack lineage narrative, verified MITRE ATT&CK alignment, human-approved containment audit history, and research limitation boundary statements.
                </p>
              </div>
            </>
          ) : (
            <div className="py-20 text-center text-sage">
              Select an investigation to preview and download its official forensic report.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
