import {
  OverviewData,
  TelemetryEvent,
  Alert,
  Investigation,
  EvidenceGraphData,
  ResponseAction,
  DemoScenario,
  SystemHealth
} from '../types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchOverview(): Promise<OverviewData> {
  const res = await fetch(`${API_BASE}/overview`);
  if (!res.ok) throw new Error('Failed to load overview data');
  return res.json();
}

export async function fetchTelemetry(params: {
  is_demo?: boolean;
  event_type?: string;
  severity?: string;
  host?: string;
  user?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<TelemetryEvent[]> {
  const query = new URLSearchParams();
  if (params.is_demo !== undefined) query.set('is_demo', String(params.is_demo));
  if (params.event_type) query.set('event_type', params.event_type);
  if (params.severity) query.set('severity', params.severity);
  if (params.host) query.set('host', params.host);
  if (params.user) query.set('user', params.user);
  if (params.limit) query.set('limit', String(params.limit));
  if (params.offset) query.set('offset', String(params.offset));

  const res = await fetch(`${API_BASE}/telemetry?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch telemetry events');
  return res.json();
}

export async function uploadTelemetryFile(formData: FormData): Promise<any> {
  const res = await fetch(`${API_BASE}/telemetry/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function clearTelemetryData(is_demo?: boolean): Promise<any> {
  const query = is_demo !== undefined ? `?is_demo=${is_demo}` : '';
  const res = await fetch(`${API_BASE}/telemetry${query}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to clear telemetry');
  return res.json();
}

export async function fetchAlerts(params: {
  is_demo?: boolean;
  severity?: string;
  detection_method?: string;
  status?: string;
} = {}): Promise<Alert[]> {
  const query = new URLSearchParams();
  if (params.is_demo !== undefined) query.set('is_demo', String(params.is_demo));
  if (params.severity) query.set('severity', params.severity);
  if (params.detection_method) query.set('detection_method', params.detection_method);
  if (params.status) query.set('status', params.status);

  const res = await fetch(`${API_BASE}/alerts?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
}

export async function triggerDetectionRun(is_demo: boolean = false): Promise<any> {
  const res = await fetch(`${API_BASE}/alerts/detect?is_demo=${is_demo}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to trigger threat detection');
  return res.json();
}

export async function createInvestigation(alert_id: string): Promise<Investigation> {
  const res = await fetch(`${API_BASE}/investigations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ alert_id }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to start investigation' }));
    throw new Error(err.detail || 'Failed to start investigation');
  }
  return res.json();
}

export async function fetchInvestigations(is_demo?: boolean): Promise<Investigation[]> {
  const query = is_demo !== undefined ? `?is_demo=${is_demo}` : '';
  const res = await fetch(`${API_BASE}/investigations${query}`);
  if (!res.ok) throw new Error('Failed to fetch investigations');
  return res.json();
}

export async function fetchInvestigationById(id: string): Promise<Investigation> {
  const res = await fetch(`${API_BASE}/investigations/${id}`);
  if (!res.ok) throw new Error('Investigation not found');
  return res.json();
}

export async function fetchEvidenceGraph(investigationId: string): Promise<EvidenceGraphData> {
  const res = await fetch(`${API_BASE}/evidence/${investigationId}/graph`);
  if (!res.ok) throw new Error('Failed to fetch evidence graph');
  return res.json();
}

export async function fetchResponseActions(params: {
  investigation_id?: string;
  status?: string;
  is_demo?: boolean;
} = {}): Promise<ResponseAction[]> {
  const query = new URLSearchParams();
  if (params.investigation_id) query.set('investigation_id', params.investigation_id);
  if (params.status) query.set('status', params.status);
  if (params.is_demo !== undefined) query.set('is_demo', String(params.is_demo));

  const res = await fetch(`${API_BASE}/response?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch response actions');
  return res.json();
}

export async function approveAction(actionId: string, decided_by: string = 'soc_lead', comments?: string): Promise<ResponseAction> {
  const res = await fetch(`${API_BASE}/response/${actionId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decided_by, comments }),
  });
  if (!res.ok) throw new Error('Failed to approve response action');
  return res.json();
}

export async function rejectAction(actionId: string, decided_by: string = 'soc_lead', comments?: string): Promise<ResponseAction> {
  const res = await fetch(`${API_BASE}/response/${actionId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decided_by, comments }),
  });
  if (!res.ok) throw new Error('Failed to reject response action');
  return res.json();
}

export async function fetchReportMetadata(investigationId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/reports/${investigationId}`);
  if (!res.ok) throw new Error('Report not found');
  return res.json();
}

export async function fetchDemoScenarios(): Promise<DemoScenario[]> {
  const res = await fetch(`${API_BASE}/demos`);
  if (!res.ok) throw new Error('Failed to load demo scenarios');
  return res.json();
}

export async function loadDemoScenario(
  scenarioId: string,
  options: { reset_first?: boolean; freshen_timestamps?: boolean } = {}
): Promise<any> {
  const query = new URLSearchParams();
  if (options.reset_first !== undefined) query.set('reset_first', String(options.reset_first));
  if (options.freshen_timestamps !== undefined) query.set('freshen_timestamps', String(options.freshen_timestamps));
  const qStr = query.toString() ? `?${query.toString()}` : '';

  const res = await fetch(`${API_BASE}/demos/${scenarioId}/load${qStr}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load demo scenario' }));
    throw new Error(err.detail || 'Failed to load demo scenario');
  }
  return res.json();
}

export async function fetchSystemSettingsHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/settings/health`);
  if (!res.ok) throw new Error('Failed to fetch settings health');
  return res.json();
}

export async function updateLLMSettings(params: {
  provider: string;
  fallback_provider?: string;
  gemini_model?: string;
  gemini_api_key?: string;
  openai_model?: string;
  openai_api_key?: string;
  live_reasoning?: boolean;
  allow_fallback?: boolean;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/settings/llm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to update LLM configuration');
  return res.json();
}

export async function testLLMConnection(params: {
  provider: 'gemini' | 'openai';
  api_key?: string;
  model?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/settings/test-llm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to execute LLM connection test');
  return res.json();
}

export async function resetDemoEnvironment(): Promise<any> {
  const res = await fetch(`${API_BASE}/settings/reset-demo`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to reset demo data');
  return res.json();
}
