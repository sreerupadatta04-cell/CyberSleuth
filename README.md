# CyberSleuth: AI-Powered Multi-Agent Cybersecurity Investigation Platform

> **Research Title:** CyberSleuth: An Evidence-Driven, LLM-Assisted Multi-Agent Framework for Autonomous Cybersecurity Investigation and Explainable Incident Response.

[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-00D5C5)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript%20%7C%20Vite%20%7C%20Tailwind-B6FF5C)](https://vitejs.dev)
[![Agents](https://img.shields.io/badge/Agentic%20Engine-LangGraph%20StateGraph-FFB454)](https://langchain-ai.github.io/langgraph/)
[![LLM](https://img.shields.io/badge/Dual%20LLM-Gemini%20%26%20OpenAI-00D5C5)](https://cloud.google.com/vertex-ai)
[![ML](https://img.shields.io/badge/Anomaly%20Detection-Isolation%20Forest-FF626C)](https://scikit-learn.org)
[![Reports](https://img.shields.io/badge/Reporting-ReportLab%20PDF-033C42)](https://www.reportlab.com)

---

## 🛡️ Executive Overview & Research Proposition

CyberSleuth proposes an **evidence-driven, stateful multi-agent investigation framework** combining hybrid threat detection (deterministic rules + unsupervised Isolation Forest), dual LLM-assisted forensic reasoning (Google Gemini & OpenAI), and explainable attack reconstruction to automate cybersecurity incident triage while strictly preserving **human control over response execution**.

### Core Pillars:
1. **Hybrid Telemetry Detection:** Combines high-fidelity rule matching with Scikit-learn unsupervised Isolation Forest anomaly scoring.
2. **Dual Live LLM Integration:** Full multi-agent reasoning using official Google Gemini (`google-genai`) and OpenAI (`openai`) SDKs, with Windows-first native AppLocker DLL guards, structured output validation, and controlled failover.
3. **Stateful LangGraph Orchestration:** Employs a compiled, cyclic LangGraph `StateGraph` containing an evidence sufficiency loop, dynamic hypothesis testing, and provenance attribution.
4. **Rigorous Epistemological Provenance:** Every finding and graph edge strictly differentiates `OBSERVED` (directly recorded in telemetry) from `INFERRED` (reasoned statistical or LLM deductions). Speculative hallucinations and fake telemetry are prohibited.
5. **Human-in-the-Loop (HITL) Containment:** Incident containment actions (host isolation, credential revocation, IP blocking, process termination) are simulated and strictly require explicit analyst authorization before execution.
6. **Authentic ReportLab Forensic Reporting:** Generates audit-grade PDF incident dossiers citing exact MITRE ATT&CK techniques, timeline reconstruction, and analyst approvals.

---

## 🧠 Dual Live LLM Reasoning Architecture

CyberSleuth integrates **Google Gemini** (Primary) and **OpenAI** (Secondary / Failover) into the compiled LangGraph investigation pipeline:

```
                  +----------------------------------------------+
                  |           LangGraph Investigation            |
                  |     Stage 4: Correlation & Validation        |
                  +----------------------------------------------+
                                         |
                                         v
                         +-------------------------------+
                         |      LLMService Router        |
                         |  (Gemini, OpenAI, or Auto)    |
                         +-------------------------------+
                            /                         \
                           v                           v
              +-----------------------+     +-----------------------+
              |     Google Gemini     |     |        OpenAI         |
              |  (google-genai SDK)   |     |     (openai SDK)      |
              +-----------------------+     +-----------------------+
                           \                         /
                            v                       v
                         +-------------------------------+
                         |   Pydantic Schema Validator   |
                         |  & Telemetry Grounding Filter |
                         +-------------------------------+
                                         |
                       [Unrecoverable Error / No Key]
                                         |
                                         v
                         +-------------------------------+
                         |  Deterministic Forensic Model |
                         |   (degraded_mode = True)      |
                         +-------------------------------+
```

### Windows-First Implementation:
- **Zero Native Compiler Requirements:** Avoids Rust, C++ MSVC build tools, or administrator privilege demands.
- **Application Control / AppLocker Guard:** Implements a pure-Python in-memory compatibility shim for native Windows DLLs (e.g. `jiter.pyd`), allowing official OpenAI and Gemini SDKs to execute on restricted Windows workstations.
- **Audited Provider Failover Policy:**
  - **Unrecoverable Errors:** Authentication rejections (401), invalid API keys, invalid model identifiers (404), and quota exhaustion (429) do **NOT** silently failover. They are explicitly surfaced in diagnostics and logged in investigation history.
  - **Recoverable Faults:** Transient 502/503 service outages or network socket disconnects in `auto` mode automatically trigger a provider transition (Gemini -> OpenAI), logging the rationale into the investigation step details.
  - **Deterministic Fallback:** When keys are not configured or both providers encounter faults, CyberSleuth executes an evidence-grounded deterministic forensic synthesizer with explicit `degraded_mode = True` and provider label `DETERMINISTIC_FALLBACK`.

---

## 🎨 Visual Identity: Vintage Futuristic Fusion

CyberSleuth features a bespoke SOC design system marrying classic terminal ergonomics with modern cyber defense aesthetics:

| Color Token | Hex Code | Visual Semantic Role |
| :--- | :--- | :--- |
| **Obsidian** | `#091315` | Deepest background canvas with subtle technical grid |
| **Deep Charcoal** | `#101C1D` | Panel and card elevation surfaces |
| **Deep Teal** | `#033C42` | Primary brand color, headers, table accents |
| **Neon Cyan** | `#00D5C5` | Primary interactive highlights, active badges, observed edges |
| **Acid Lime** | `#B6FF5C` | ML anomaly highlights, execution status, healthy states |
| **Amber** | `#FFB454` | Medium/High alerts, inferred hypotheses, pending approval |
| **Coral Red** | `#FF626C` | Critical alerts, simulated containment actions, process threats |
| **Warm Ivory** | `#E7F0EC` | Primary technical typography & high-contrast labels |
| **Muted Sage** | `#91AAA5` | Secondary metadata, timestamps, and architectural labels |

**Typography:** *Space Grotesk* (headings), *IBM Plex Mono* (IPs, hashes, timestamps, event IDs), and *Inter* (body text).

---

## 📂 Project Architecture

```
CyberSleuth/
├── frontend/                     # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/           # Common, layout, and graph components
│   │   ├── pages/                # 8 Primary SOC views
│   │   │   ├── CommandCenter.tsx     # Primary SOC metrics, Recharts trends & quick actions
│   │   │   ├── ThreatDetection.tsx   # Rule Engine + Isolation Forest anomaly inspector
│   │   │   ├── Investigations.tsx    # LangGraph visual pipeline, hypotheses & findings
│   │   │   ├── EvidenceExplorer.tsx  # Interactive SVG topology graph (Observed vs Inferred)
│   │   │   ├── ResponseCenter.tsx    # Human-approved simulated incident containment
│   │   │   ├── Reports.tsx           # ReportLab PDF generation and preview
│   │   │   ├── Telemetry.tsx         # JSON/CSV ingestion engine & partition manager
│   │   │   └── Settings.tsx          # Dual LLM diagnostics, provider testing & credentials
│   │   ├── services/api.ts       # Typed API client
│   │   └── types/index.ts        # Shared TypeScript data models
│   └── dist/                     # Pre-compiled production bundle (auto-served by backend)
├── backend/                      # FastAPI + SQLAlchemy + LangGraph + Scikit-Learn
│   ├── app/
│   │   ├── api/routes/           # Typed REST endpoints (health, telemetry, alerts, invs, settings)
│   │   ├── core/                 # Config, settings, and SQLite database engine
│   │   ├── models/               # SQLAlchemy ORM models (Telemetry, Alert, Inv, Evidence, etc.)
│   │   ├── schemas/              # Pydantic v2 validation contracts (including LLM schemas)
│   │   ├── services/
│   │   │   ├── agentic/          # Compiled LangGraph StateGraph & sufficiency loop
│   │   │   ├── detection/        # Rule-based engine + Scikit-learn Isolation Forest
│   │   │   ├── evidence/         # Forensic SVG graph builder & correlation
│   │   │   ├── ingestion/        # CSV/JSON normalization & DB partition pipeline
│   │   │   ├── llm/              # Dual Gemini & OpenAI client + deterministic fallback
│   │   │   ├── mitre/            # Grounded MITRE ATT&CK catalog & evaluator
│   │   │   ├── reporting/        # ReportLab PDF report generation
│   │   │   └── response/         # Human-in-the-loop simulated containment service
│   │   └── main.py               # Application entrypoint & static mount
│   └── tests/                    # Automated pytest & verification test suites
├── datasets/
│   ├── demo/                     # 4 Realistic synthetic multi-stage cyberattack scenarios
│   └── schemas/                  # JSON schema definitions for telemetry validation
└── docs/                         # Research paper, architecture, and guides
```

---

## ⚡ Quick Start & Startup Instructions (Windows PowerShell)

### 1. Prerequisites
- Python 3.11+
- Node.js v18+ & npm

### 2. Environment Configuration
Edit `backend/.env`:
```env
LLM_PROVIDER="gemini"
LLM_FALLBACK_PROVIDER="openai"

GEMINI_API_KEY="your-gemini-key"
GEMINI_MODEL="gemini-flash-lite-latest"

OPENAI_API_KEY="your-openai-key"
OPENAI_MODEL="gpt-4o-mini"

LLM_LIVE_REASONING=true
LLM_ALLOW_DETERMINISTIC_FALLBACK=true
```

### 3. Backend Startup
```powershell
cd C:\Users\ilike\.gemini\antigravity\scratch\CyberSleuth_Fresh\CyberSleuth\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 4. Frontend Startup
```powershell
cd C:\Users\ilike\.gemini\antigravity\scratch\CyberSleuth_Fresh\CyberSleuth\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

> **Unified Production Mode:** Navigating to `http://127.0.0.1:8000/` serves the complete React SPA directly from FastAPI!

### 5. Automated Verification Suite
To verify the entire dual LLM pipeline, run the dedicated test harness:
```powershell
cd C:\Users\ilike\.gemini\antigravity\scratch\CyberSleuth_Fresh\CyberSleuth\backend
.\.venv\Scripts\python.exe tests\verify_dual_llm.py
```

---

## 🧪 Interactive Demo Scenarios

CyberSleuth includes four pre-packaged multi-stage scenarios:
1. **Scenario 1: Credential Compromise & Brute Force:** Brute force logon bursts followed by interactive login and privilege reconnaissance.
2. **Scenario 2: Malicious PowerShell Download Cradle:** Office macro execution spawning encoded LOLBin PowerShell commands.
3. **Scenario 3: Command & Control (C2) Beaconing:** Outbound periodic TCP sockets to untrusted external IP addresses.
4. **Scenario 4: DNS Tunneling & Covert Exfiltration:** High-entropy serialized subdomain queries exfiltrating data over port 53.

---

## 📜 License
Academic Research Project. Developed from scratch for autonomous cybersecurity investigation research.
