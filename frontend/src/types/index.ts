export interface TelemetryEvent {
  id: string;
  timestamp: string;
  event_type: string;
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  user?: string;
  host?: string;
  source_ip?: string;
  destination_ip?: string;
  source_port?: number;
  destination_port?: number;
  protocol?: string;
  process_name?: string;
  process_path?: string;
  parent_process?: string;
  command_line?: string;
  domain?: string;
  hash?: string;
  is_demo: boolean;
  created_at: string;
}

export interface Alert {
  id: string;
  title: string;
  description: string;
  detection_method: "RULE_BASED" | "ISOLATION_FOREST";
  rule_name?: string;
  anomaly_score?: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "NEW" | "INVESTIGATING" | "RESOLVED" | "FALSE_POSITIVE";
  primary_event_id?: string;
  affected_entities: Array<{ type: string; value: string }>;
  explanation?: string;
  investigation_id?: string;
  is_demo: boolean;
  created_at: string;
}

export interface InvestigationStep {
  id: number;
  stage_name: string;
  status: string;
  step_order: number;
  details: Record<string, any>;
  output_summary?: string;
  timestamp: string;
}

export interface Finding {
  id: string;
  statement: string;
  status: "OBSERVED" | "INFERRED" | "UNKNOWN";
  confidence: number;
  supporting_events: string[];
  rationale: string;
}

export interface Hypothesis {
  id: string;
  hypothesis: string;
  likelihood: "LOW" | "MEDIUM" | "HIGH";
  tested: boolean;
  supported?: boolean;
}

export interface MitreMapping {
  technique_id: string;
  tactic: string;
  name: string;
  supporting_events: string[];
  confidence?: number;
  explanation: string;
}

export interface Investigation {
  id: string;
  alert_id: string;
  status: "INITIALIZING" | "IN_PROGRESS" | "COMPLETED" | "FAILED" | "CLOSED";
  current_stage: string;
  progress: number;
  hypotheses: Hypothesis[];
  findings: Finding[];
  missing_evidence: any[];
  sufficiency_reached: boolean;
  iteration_count: number;
  attack_reconstruction: {
    narrative?: string;
    timeline?: string[];
  };
  mitre_mappings: MitreMapping[];
  risk_assessment: {
    overall_severity?: string;
    impact_score?: number;
    blast_radius?: string;
    uncertainty?: string;
    rationale?: string;
  };
  executive_summary?: string;
  llm_invoked: boolean;
  llm_provider?: string;
  llm_model?: string;
  degraded_mode: boolean;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  steps: InvestigationStep[];
}

export interface GraphNode {
  id: string;
  label: string;
  node_type: "user" | "host" | "ip" | "process" | "alert" | "event" | "domain" | "investigation";
  category: "OBSERVED" | "INFERRED";
  details: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  relationship_category: "OBSERVED" | "INFERRED";
  confidence: number;
  supporting_event_id?: string;
}

export interface EvidenceGraphData {
  investigation_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    observed_count: number;
    inferred_count: number;
  };
}

export interface ResponseAction {
  id: string;
  investigation_id: string;
  action_type: "ISOLATE_HOST" | "RESET_CREDENTIALS" | "BLOCK_IP" | "TERMINATE_PROCESS" | "REVOKE_TOKEN";
  target_entity: string;
  status: "PROPOSED" | "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "EXECUTED" | "FAILED";
  rationale: string;
  risk_assessment?: string;
  is_simulated: boolean;
  decided_by?: string;
  decision_reason?: string;
  decision_timestamp?: string;
  execution_result?: Record<string, any>;
  execution_log?: string;
  is_demo: boolean;
  created_at: string;
}

export interface DemoScenario {
  id: string;
  title: string;
  category: string;
  severity: string;
  description: string;
  mitre_techniques: string[];
  preview_events: any[];
}

export interface SystemHealth {
  status: string;
  backend_health: string;
  database_connected: boolean;
  detection_engine_status: string;
  langgraph_workflow_status: string;
  llm_provider_status: string;
  llm_provider: string;
  llm_fallback_provider: string;
  llm_model: string;
  degraded_mode: boolean;
  live_reasoning_enabled: boolean;
  deterministic_fallback_allowed: boolean;
  gemini_configured: boolean;
  gemini_model: string;
  gemini_status: string;
  openai_configured: boolean;
  openai_model: string;
  openai_status: string;
  events_count_live: number;
  events_count_demo: number;
  alerts_count: number;
  investigations_count: number;
  environment_mode: string;
}

export interface LLMConnectionTestResult {
  provider: string;
  model: string;
  status: "HEALTHY" | "UNCONFIGURED" | "INVALID_KEY" | "MODEL_NOT_FOUND" | "QUOTA_EXCEEDED" | "CONNECTION_FAILED" | "SERVER_BUSY";
  available: boolean;
  latency_ms?: number;
  message: string;
  tested_at: string;
}

export interface OverviewData {
  metrics: {
    total_events: number;
    live_events: number;
    demo_events: number;
    total_alerts: number;
    active_alerts: number;
    critical_threats: number;
    investigations_running: number;
    investigations_completed: number;
    detected_anomalies: number;
    rule_detections: number;
  };
  severity_distribution: Array<{ name: string; value: number }>;
  detection_types: Array<{ name: string; value: number }>;
  recent_investigations: Array<{
    id: string;
    alert_id: string;
    status: string;
    stage: string;
    progress: number;
    created_at: string;
  }>;
  recent_events: Array<{
    id: string;
    type: string;
    severity: string;
    user?: string;
    host?: string;
    timestamp: string;
    is_demo: boolean;
  }>;
}
