# CyberSleuth: Technical Architecture

## 1. System Topology & Dual Live LLM Orchestration

CyberSleuth is an evidence-driven, stateful multi-agent investigation system running natively on Windows 10/11. It integrates official Google Gemini (`google-genai`) and OpenAI (`openai`) SDKs directly into a compiled LangGraph `StateGraph`.

```
                        +--------------------------------+
                        |      Unified Web Interface     |
                        |   React 18 + TS + Tailwind     |
                        +--------------------------------+
                                       |
                   HTTP REST APIs      | (Port 8000 / Port 5173 Proxy)
                                       v
                        +--------------------------------+
                        |        FastAPI Backend         |
                        | (app/main.py, Windows Py 3.11) |
                        +--------------------------------+
                         /             |                \
                        v              v                 v
            +----------------+ +---------------+ +---------------+
            | Hybrid Engine  | | SQLite Database| | Response Engine|
            | (Rules + ML)   | | cybersleuth.db| | (HITL Staged) |
            +----------------+ +---------------+ +---------------+
                                       |
                                       v
                        +--------------------------------+
                        |   LangGraph Stateful Engine    |
                        |     (StateGraph Pipeline)      |
                        +--------------------------------+
                                       |
                                       v
                        +--------------------------------+
                        |    LLMService Router & Shim    |
                        | (Windows-Guarded Dual Provider)|
                        +--------------------------------+
                                  /            \
                                 v              v
                     +----------------+    +----------------+
                     | Google Gemini  |    |     OpenAI     |
                     | (Official SDK) |    | (Official SDK) |
                     +----------------+    +----------------+
```

## 2. LangGraph 9-Stage Stateful Investigation Pipeline

Each security alert processed by CyberSleuth passes through a stateful directed acyclic graph (with conditional sufficiency loop):

1. **Alert Intake (`alert_intake`)**: Parses target entities (host, IP, process, user account) and normalizes severity.
2. **Investigation Planning (`investigation_planning`)**: Generates initial forensic hypotheses (H1, H2) for testing.
3. **Evidence Collection (`evidence_collection`)**: Queries partitioned SQLite database for events temporally correlated with target entities.
4. **Correlation & Validation (`correlation_and_validation`)**: Calls `LLMService.reason_investigation()`. Live Gemini/OpenAI synthesizes structured evidentiary findings, categorizing each as `OBSERVED` or `INFERRED` with concrete event provenance (`EVT-...`).
5. **Sufficiency Loop (`evidence_sufficiency_assessment`)**: Evaluates whether forensic depth is satisfied. If incomplete, loops back to expand entity collection.
6. **Attack Reconstruction (`attack_reconstruction`)**: Reconstructs attack narrative, event timeline, and blast radius.
7. **MITRE ATT&CK Mapping (`mitre_mapping`)**: Correlates observed behaviors against grounded MITRE ATT&CK techniques (e.g. `T1071.001`, `T1110`).
8. **Risk Assessment (`risk_assessment`)**: Computes quantitative impact and blast radius scores.
9. **Response Staging & Closure (`response_and_closure`)**: Generates simulated containment recommendations (e.g., isolate host, block IP, terminate process) requiring explicit Human-in-the-Loop authorization.

## 3. Windows-First Resilience & Security Controls

- **No Compiler Prerequisite**: Pure Python 3.11 standard packages; no MSVC or Rust compilers required.
- **AppLocker Guard**: In-memory compatibility shim prevents native DLL loading blocks on secured Windows environments.
- **Failover Governance**: Unrecoverable errors (invalid keys, 401, quota 429) do not silently failover. Recoverable transient errors failover to secondary provider or engage the deterministic forensic model with explicit `degraded_mode = True` provenance.
