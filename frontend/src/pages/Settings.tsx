import React, { useEffect, useState } from 'react';
import {
  Sliders,
  Activity,
  Brain,
  Cpu,
  Workflow,
  Database,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Key,
  Trash2,
  Terminal,
  Layers,
  Zap,
  ShieldCheck,
  ArrowRightLeft,
  Clock,
  Sparkles
} from 'lucide-react';
import {
  fetchSystemSettingsHealth,
  updateLLMSettings,
  testLLMConnection,
  resetDemoEnvironment
} from '../services/api';
import { SystemHealth, LLMConnectionTestResult } from '../types';

export const Settings: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Form State
  const [provider, setProvider] = useState<string>('gemini');
  const [fallbackProvider, setFallbackProvider] = useState<string>('openai');
  const [geminiModel, setGeminiModel] = useState<string>('gemini-flash-lite-latest');
  const [geminiApiKey, setGeminiApiKey] = useState<string>('');
  const [openaiModel, setOpenaiModel] = useState<string>('gpt-4o-mini');
  const [openaiApiKey, setOpenaiApiKey] = useState<string>('');
  const [liveReasoning, setLiveReasoning] = useState<boolean>(true);
  const [allowFallback, setAllowFallback] = useState<boolean>(true);

  const [savingConfig, setSavingConfig] = useState<boolean>(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // Connection Test States
  const [testingGemini, setTestingGemini] = useState<boolean>(false);
  const [geminiTestResult, setGeminiTestResult] = useState<LLMConnectionTestResult | null>(null);

  const [testingOpenai, setTestingOpenai] = useState<boolean>(false);
  const [openaiTestResult, setOpenaiTestResult] = useState<LLMConnectionTestResult | null>(null);

  const [resetting, setResetting] = useState<boolean>(false);

  const loadHealth = async () => {
    try {
      setLoading(true);
      const data = await fetchSystemSettingsHealth();
      setHealth(data);
      setProvider(data.llm_provider || 'gemini');
      setFallbackProvider(data.llm_fallback_provider || 'openai');
      setGeminiModel(data.gemini_model || 'gemini-flash-lite-latest');
      setOpenaiModel(data.openai_model || 'gpt-4o-mini');
      setLiveReasoning(data.live_reasoning_enabled ?? true);
      setAllowFallback(data.deterministic_fallback_allowed ?? true);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const handleSaveLLM = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSavingConfig(true);
      setSaveMessage(null);
      const res = await updateLLMSettings({
        provider,
        fallback_provider: fallbackProvider,
        gemini_model: geminiModel,
        gemini_api_key: geminiApiKey || undefined,
        openai_model: openaiModel,
        openai_api_key: openaiApiKey || undefined,
        live_reasoning: liveReasoning,
        allow_fallback: allowFallback,
      });
      setSaveMessage(res.message);
      // Clear password inputs after applying
      setGeminiApiKey('');
      setOpenaiApiKey('');
      await loadHealth();
    } catch (err: any) {
      setSaveMessage('Failed to update LLM configuration: ' + err.message);
    } finally {
      setSavingConfig(false);
    }
  };

  const handleTestProvider = async (p: 'gemini' | 'openai') => {
    if (p === 'gemini') {
      try {
        setTestingGemini(true);
        setGeminiTestResult(null);
        const res = await testLLMConnection({
          provider: 'gemini',
          api_key: geminiApiKey || undefined,
          model: geminiModel || undefined,
        });
        setGeminiTestResult(res);
      } catch (err: any) {
        setGeminiTestResult({
          provider: 'gemini',
          model: geminiModel,
          status: 'CONNECTION_FAILED',
          available: false,
          message: err.message,
          tested_at: new Date().toISOString(),
        });
      } finally {
        setTestingGemini(false);
      }
    } else {
      try {
        setTestingOpenai(true);
        setOpenaiTestResult(null);
        const res = await testLLMConnection({
          provider: 'openai',
          api_key: openaiApiKey || undefined,
          model: openaiModel || undefined,
        });
        setOpenaiTestResult(res);
      } catch (err: any) {
        setOpenaiTestResult({
          provider: 'openai',
          model: openaiModel,
          status: 'CONNECTION_FAILED',
          available: false,
          message: err.message,
          tested_at: new Date().toISOString(),
        });
      } finally {
        setTestingOpenai(false);
      }
    }
  };

  const handleResetDemo = async () => {
    if (!confirm('Clear all synthetic DEMO events, alerts, and investigations? This cannot be undone.')) {
      return;
    }
    try {
      setResetting(true);
      await resetDemoEnvironment();
      await loadHealth();
      alert('All synthetic DEMO data cleared successfully. LIVE data preserved intact.');
    } catch (err) {
      console.error(err);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto font-mono text-xs">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-teal-light/40 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-cyan-neon" />
            <h1 className="text-xl md:text-2xl font-bold font-heading tracking-tight text-ivory">
              SYSTEM SETTINGS & DUAL LLM REASONING ENGINE
            </h1>
          </div>
          <p className="text-xs text-sage mt-1">
            Dual Provider Orchestration (Gemini & OpenAI) • Windows Native Runtime • Controlled Failover & Provenance Safeguards
          </p>
        </div>

        <button
          onClick={loadHealth}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-charcoal border border-teal-light text-sage hover:text-cyan-neon hover:border-cyan-neon transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-neon' : ''}`} />
          <span>RE-RUN DIAGNOSTICS</span>
        </button>
      </div>

      {/* Diagnostics Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* FastAPI Core */}
        <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 space-y-1.5">
          <div className="flex items-center justify-between text-sage text-[10px] uppercase">
            <span>FastAPI Core</span>
            <Activity className="w-4 h-4 text-cyan-neon" />
          </div>
          <div className="text-lg font-bold text-cyan-neon">
            {health?.backend_health || 'OPERATIONAL'}
          </div>
          <div className="text-[10px] text-sage">Windows Python 3.11 Runtime</div>
        </div>

        {/* SQLite Database */}
        <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 space-y-1.5">
          <div className="flex items-center justify-between text-sage text-[10px] uppercase">
            <span>Database Partitioning</span>
            <Database className="w-4 h-4 text-cyan-neon" />
          </div>
          <div className="text-lg font-bold text-lime-acid">
            {health?.database_connected ? 'CONNECTED' : 'DISCONNECTED'}
          </div>
          <div className="text-[10px] text-sage">
            {health ? `${health.events_count_live} Live / ${health.events_count_demo} Demo Records` : '—'}
          </div>
        </div>

        {/* Active LLM Mode */}
        <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 space-y-1.5">
          <div className="flex items-center justify-between text-sage text-[10px] uppercase">
            <span>Active LLM Strategy</span>
            <Brain className="w-4 h-4 text-cyan-neon" />
          </div>
          <div className="text-lg font-bold text-cyan-neon uppercase">
            {health?.llm_provider || 'GEMINI'}
          </div>
          <div className="text-[10px] text-sage truncate">
            {health?.llm_provider_status}
          </div>
        </div>

        {/* Fallback Engine */}
        <div className="p-4 rounded-lg bg-charcoal border border-teal-light/40 space-y-1.5">
          <div className="flex items-center justify-between text-sage text-[10px] uppercase">
            <span>Forensic Fallback</span>
            <ShieldCheck className="w-4 h-4 text-lime-acid" />
          </div>
          <div
            className={`text-lg font-bold ${
              health?.degraded_mode ? 'text-amber-neon' : 'text-lime-acid'
            }`}
          >
            {health?.degraded_mode ? 'DEGRADED FALLBACK' : 'LIVE READY'}
          </div>
          <div className="text-[10px] text-sage">
            {health?.deterministic_fallback_allowed ? 'Fallback Permitted' : 'Strict Live Only'}
          </div>
        </div>
      </div>

      {/* Dual Provider Status Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Google Gemini Card */}
        <div className="p-5 rounded-lg bg-charcoal border border-teal-light/50 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-teal-light/30">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-cyan-neon" />
              <h2 className="text-sm font-heading font-bold text-ivory uppercase tracking-wider">
                Google Gemini (Primary Provider)
              </h2>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                health?.gemini_configured
                  ? 'bg-lime-acid/15 border-lime-acid/40 text-lime-acid'
                  : 'bg-amber-neon/15 border-amber-neon/40 text-amber-neon'
              }`}
            >
              {health?.gemini_configured ? 'CONFIGURED' : 'NOT CONFIGURED'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-2.5 rounded bg-obsidian border border-teal-light/30">
              <div className="text-[10px] text-sage uppercase">Configured Model</div>
              <div className="text-cyan-neon font-bold mt-0.5">{health?.gemini_model || 'gemini-flash-lite-latest'}</div>
            </div>
            <div className="p-2.5 rounded bg-obsidian border border-teal-light/30">
              <div className="text-[10px] text-sage uppercase">API Key Status</div>
              <div className="text-ivory mt-0.5">
                {health?.gemini_configured ? '●●●●●●●● (Loaded in Backend)' : 'Not Set (Fallback Active)'}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <button
              type="button"
              onClick={() => handleTestProvider('gemini')}
              disabled={testingGemini}
              className="flex items-center space-x-2 px-3.5 py-1.5 rounded bg-cyan-neon/15 border border-cyan-neon/50 text-cyan-neon hover:bg-cyan-neon hover:text-obsidian transition-all text-xs font-bold"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{testingGemini ? 'PROBING GEMINI...' : 'TEST GEMINI CONNECTION'}</span>
            </button>
            <span className="text-[10px] text-sage">Official google-genai SDK</span>
          </div>

          {geminiTestResult && (
            <div
              className={`p-3 rounded border text-[11px] space-y-1 ${
                geminiTestResult.status === 'HEALTHY'
                  ? 'bg-lime-acid/10 border-lime-acid/40 text-lime-acid'
                  : geminiTestResult.status === 'SERVER_BUSY'
                  ? 'bg-amber-neon/10 border-amber-neon/40 text-amber-neon'
                  : 'bg-coral-neon/10 border-coral-neon/40 text-coral-neon'
              }`}
            >
              <div className="flex items-center justify-between font-bold">
                <span>Status: {geminiTestResult.status}</span>
                {geminiTestResult.latency_ms && (
                  <span className="text-[10px] font-mono text-sage">{geminiTestResult.latency_ms}ms</span>
                )}
              </div>
              <p className="text-[10px] text-ivory/90">{geminiTestResult.message}</p>
            </div>
          )}
        </div>

        {/* OpenAI Card */}
        <div className="p-5 rounded-lg bg-charcoal border border-teal-light/50 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-teal-light/30">
            <div className="flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-cyan-neon" />
              <h2 className="text-sm font-heading font-bold text-ivory uppercase tracking-wider">
                OpenAI (Secondary / Failover Provider)
              </h2>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                health?.openai_configured
                  ? 'bg-lime-acid/15 border-lime-acid/40 text-lime-acid'
                  : 'bg-amber-neon/15 border-amber-neon/40 text-amber-neon'
              }`}
            >
              {health?.openai_configured ? 'CONFIGURED' : 'NOT CONFIGURED'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-2.5 rounded bg-obsidian border border-teal-light/30">
              <div className="text-[10px] text-sage uppercase">Configured Model</div>
              <div className="text-cyan-neon font-bold mt-0.5">{health?.openai_model || 'gpt-4o-mini'}</div>
            </div>
            <div className="p-2.5 rounded bg-obsidian border border-teal-light/30">
              <div className="text-[10px] text-sage uppercase">API Key Status</div>
              <div className="text-ivory mt-0.5">
                {health?.openai_configured ? '●●●●●●●● (Loaded in Backend)' : 'Not Set (Fallback Active)'}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <button
              type="button"
              onClick={() => handleTestProvider('openai')}
              disabled={testingOpenai}
              className="flex items-center space-x-2 px-3.5 py-1.5 rounded bg-cyan-neon/15 border border-cyan-neon/50 text-cyan-neon hover:bg-cyan-neon hover:text-obsidian transition-all text-xs font-bold"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{testingOpenai ? 'PROBING OPENAI...' : 'TEST OPENAI CONNECTION'}</span>
            </button>
            <span className="text-[10px] text-sage">Official openai SDK (Windows Guarded)</span>
          </div>

          {openaiTestResult && (
            <div
              className={`p-3 rounded border text-[11px] space-y-1 ${
                openaiTestResult.status === 'HEALTHY'
                  ? 'bg-lime-acid/10 border-lime-acid/40 text-lime-acid'
                  : 'bg-coral-neon/10 border-coral-neon/40 text-coral-neon'
              }`}
            >
              <div className="flex items-center justify-between font-bold">
                <span>Status: {openaiTestResult.status}</span>
                {openaiTestResult.latency_ms && (
                  <span className="text-[10px] font-mono text-sage">{openaiTestResult.latency_ms}ms</span>
                )}
              </div>
              <p className="text-[10px] text-ivory/90">{openaiTestResult.message}</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Configuration & Governance Form */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Dual LLM Configuration Form */}
        <div className="lg:col-span-8 p-6 rounded-lg bg-charcoal border border-teal-light/40 space-y-5">
          <div className="flex items-center space-x-2 pb-3 border-b border-teal-light/30">
            <Key className="w-4 h-4 text-cyan-neon" />
            <h2 className="text-sm font-heading font-bold text-ivory uppercase tracking-wider">
              Dual LLM Provider & Routing Control
            </h2>
          </div>

          <form onSubmit={handleSaveLLM} className="space-y-4">
            {/* Routing Strategy Dropdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] text-sage uppercase mb-1">
                  Primary Routing Strategy:
                </label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full p-2.5 rounded bg-obsidian border border-teal-light/40 text-ivory text-xs focus:outline-none focus:border-cyan-neon"
                >
                  <option value="gemini">Google Gemini (Default Primary)</option>
                  <option value="openai">OpenAI (Primary Direct)</option>
                  <option value="auto">Automatic (Gemini Primary + OpenAI Failover)</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-sage uppercase mb-1">
                  Failover Secondary Provider:
                </label>
                <select
                  value={fallbackProvider}
                  onChange={(e) => setFallbackProvider(e.target.value)}
                  className="w-full p-2.5 rounded bg-obsidian border border-teal-light/40 text-ivory text-xs focus:outline-none focus:border-cyan-neon"
                >
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Google Gemini</option>
                </select>
              </div>
            </div>

            {/* Provider Credentials & Models */}
            <div className="p-4 rounded bg-obsidian/70 border border-teal-light/30 space-y-4">
              <div className="text-[11px] font-bold text-cyan-neon uppercase">
                1. Google Gemini Parameters
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] text-sage uppercase mb-1">Gemini Model:</label>
                  <input
                    type="text"
                    value={geminiModel}
                    onChange={(e) => setGeminiModel(e.target.value)}
                    placeholder="gemini-flash-lite-latest or gemini-3.8-flash"
                    className="w-full p-2 rounded bg-charcoal border border-teal-light/40 text-ivory text-xs font-mono focus:border-cyan-neon"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-sage uppercase mb-1">
                    Gemini API Key (Optional Override):
                  </label>
                  <input
                    type="password"
                    value={geminiApiKey}
                    onChange={(e) => setGeminiApiKey(e.target.value)}
                    placeholder={health?.gemini_configured ? "●●●●●●●● (Loaded from .env)" : "Enter Gemini API key..."}
                    className="w-full p-2 rounded bg-charcoal border border-teal-light/40 text-ivory text-xs font-mono focus:border-cyan-neon"
                  />
                </div>
              </div>
            </div>

            <div className="p-4 rounded bg-obsidian/70 border border-teal-light/30 space-y-4">
              <div className="text-[11px] font-bold text-cyan-neon uppercase">
                2. OpenAI Parameters
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] text-sage uppercase mb-1">OpenAI Model:</label>
                  <input
                    type="text"
                    value={openaiModel}
                    onChange={(e) => setOpenaiModel(e.target.value)}
                    placeholder="gpt-4o-mini or gpt-4o"
                    className="w-full p-2 rounded bg-charcoal border border-teal-light/40 text-ivory text-xs font-mono focus:border-cyan-neon"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-sage uppercase mb-1">
                    OpenAI API Key (Optional Override):
                  </label>
                  <input
                    type="password"
                    value={openaiApiKey}
                    onChange={(e) => setOpenaiApiKey(e.target.value)}
                    placeholder={health?.openai_configured ? "●●●●●●●● (Loaded from .env)" : "Enter OpenAI API key..."}
                    className="w-full p-2 rounded bg-charcoal border border-teal-light/40 text-ivory text-xs font-mono focus:border-cyan-neon"
                  />
                </div>
              </div>
            </div>

            {/* Execution Toggles */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              <label className="flex items-center space-x-2.5 p-3 rounded bg-obsidian border border-teal-light/30 cursor-pointer">
                <input
                  type="checkbox"
                  checked={liveReasoning}
                  onChange={(e) => setLiveReasoning(e.target.checked)}
                  className="rounded bg-charcoal border-teal-light text-cyan-neon focus:ring-0"
                />
                <div>
                  <div className="text-xs font-bold text-ivory">Enable Live LLM Reasoning</div>
                  <div className="text-[10px] text-sage">Allows LangGraph to call configured LLM providers</div>
                </div>
              </label>

              <label className="flex items-center space-x-2.5 p-3 rounded bg-obsidian border border-teal-light/30 cursor-pointer">
                <input
                  type="checkbox"
                  checked={allowFallback}
                  onChange={(e) => setAllowFallback(e.target.checked)}
                  className="rounded bg-charcoal border-teal-light text-cyan-neon focus:ring-0"
                />
                <div>
                  <div className="text-xs font-bold text-ivory">Allow Deterministic Fallback</div>
                  <div className="text-[10px] text-sage">Engage telemetry synthesizer on provider failure</div>
                </div>
              </label>
            </div>

            {saveMessage && (
              <div className="p-2.5 rounded bg-teal-brand/20 border border-cyan-neon/40 text-cyan-neon text-[11px]">
                {saveMessage}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={savingConfig}
                className="px-6 py-2.5 rounded bg-cyan-neon text-obsidian font-bold text-xs hover:bg-cyan-neon/90 shadow-neon-cyan transition-all"
              >
                {savingConfig ? 'APPLYING CONFIGURATION...' : 'APPLY DUAL LLM CONFIGURATION'}
              </button>
            </div>
          </form>
        </div>

        {/* Governance & Failover Architecture Panel */}
        <div className="lg:col-span-4 space-y-6">
          {/* Safeguards Summary */}
          <div className="p-5 rounded-lg bg-charcoal border border-teal-light/40 space-y-3">
            <div className="flex items-center space-x-2 pb-2 border-b border-teal-light/30">
              <ShieldCheck className="w-4 h-4 text-cyan-neon" />
              <h2 className="text-xs font-heading font-bold text-ivory uppercase tracking-wider">
                Forensic Governance Safeguards
              </h2>
            </div>

            <div className="space-y-2 text-[11px] text-sage">
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-neon mt-1.5 shrink-0" />
                <span>
                  <strong className="text-ivory">Grounded Epistemology:</strong> LLM responses are validated against raw database events. Phantom event IDs are stripped.
                </span>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-neon mt-1.5 shrink-0" />
                <span>
                  <strong className="text-ivory">Controlled Failover:</strong> Unrecoverable errors (invalid keys, 401 auth, quota exhausted) are NOT silently failed over.
                </span>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-neon mt-1.5 shrink-0" />
                <span>
                  <strong className="text-ivory">Audited Switches:</strong> All provider transitions are recorded in LangGraph step history with reasons.
                </span>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-neon mt-1.5 shrink-0" />
                <span>
                  <strong className="text-ivory">Simulated Containment:</strong> The LLM cannot execute containment actions autonomously; human approval is strictly required.
                </span>
              </div>
            </div>
          </div>

          {/* Dataset Partitions & Maintenance */}
          <div className="p-5 rounded-lg bg-charcoal border border-teal-light/40 space-y-3">
            <div className="flex items-center space-x-2 pb-2 border-b border-teal-light/30">
              <Layers className="w-4 h-4 text-cyan-neon" />
              <h2 className="text-xs font-heading font-bold text-ivory uppercase tracking-wider">
                Database Partitions
              </h2>
            </div>

            <div className="space-y-2">
              <div className="p-2.5 rounded bg-obsidian border border-teal-light/30 flex justify-between items-center">
                <span className="text-[10px] text-sage uppercase">LIVE Production Records</span>
                <span className="text-cyan-neon font-bold">{health?.events_count_live || 0}</span>
              </div>
              <div className="p-2.5 rounded bg-obsidian border border-teal-light/30 flex justify-between items-center">
                <span className="text-[10px] text-sage uppercase">DEMO Synthetic Records</span>
                <span className="text-amber-neon font-bold">{health?.events_count_demo || 0}</span>
              </div>
            </div>

            <button
              onClick={handleResetDemo}
              disabled={resetting}
              className="w-full flex items-center justify-center space-x-2 p-2 rounded bg-coral-neon/15 border border-coral-neon/40 text-coral-neon hover:bg-coral-neon hover:text-obsidian transition-all font-bold text-[11px] mt-2"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{resetting ? 'PURGING...' : 'RESET DEMO DATA'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
