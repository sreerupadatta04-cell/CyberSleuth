import React, { useEffect, useState, useRef } from 'react';
import {
  Database,
  Upload,
  FileText,
  Filter,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Play,
  Clock,
  Layers,
  ArrowRight,
  Activity
} from 'lucide-react';
import {
  fetchTelemetry,
  uploadTelemetryFile,
  clearTelemetryData,
  triggerDetectionRun
} from '../services/api';
import { TelemetryEvent } from '../types';
import { SeverityBadge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';

export const Telemetry: React.FC = () => {
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

  // Filters
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [envFilter, setEnvFilter] = useState<string>('ALL'); // ALL, DEMO, LIVE
  const [hostSearch, setHostSearch] = useState<string>('');

  // Upload options
  const [isDemoUpload, setIsDemoUpload] = useState<boolean>(false);
  const [autoDetect, setAutoDetect] = useState<boolean>(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 150 };
      if (eventTypeFilter !== 'ALL') params.event_type = eventTypeFilter;
      if (severityFilter !== 'ALL') params.severity = severityFilter;
      if (envFilter === 'DEMO') params.is_demo = true;
      if (envFilter === 'LIVE') params.is_demo = false;
      if (hostSearch.trim()) params.host = hostSearch.trim();

      const data = await fetchTelemetry(params);
      setEvents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [eventTypeFilter, severityFilter, envFilter, hostSearch]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setUploadResult(null);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('is_demo', String(isDemoUpload));
      formData.append('run_detection_after', String(autoDetect));

      const res = await uploadTelemetryFile(formData);
      setUploadResult(res);
      await loadEvents();
    } catch (err: any) {
      alert('Upload error: ' + (err.message || err));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleClear = async (demoOnly?: boolean) => {
    if (!confirm(demoOnly ? 'Clear all DEMO telemetry records?' : 'Clear telemetry records?')) return;
    try {
      await clearTelemetryData(demoOnly);
      await loadEvents();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto font-mono text-xs">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-teal-light/40 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-cyan-neon" />
            <h1 className="text-xl md:text-2xl font-bold font-heading tracking-tight text-ivory">
              SECURITY TELEMETRY INGESTION ENGINE
            </h1>
          </div>
          <p className="text-xs text-sage mt-1">
            Normalized JSON/CSV Telemetry Pipeline • Strict DEMO vs LIVE Database Partitioning
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".json,.csv"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="flex items-center space-x-1.5 px-4 py-2 rounded bg-cyan-neon text-obsidian font-bold text-xs hover:bg-cyan-neon/90 shadow-neon-cyan transition-all"
          >
            <Upload className={`w-3.5 h-3.5 ${uploading ? 'animate-spin' : ''}`} />
            <span>{uploading ? 'INGESTING...' : 'UPLOAD TELEMETRY (JSON / CSV)'}</span>
          </button>
        </div>
      </div>

      {/* Upload Settings Ribbon */}
      <div className="p-3.5 rounded-lg bg-charcoal border border-teal-light/30 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-5">
          <label className="flex items-center space-x-2 cursor-pointer text-ivory">
            <input
              type="checkbox"
              checked={isDemoUpload}
              onChange={(e) => setIsDemoUpload(e.target.checked)}
              className="accent-cyan-neon rounded"
            />
            <span>Tag as DEMO data (Isolated from LIVE production records)</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer text-ivory">
            <input
              type="checkbox"
              checked={autoDetect}
              onChange={(e) => setAutoDetect(e.target.checked)}
              className="accent-cyan-neon rounded"
            />
            <span>Auto-trigger threat detection upon ingestion</span>
          </label>
        </div>

        <button
          onClick={() => handleClear(true)}
          className="flex items-center space-x-1 text-sage hover:text-coral-neon transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>CLEAR DEMO DATA</span>
        </button>
      </div>

      {/* Ingestion Report Banner (if file just uploaded) */}
      {uploadResult && (
        <div className="p-4 rounded-lg bg-teal-brand/30 border border-cyan-neon/50 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-cyan-neon font-bold text-sm">
              <CheckCircle2 className="w-4 h-4" />
              <span>Ingestion Pipeline Complete</span>
            </div>
            <button
              onClick={() => setUploadResult(null)}
              className="text-sage hover:text-ivory"
            >
              ✕
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px] pt-1">
            <div>Total Received: <strong className="text-ivory">{uploadResult.total_received}</strong></div>
            <div>Valid Normalized: <strong className="text-cyan-neon">{uploadResult.valid_count}</strong></div>
            <div>Invalid Records: <strong className="text-coral-neon">{uploadResult.invalid_count}</strong></div>
            <div>Target Partition: <strong className="text-amber-neon">{uploadResult.is_demo ? 'DEMO' : 'LIVE'}</strong></div>
          </div>
          {uploadResult.errors?.length > 0 && (
            <div className="text-[10px] text-coral-neon pt-1">
              Sample validation errors: {uploadResult.errors.join('; ')}
            </div>
          )}
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between p-3 rounded-lg bg-charcoal border border-teal-light/30 gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-1.5 text-sage">
            <Filter className="w-3.5 h-3.5" />
            <span>EVENT TYPE:</span>
            <select
              value={eventTypeFilter}
              onChange={(e) => setEventTypeFilter(e.target.value)}
              className="bg-obsidian border border-teal-light/40 rounded px-2 py-1 text-ivory text-xs focus:outline-none"
            >
              <option value="ALL">All Types</option>
              <option value="AUTH_FAILURE">AUTH_FAILURE</option>
              <option value="AUTH_SUCCESS">AUTH_SUCCESS</option>
              <option value="PROCESS_CREATE">PROCESS_CREATE</option>
              <option value="POWERSHELL_EXEC">POWERSHELL_EXEC</option>
              <option value="NETWORK_CONNECT">NETWORK_CONNECT</option>
              <option value="DNS_QUERY">DNS_QUERY</option>
              <option value="FILE_MOD">FILE_MOD</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 text-sage">
            <span>SEVERITY:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-obsidian border border-teal-light/40 rounded px-2 py-1 text-ivory text-xs focus:outline-none"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="INFO">Info</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 text-sage">
            <span>ENVIRONMENT:</span>
            <select
              value={envFilter}
              onChange={(e) => setEnvFilter(e.target.value)}
              className="bg-obsidian border border-teal-light/40 rounded px-2 py-1 text-ivory text-xs focus:outline-none"
            >
              <option value="ALL">All Partitions</option>
              <option value="DEMO">Demo Only</option>
              <option value="LIVE">Live Only</option>
            </select>
          </div>

          <input
            type="text"
            placeholder="Search Host / Asset..."
            value={hostSearch}
            onChange={(e) => setHostSearch(e.target.value)}
            className="bg-obsidian border border-teal-light/40 rounded px-2.5 py-1 text-ivory text-xs placeholder:text-sage/50 focus:outline-none focus:border-cyan-neon"
          />
        </div>

        <div className="text-sage text-[11px]">
          Displaying <span className="text-cyan-neon font-bold">{events.length}</span> normalized events
        </div>
      </div>

      {events.length === 0 && !loading && (
        <EmptyState
          icon={Database}
          title="No Telemetry Events Stored"
          description="Upload a CSV or JSON telemetry log file, or load one of the four synthetic demo datasets to populate the security event warehouse."
          actionLabel="SELECT TELEMETRY FILE"
          onAction={() => fileInputRef.current?.click()}
        />
      )}

      {/* Telemetry Events Table */}
      {events.length > 0 && (
        <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-teal-light/30 text-[10px] text-sage uppercase">
                <th className="pb-2.5">Event ID</th>
                <th className="pb-2.5">Timestamp</th>
                <th className="pb-2.5">Type</th>
                <th className="pb-2.5">Severity</th>
                <th className="pb-2.5">User</th>
                <th className="pb-2.5">Host</th>
                <th className="pb-2.5">Network / Process / Domain</th>
                <th className="pb-2.5">Env</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-teal-light/10">
              {events.map((ev) => (
                <tr key={ev.id} className="hover:bg-teal-brand/10 transition-colors">
                  <td className="py-2.5 text-cyan-neon font-bold">{ev.id}</td>
                  <td className="py-2.5 text-sage/90">
                    {ev.timestamp.substring(0, 19).replace('T', ' ')}
                  </td>
                  <td className="py-2.5 text-ivory font-semibold">{ev.event_type}</td>
                  <td className="py-2.5">
                    <SeverityBadge severity={ev.severity} size="sm" />
                  </td>
                  <td className="py-2.5 text-ivory">{ev.user || '—'}</td>
                  <td className="py-2.5 text-cyan-neon">{ev.host || '—'}</td>
                  <td className="py-2.5 text-sage max-w-xs truncate font-mono text-[11px]">
                    {ev.command_line ||
                      ev.domain ||
                      (ev.destination_ip ? `${ev.source_ip} -> ${ev.destination_ip}:${ev.destination_port}` : '—')}
                  </td>
                  <td className="py-2.5">
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded border font-bold ${
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
      )}
    </div>
  );
};
