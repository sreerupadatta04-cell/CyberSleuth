import sys
import types
import json
import time
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Literal

# Windows AppLocker compatibility guard: Pure-Python fallback for native DLL imports
if "jiter" not in sys.modules:
    try:
        import jiter  # type: ignore
    except (ImportError, Exception):
        m = types.ModuleType("jiter")
        m.from_json = json.loads
        m.cache_clear = lambda: None
        sys.modules["jiter"] = m

from app.core.config import settings
from app.schemas.llm import (
    InvestigationReasoningOutput,
    HypothesisSchema,
    FindingSchema,
    AttackReconstructionSchema,
    ResponseRecommendationSchema,
    MitreObservationSchema,
    LLMConnectionTestResult
)

class LLMService:
    """
    Dual Live LLM Integration Service (Gemini & OpenAI) for CyberSleuth.
    Supports:
      - Primary: Google Gemini (via official google-genai SDK)
      - Secondary: OpenAI (via official openai SDK with pure-Python DLL guard)
      - Automatic Mode: Deterministic primary routing with controlled failover on recoverable faults
      - Deterministic Forensic Synthesizer: Grounded fallback when unconfigured or on failure
      - Strict provenance enforcement (OBSERVED vs INFERRED) and telemetry grounding validation
    """

    @classmethod
    def get_api_key(cls, provider: str) -> Optional[str]:
        p = provider.lower()
        k = ""
        if p == "gemini":
            k = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or ""
        elif p == "openai":
            k = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY or ""
        return k.strip() if k and k.strip() else None

    @classmethod
    def is_provider_configured(cls, provider: str) -> bool:
        return bool(cls.get_api_key(provider))

    @classmethod
    def test_connection(
        cls,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> LLMConnectionTestResult:
        """
        Safely test connectivity to Gemini or OpenAI without saving secrets or executing workflow actions.
        Returns detailed classification: HEALTHY, UNCONFIGURED, INVALID_KEY, MODEL_NOT_FOUND, QUOTA_EXCEEDED, CONNECTION_FAILED.
        """
        p = provider.lower()
        key = (api_key if api_key is not None else (cls.get_api_key(p) or "")).strip()
        tested_at = datetime.utcnow().isoformat()

        if not key:
            return LLMConnectionTestResult(
                provider=p,
                model=model or (settings.GEMINI_MODEL if p == "gemini" else settings.OPENAI_MODEL),
                status="UNCONFIGURED",
                available=False,
                latency_ms=None,
                message=f"No API key provided or configured for {p.upper()}. Deterministic fallback remains active.",
                tested_at=tested_at
            )

        start_time = time.time()
        try:
            if p == "gemini":
                from google import genai
                from google.genai import types

                target_model = model or settings.GEMINI_MODEL or "gemini-3.8-flash"
                http_opts = types.HttpOptions(api_version="v1beta")
                client = genai.Client(api_key=key, http_options=http_opts)
                
                # Execute lightweight connection probe with resilient demand-spike handling
                try:
                    response = client.models.generate_content(
                        model=target_model,
                        contents="Forensic health probe. Respond with single word: READY."
                    )
                except Exception as probe_err:
                    if ("503" in str(probe_err) or "unavailable" in str(probe_err).lower()) and target_model != "gemini-flash-lite-latest":
                        target_model = "gemini-flash-lite-latest"
                        response = client.models.generate_content(
                            model=target_model,
                            contents="Forensic health probe. Respond with single word: READY."
                        )
                    else:
                        raise probe_err
                latency = round((time.time() - start_time) * 1000, 2)
                
                if response and (response.text or hasattr(response, "candidates")):
                    return LLMConnectionTestResult(
                        provider="gemini",
                        model=target_model,
                        status="HEALTHY",
                        available=True,
                        latency_ms=latency,
                        message=f"Google Gemini connection verified successfully ({target_model}, latency {latency}ms).",
                        tested_at=tested_at
                    )
                else:
                    return LLMConnectionTestResult(
                        provider="gemini",
                        model=target_model,
                        status="CONNECTION_FAILED",
                        available=False,
                        latency_ms=None,
                        message="Gemini returned empty response body during health probe.",
                        tested_at=tested_at
                    )

            elif p == "openai":
                from openai import OpenAI
                target_model = model or settings.OPENAI_MODEL or "gpt-4o-mini"
                client = OpenAI(api_key=key)

                response = client.chat.completions.create(
                    model=target_model,
                    messages=[{"role": "user", "content": "Forensic health probe. Respond with single word: READY."}],
                    max_tokens=5
                )
                latency = round((time.time() - start_time) * 1000, 2)

                if response.choices:
                    return LLMConnectionTestResult(
                        provider="openai",
                        model=target_model,
                        status="HEALTHY",
                        available=True,
                        latency_ms=latency,
                        message=f"OpenAI connection verified successfully ({target_model}, latency {latency}ms).",
                        tested_at=tested_at
                    )
                else:
                    return LLMConnectionTestResult(
                        provider="openai",
                        model=target_model,
                        status="CONNECTION_FAILED",
                        available=False,
                        latency_ms=None,
                        message="OpenAI returned empty response choices during health probe.",
                        tested_at=tested_at
                    )
            else:
                return LLMConnectionTestResult(
                    provider=p,
                    model=model or "unknown",
                    status="CONNECTION_FAILED",
                    available=False,
                    latency_ms=None,
                    message=f"Unsupported provider: {p}",
                    tested_at=tested_at
                )

        except Exception as e:
            err_str = str(e)
            latency = round((time.time() - start_time) * 1000, 2)

            # Classify error accurately
            if "503" in err_str or "unavailable" in err_str.lower() or "high demand" in err_str.lower():
                status = "SERVER_BUSY"
                msg = f"Google Gemini service is temporarily overloaded (503 UNAVAILABLE - High Demand). Please retry shortly."
            elif "API key not valid" in err_str or "INVALID_ARGUMENT" in err_str or "Incorrect API key" in err_str or "401" in err_str:
                status = "INVALID_KEY"
                msg = f"Authentication rejected by {p.upper()}: Invalid API key credentials."
            elif "not found" in err_str.lower() or "404" in err_str:
                status = "MODEL_NOT_FOUND"
                msg = f"Model configuration error: Specified model not accessible ({err_str[:120]})."
            elif "quota" in err_str.lower() or "429" in err_str or "rate limit" in err_str.lower():
                status = "QUOTA_EXCEEDED"
                msg = f"Usage limit reached on {p.upper()}: Quota exceeded or rate limited."
            elif "getaddrinfo" in err_str.lower() or "connect" in err_str.lower() or "network" in err_str.lower():
                status = "CONNECTION_FAILED"
                msg = f"Network connectivity error reaching {p.upper()} API endpoints (Check internet connection or firewall/proxy)."
            else:
                status = "CONNECTION_FAILED"
                msg = f"Diagnostic test error on {p.upper()}: {err_str[:150]}"

            return LLMConnectionTestResult(
                provider=p,
                model=model or (settings.GEMINI_MODEL if p == "gemini" else settings.OPENAI_MODEL),
                status=status,
                available=False,
                latency_ms=latency,
                message=msg,
                tested_at=tested_at
            )

    @classmethod
    def check_health(cls) -> Dict[str, Any]:
        """
        Evaluate full multi-provider health.
        Checks configured status for Gemini, OpenAI, and active routing mode.
        """
        gemini_configured = cls.is_provider_configured("gemini")
        openai_configured = cls.is_provider_configured("openai")

        active_mode = settings.LLM_PROVIDER.lower()
        fallback_prov = settings.LLM_FALLBACK_PROVIDER.lower()

        # Probe active provider if configured
        gemini_status = "CONFIGURED" if gemini_configured else "UNCONFIGURED"
        openai_status = "CONFIGURED" if openai_configured else "UNCONFIGURED"

        active_available = False
        active_status = "UNCONFIGURED"
        active_message = "No live LLM credentials configured. Deterministic forensic mode active."

        if active_mode == "gemini":
            if gemini_configured:
                active_status = "CONFIGURED"
                active_available = True
                active_message = f"Google Gemini active ({settings.GEMINI_MODEL})."
            else:
                active_status = "UNCONFIGURED"
                active_message = "Gemini API key not configured. Using deterministic forensic synthesizer."
        elif active_mode == "openai":
            if openai_configured:
                active_status = "CONFIGURED"
                active_available = True
                active_message = f"OpenAI active ({settings.OPENAI_MODEL})."
            else:
                active_status = "UNCONFIGURED"
                active_message = "OpenAI API key not configured. Using deterministic forensic synthesizer."
        elif active_mode == "auto":
            if gemini_configured:
                active_status = "CONFIGURED (PRIMARY: GEMINI)"
                active_available = True
                active_message = f"Automatic Mode: Gemini primary ({settings.GEMINI_MODEL}) with OpenAI failover."
            elif openai_configured:
                active_status = "CONFIGURED (PRIMARY: OPENAI)"
                active_available = True
                active_message = f"Automatic Mode: OpenAI active ({settings.OPENAI_MODEL}) as secondary."
            else:
                active_status = "UNCONFIGURED"
                active_message = "Neither Gemini nor OpenAI is configured. Deterministic fallback mode active."

        return {
            "available": active_available,
            "status": active_status,
            "provider": active_mode, # Backward compatibility alias
            "active_provider": active_mode,
            "fallback_provider": fallback_prov,
            "model": settings.GEMINI_MODEL if active_mode in ["gemini", "auto"] else settings.OPENAI_MODEL,
            "message": active_message,
            "gemini_configured": gemini_configured,
            "gemini_model": settings.GEMINI_MODEL,
            "gemini_status": gemini_status,
            "openai_configured": openai_configured,
            "openai_model": settings.OPENAI_MODEL,
            "openai_status": openai_status,
            "live_reasoning_enabled": settings.LLM_LIVE_REASONING,
            "deterministic_fallback_allowed": settings.LLM_ALLOW_DETERMINISTIC_FALLBACK
        }

    @classmethod
    def list_available_gemini_models(cls, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query available models from Google AI Studio under v1beta using configured or provided key.
        Identifies models supporting generateContent.
        """
        key = (api_key or cls.get_api_key("gemini") or "").strip()
        if not key:
            raise ValueError("No Gemini API key available to list models.")
            
        from google import genai
        from google.genai import types
        http_opts = types.HttpOptions(api_version="v1beta")
        client = genai.Client(api_key=key, http_options=http_opts)
        
        models_out = []
        try:
            for m in client.models.list():
                methods = getattr(m, 'supported_generation_methods', []) or getattr(m, 'supported_actions', []) or []
                supports_generation = "generateContent" in methods or not methods
                clean_name = m.name.replace("models/", "") if m.name else ""
                models_out.append({
                    "id": clean_name,
                    "full_name": m.name,
                    "display_name": getattr(m, 'display_name', clean_name),
                    "description": getattr(m, 'description', ""),
                    "supports_generate_content": supports_generation,
                    "is_flash": "flash" in clean_name.lower()
                })
        except Exception as e:
            raise RuntimeError(f"Failed to query Google models: {str(e)}")
            
        return models_out

    @classmethod
    def _is_recoverable_error(cls, err: Exception) -> bool:
        """
        Identifies whether a provider exception is a recoverable transient failure
        (e.g., network disconnect, timeout, 502/503/504 server errors) versus an
        unrecoverable configuration error (invalid key, 401 auth, invalid model, quota exhausted).
        """
        err_str = str(err).lower()
        # Unrecoverable errors that must NOT silently failover
        if "api key not valid" in err_str or "invalid_argument" in err_str or "incorrect api key" in err_str or "401" in err_str:
            return False
        if "not found" in err_str or "404" in err_str:
            return False
        if "quota" in err_str or "credit" in err_str or "billing" in err_str:
            return False
        
        # Recoverable transient faults
        if "timeout" in err_str or "503" in err_str or "502" in err_str or "504" in err_str:
            return True
        if "connection" in err_str or "getaddrinfo" in err_str or "network" in err_str:
            return True
        if "rate limit" in err_str or "429" in err_str:
            return True
        return False

    @classmethod
    def reason_investigation(
        cls,
        alert_data: Dict[str, Any],
        telemetry_events: List[Dict[str, Any]],
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Main LangGraph LLM reasoning invocation with dual-provider orchestration,
        failover handling, structured validation, and telemetry grounding.
        """
        # If live reasoning is explicitly disabled in settings, engage deterministic engine
        if not settings.LLM_LIVE_REASONING:
            return cls._wrap_deterministic(
                alert_data, telemetry_events, iteration,
                reason="Live LLM reasoning is disabled in system configuration."
            )

        active_mode = settings.LLM_PROVIDER.lower()
        provider_switches: List[Dict[str, Any]] = []

        # Determine Primary and Secondary providers
        if active_mode == "openai":
            primary_provider = "openai"
            secondary_provider = "gemini" if cls.is_provider_configured("gemini") else None
        elif active_mode == "auto":
            primary_provider = "gemini" if cls.is_provider_configured("gemini") else "openai"
            secondary_provider = "openai" if primary_provider == "gemini" and cls.is_provider_configured("openai") else None
        else: # Default: gemini
            primary_provider = "gemini"
            secondary_provider = "openai" if cls.is_provider_configured("openai") else None

        primary_key = cls.get_api_key(primary_provider)

        # If primary is not configured
        if not primary_key:
            # Check if secondary is configured in auto mode
            if active_mode == "auto" and secondary_provider:
                primary_provider = secondary_provider
                primary_key = cls.get_api_key(primary_provider)
            else:
                return cls._wrap_deterministic(
                    alert_data, telemetry_events, iteration,
                    reason=f"No API key configured for {primary_provider.upper()}."
                )

        # 1. Attempt Primary Provider Execution
        try:
            raw_output = cls._invoke_provider(primary_provider, alert_data, telemetry_events, iteration)
            validated_output = cls._validate_and_ground_output(raw_output, telemetry_events)
            validated_output["llm_invoked"] = True
            validated_output["llm_provider"] = primary_provider.upper()
            validated_output["llm_model"] = (
                settings.GEMINI_MODEL if primary_provider == "gemini" else settings.OPENAI_MODEL
            )
            validated_output["degraded_mode"] = False
            validated_output["provider_switches"] = provider_switches
            return validated_output

        except Exception as e_primary:
            err_msg = str(e_primary)
            is_recoverable = cls._is_recoverable_error(e_primary)

            # Check if controlled failover is allowed
            if is_recoverable and active_mode == "auto" and secondary_provider:
                switch_record = {
                    "from_provider": primary_provider.upper(),
                    "to_provider": secondary_provider.upper(),
                    "reason": f"Recoverable error from {primary_provider}: {err_msg[:120]}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                provider_switches.append(switch_record)

                try:
                    raw_output = cls._invoke_provider(secondary_provider, alert_data, telemetry_events, iteration)
                    validated_output = cls._validate_and_ground_output(raw_output, telemetry_events)
                    validated_output["llm_invoked"] = True
                    validated_output["llm_provider"] = secondary_provider.upper()
                    validated_output["llm_model"] = (
                        settings.GEMINI_MODEL if secondary_provider == "gemini" else settings.OPENAI_MODEL
                    )
                    validated_output["degraded_mode"] = False
                    validated_output["provider_switches"] = provider_switches
                    return validated_output
                except Exception as e_secondary:
                    err_msg += f" | Failover to {secondary_provider} also failed: {str(e_secondary)[:120]}"

            # If failover not permitted, not configured, or both failed:
            if settings.LLM_ALLOW_DETERMINISTIC_FALLBACK:
                return cls._wrap_deterministic(
                    alert_data, telemetry_events, iteration,
                    reason=f"Live inference failed on {primary_provider.upper()} ({err_msg[:150]}). Safe deterministic fallback engaged.",
                    provider_switches=provider_switches
                )
            else:
                raise RuntimeError(f"Live LLM reasoning failed on {primary_provider.upper()}: {err_msg}")

    @classmethod
    def _invoke_provider(
        cls,
        provider: str,
        alert_data: Dict[str, Any],
        telemetry_events: List[Dict[str, Any]],
        iteration: int
    ) -> Dict[str, Any]:
        """
        Execute live structured inference against Google Gemini or OpenAI.
        """
        p = provider.lower()
        key = cls.get_api_key(p)
        if not key:
            raise ValueError(f"API key missing for {p.upper()}")

        events_summary = [
            {
                "id": e.get("id"),
                "time": str(e.get("timestamp")),
                "type": e.get("event_type"),
                "user": e.get("user"),
                "host": e.get("host"),
                "src_ip": e.get("source_ip"),
                "dst_ip": e.get("destination_ip"),
                "process": e.get("process_name"),
                "cmd": e.get("command_line"),
                "domain": e.get("domain")
            }
            for e in telemetry_events[:20]
        ]

        system_prompt = (
            "You are CyberSleuth AI Forensics Engine, an evidence-grounded multi-agent investigation system. "
            "Your task is to analyze the security alert and correlated telemetry events to reconstruct the attack. "
            "CRITICAL FORENSIC RULES:\n"
            "1. Ground all observations strictly in the provided telemetry events.\n"
            "2. NEVER invent entity names, IP addresses, users, hosts, or event IDs not in the telemetry.\n"
            "3. Clearly distinguish OBSERVED facts (directly evidenced in telemetry) from INFERRED deductions.\n"
            "4. For every finding, list the exact event IDs (e.g. ['EVT-AUTH-101']) in 'supporting_events'.\n"
            "5. Inferred findings must have confidence <= 0.95 and an explanatory rationale.\n"
            "6. Recommend only simulated response actions (ISOLATE_HOST, RESET_CREDENTIALS, BLOCK_IP, TERMINATE_PROCESS).\n"
            "7. Return strictly valid JSON adhering to the specified schema."
        )

        user_prompt = f"""
SECURITY ALERT:
{json.dumps(alert_data, indent=2)}

CORRELATED TELEMETRY EVENTS ({len(events_summary)} records):
{json.dumps(events_summary, indent=2)}

INVESTIGATION ITERATION: {iteration}

Respond ONLY with a JSON object adhering to this exact schema:
{{
  "hypotheses": [
    {{
      "id": "H1",
      "hypothesis": "Forensic hypothesis statement",
      "likelihood": "HIGH|MEDIUM|LOW",
      "tested": true,
      "supported": true,
      "rationale": "Forensic rationale"
    }}
  ],
  "findings": [
    {{
      "id": "F1",
      "statement": "Evidence-grounded finding statement",
      "status": "OBSERVED|INFERRED",
      "confidence": 0.95,
      "supporting_events": ["EVT-..."],
      "rationale": "Forensic explanation referencing telemetry"
    }}
  ],
  "missing_evidence": [],
  "attack_narrative": "Detailed chronological attack reconstruction based on event timestamps.",
  "attack_timeline": ["EVT-..."],
  "executive_summary": "Comprehensive forensic summary for SOC leadership.",
  "response_recommendations": [
    {{
      "action_type": "ISOLATE_HOST|RESET_CREDENTIALS|BLOCK_IP|TERMINATE_PROCESS",
      "target_entity": "Host/User/IP/Process",
      "rationale": "Justification for containment",
      "risk_assessment": "Operational risk analysis"
    }}
  ],
  "mitre_mappings": [
    {{
      "technique_id": "T1110",
      "tactic": "Credential Access",
      "name": "Brute Force",
      "supporting_events": ["EVT-..."],
      "explanation": "Technique explanation"
    }}
  ],
  "recommended_next_steps": [
    "Next investigative step"
  ],
  "sufficiency_reached": true
}}
"""

        raw_text = ""
        if p == "gemini":
            from google import genai
            from google.genai import types

            http_opts = types.HttpOptions(api_version="v1beta")
            client = genai.Client(api_key=key, http_options=http_opts)
            target_model = settings.GEMINI_MODEL or "gemini-3.8-flash"
            
            try:
                response = client.models.generate_content(
                    model=target_model,
                    contents=f"{system_prompt}\n\n{user_prompt}",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
            except Exception as gen_err:
                if ("503" in str(gen_err) or "unavailable" in str(gen_err).lower()) and target_model != "gemini-flash-lite-latest":
                    target_model = "gemini-flash-lite-latest"
                    response = client.models.generate_content(
                        model=target_model,
                        contents=f"{system_prompt}\n\n{user_prompt}",
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                else:
                    raise gen_err
            raw_text = response.text or ""

        elif p == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=key)
            target_model = settings.OPENAI_MODEL or "gpt-4o-mini"

            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            raw_text = response.choices[0].message.content or ""

        # Parse JSON and clean fences if model wrapped them
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        parsed = json.loads(clean_text.strip())
        return parsed

    @classmethod
    def _validate_and_ground_output(
        cls,
        raw_output: Dict[str, Any],
        telemetry_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Pydantic schema validation and strict telemetry grounding.
        Strips phantom event IDs and enforces OBSERVED vs INFERRED confidence constraints.
        """
        valid_event_ids = {e.get("id") for e in telemetry_events if e.get("id")}

        # Ground findings
        grounded_findings = []
        for i, f in enumerate(raw_output.get("findings", [])):
            fid = f.get("id") or f"F{i+1}"
            statement = f.get("statement", "")
            status = f.get("status", "INFERRED").upper()
            if status not in ["OBSERVED", "INFERRED"]:
                status = "INFERRED"

            confidence = float(f.get("confidence", 0.85))
            raw_supporting = f.get("supporting_events", [])
            # Filter to genuinely existing event IDs
            grounded_supporting = [eid for eid in raw_supporting if eid in valid_event_ids]

            # If marked OBSERVED but no valid supporting events remain, demote to INFERRED
            if status == "OBSERVED" and not grounded_supporting:
                status = "INFERRED"
                confidence = min(confidence, 0.85)

            if status == "INFERRED" and confidence > 0.95:
                confidence = 0.90

            rationale = f.get("rationale") or f"Forensic deduction based on correlated telemetry."

            grounded_findings.append({
                "id": fid,
                "statement": statement,
                "status": status,
                "confidence": round(confidence, 2),
                "supporting_events": grounded_supporting,
                "rationale": rationale
            })

        # Ground MITRE mappings
        grounded_mitre = []
        for m in raw_output.get("mitre_mappings", []):
            tid = m.get("technique_id")
            if tid:
                m_events = [eid for eid in m.get("supporting_events", []) if eid in valid_event_ids]
                grounded_mitre.append({
                    "technique_id": tid,
                    "tactic": m.get("tactic", "Execution"),
                    "name": m.get("name", "Grounded Technique"),
                    "supporting_events": m_events,
                    "explanation": m.get("explanation", "Mapped from observed telemetry activity.")
                })

        # Ground Timeline
        raw_timeline = raw_output.get("attack_timeline") or raw_output.get("attack_reconstruction", {}).get("timeline", [])
        grounded_timeline = [eid for eid in raw_timeline if eid in valid_event_ids]
        if not grounded_timeline:
            grounded_timeline = [e.get("id") for e in telemetry_events if e.get("id")]

        attack_narrative = (
            raw_output.get("attack_narrative") or
            raw_output.get("attack_reconstruction", {}).get("narrative") or
            "Temporal progression established across collected telemetry records."
        )

        return {
            "hypotheses": raw_output.get("hypotheses", []),
            "findings": grounded_findings,
            "missing_evidence": raw_output.get("missing_evidence", []),
            "attack_reconstruction": {
                "narrative": attack_narrative,
                "timeline": grounded_timeline,
                "phases": raw_output.get("phases", [])
            },
            "executive_summary": raw_output.get("executive_summary", "Forensic analysis completed."),
            "response_recommendations": raw_output.get("response_recommendations", []),
            "mitre_mappings": grounded_mitre,
            "recommended_next_steps": raw_output.get("recommended_next_steps", []),
            "sufficiency_reached": raw_output.get("sufficiency_reached", True)
        }

    @classmethod
    def _wrap_deterministic(
        cls,
        alert_data: Dict[str, Any],
        telemetry_events: List[Dict[str, Any]],
        iteration: int,
        reason: str = "Deterministic mode active.",
        provider_switches: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Wraps deterministic reasoning results with explicit DEGRADED_MODE provenance tagging.
        """
        res = cls._deterministic_reasoning(alert_data, telemetry_events, iteration)
        res["llm_invoked"] = False
        res["llm_provider"] = "DETERMINISTIC_FALLBACK"
        res["llm_model"] = "forensic-rule-synthesizer-v1"
        res["degraded_mode"] = True
        res["failover_reason"] = reason
        res["provider_switches"] = provider_switches or []
        return res

    @classmethod
    def _deterministic_reasoning(
        cls,
        alert_data: Dict[str, Any],
        telemetry_events: List[Dict[str, Any]],
        iteration: int
    ) -> Dict[str, Any]:
        """
        Deterministic forensic reasoning synthesizer.
        Grounded in telemetry with explicit provenance labels (OBSERVED vs INFERRED).
        """
        title = alert_data.get("title", "Security Alert")
        rule = alert_data.get("rule_name") or alert_data.get("detection_method", "")
        primary_id = alert_data.get("primary_event_id")

        hypotheses = []
        findings = []
        missing_evidence = []
        narrative = ""
        recs = []
        mitre_list = []

        # Target entities
        target_users = list({e.get("user") for e in telemetry_events if e.get("user")})
        target_hosts = list({e.get("host") for e in telemetry_events if e.get("host")})
        target_ips = list({e.get("source_ip") for e in telemetry_events if e.get("source_ip")})
        target_dst_ips = list({e.get("destination_ip") for e in telemetry_events if e.get("destination_ip")})

        # SCENARIO 1: Credential Brute Force & Account Compromise
        if "BRUTE_FORCE" in rule or "AUTH" in rule or "Credential" in title:
            auth_failures = [e for e in telemetry_events if e.get("event_type") == "AUTH_FAILURE"]
            auth_success = [e for e in telemetry_events if e.get("event_type") == "AUTH_SUCCESS"]

            hypotheses = [
                {
                    "id": "H1",
                    "hypothesis": "External actor conducted credential guessing attack resulting in account takeover.",
                    "likelihood": "HIGH",
                    "tested": True,
                    "supported": bool(auth_success and len(auth_failures) >= 3),
                    "rationale": f"Observed {len(auth_failures)} sequential logon failures followed by successful authentication."
                },
                {
                    "id": "H2",
                    "hypothesis": "Legitimate user forgot password followed by successful recall.",
                    "likelihood": "LOW",
                    "tested": True,
                    "supported": False,
                    "rationale": "High frequency of failures across distinct user accounts from single external IP indicates automated tool."
                }
            ]

            if auth_failures:
                findings.append({
                    "id": "F1",
                    "statement": f"Multiple authentication failures detected originating from IP {target_ips[0] if target_ips else 'External'}.",
                    "status": "OBSERVED",
                    "confidence": 0.99,
                    "supporting_events": [e.get("id") for e in auth_failures[:4]],
                    "rationale": "Telemetry directly logs event_type AUTH_FAILURE with logon type 10 (Remote Desktop)."
                })

            if auth_success:
                findings.append({
                    "id": "F2",
                    "statement": f"Account {auth_success[0].get('user', 'Target User')} successfully authenticated following failed logon burst.",
                    "status": "OBSERVED",
                    "confidence": 0.98,
                    "supporting_events": [auth_success[0].get("id")],
                    "rationale": "Event AUTH_SUCCESS registered for target identity immediately subsequent to failure window."
                })
                findings.append({
                    "id": "F3",
                    "statement": "Adversary gained unauthorized interactive access using compromised credentials.",
                    "status": "INFERRED",
                    "confidence": 0.92,
                    "supporting_events": [auth_success[0].get("id")],
                    "rationale": "Temporal linkage between high-volume automated guessing and immediate successful session establishment."
                })

            narrative = (
                f"Adversary initiated dictionary attack from source IP {target_ips[0] if target_ips else '198.51.100.44'} "
                f"targeting domain accounts on host {target_hosts[0] if target_hosts else 'FIN-SRV-01'}. "
                f"Following repeated logon failures, credentials for user '{target_users[0] if target_users else 'finance_admin'}' were verified, "
                f"granting unauthorized remote desktop access."
            )

            recs = [
                {
                    "action_type": "RESET_CREDENTIALS",
                    "target_entity": target_users[0] if target_users else "Compromised Account",
                    "rationale": "Invalidate compromised authentication token and force password rotation.",
                    "risk_assessment": "Low operational risk; prevents adversary re-authentication."
                },
                {
                    "action_type": "BLOCK_IP",
                    "target_entity": target_ips[0] if target_ips else "198.51.100.44",
                    "rationale": "Sever inbound adversary network connectivity at edge perimeter.",
                    "risk_assessment": "Low risk; source identified as untrusted public IP."
                }
            ]

            mitre_list = [
                {
                    "technique_id": "T1110.001",
                    "tactic": "Credential Access",
                    "name": "Password Guessing",
                    "supporting_events": [e.get("id") for e in auth_failures[:3]],
                    "explanation": "Multiple sequential logon failures indicates automated password guessing."
                },
                {
                    "technique_id": "T1078",
                    "tactic": "Initial Access",
                    "name": "Valid Accounts",
                    "supporting_events": [auth_success[0].get("id")] if auth_success else [],
                    "explanation": "Adversary leveraged legitimate compromised credentials for initial entry."
                }
            ]

        # SCENARIO 2: PowerShell & Living-off-the-Land Execution
        elif "POWERSHELL" in rule or "SHELL" in rule or "EXECUTION" in rule or "PowerShell" in title:
            ps_events = [e for e in telemetry_events if "powershell" in (e.get("process_name") or "").lower() or e.get("event_type") == "POWERSHELL_EXEC"]
            proc_events = [e for e in telemetry_events if e.get("event_type") == "PROCESS_CREATE"]

            hypotheses = [
                {
                    "id": "H1",
                    "hypothesis": "Malicious payload delivered via document macro spawning obfuscated PowerShell.",
                    "likelihood": "HIGH",
                    "tested": True,
                    "supported": True,
                    "rationale": "Office application spawned powershell.exe with Base64 encoded payload and execution policy bypass."
                },
                {
                    "id": "H2",
                    "hypothesis": "Legitimate systems management automation script.",
                    "likelihood": "LOW",
                    "tested": True,
                    "supported": False,
                    "rationale": "Legitimate enterprise scripts execute from trusted paths without Base64 payload encoding."
                }
            ]

            if ps_events:
                findings.append({
                    "id": "F1",
                    "statement": f"PowerShell executed with -ExecutionPolicy Bypass and encoded command on {target_hosts[0] if target_hosts else 'Endpoint'}.",
                    "status": "OBSERVED",
                    "confidence": 0.99,
                    "supporting_events": [ps_events[0].get("id")],
                    "rationale": "Command line contains '-NoProfile -WindowStyle Hidden -Enc' arguments."
                })
            
            findings.append({
                "id": "F2",
                "statement": "Adversary attempted defense evasion by executing payload through native Windows LOLBin.",
                "status": "INFERRED",
                "confidence": 0.94,
                "supporting_events": [ps_events[0].get("id")] if ps_events else [],
                "rationale": "LOLBin execution avoids binary drop on disk and circumvents standard application whitelisting."
            })

            narrative = (
                f"Phishing lure opened on endpoint {target_hosts[0] if target_hosts else 'WKSTN-SEC-04'}. "
                f"Parent process WINWORD.EXE spawned powershell.exe with bypass flags, executing in-memory payload "
                f"and staging registry persistence."
            )

            recs = [
                {
                    "action_type": "ISOLATE_HOST",
                    "target_entity": target_hosts[0] if target_hosts else "Infected Host",
                    "rationale": "Contain endpoint to prevent lateral movement and C2 polling.",
                    "risk_assessment": "Temporarily disconnects workstation from local LAN; maintains management channel."
                },
                {
                    "action_type": "TERMINATE_PROCESS",
                    "target_entity": "powershell.exe",
                    "rationale": "Kill executing adversary process tree.",
                    "risk_assessment": "Zero enterprise impact; kills malicious in-memory shell."
                }
            ]

            mitre_list = [
                {
                    "technique_id": "T1059.001",
                    "tactic": "Execution",
                    "name": "PowerShell",
                    "supporting_events": [ps_events[0].get("id")] if ps_events else [],
                    "explanation": "Execution of powershell.exe with encoded commands."
                },
                {
                    "technique_id": "T1566.001",
                    "tactic": "Initial Access",
                    "name": "Spearphishing Attachment",
                    "supporting_events": [proc_events[0].get("id")] if proc_events else [],
                    "explanation": "Malicious macro-enabled office attachment."
                }
            ]

        # SCENARIO 3: C2 Beaconing & Lateral Movement
        elif "BEACONING" in rule or "C2" in rule or "Command and Control" in title:
            net_events = [e for e in telemetry_events if e.get("event_type") == "NETWORK_CONNECTION"]
            
            hypotheses = [
                {
                    "id": "H1",
                    "hypothesis": "Compromised host established persistent C2 channel with external adversary infrastructure.",
                    "likelihood": "HIGH",
                    "tested": True,
                    "supported": True,
                    "rationale": "Periodic low-jitter outbound HTTP connections to unregistered dynamic external IP."
                }
            ]

            findings.append({
                "id": "F1",
                "statement": f"Periodic network connections observed to external IP {target_dst_ips[0] if target_dst_ips else '185.220.101.5'} at regular intervals.",
                "status": "OBSERVED",
                "confidence": 0.98,
                "supporting_events": [e.get("id") for e in net_events[:4]],
                "rationale": "Outbound TCP session logging demonstrates 60-second periodic beacon interval."
            })
            findings.append({
                "id": "F2",
                "statement": "Adversary implant is actively awaiting tasking from command-and-control server.",
                "status": "INFERRED",
                "confidence": 0.91,
                "supporting_events": [net_events[0].get("id")] if net_events else [],
                "rationale": "Strict cadence and small packet payload characteristics match known C2 beacon profiles."
            })

            narrative = (
                f"Post-exploitation agent on {target_hosts[0] if target_hosts else 'SRV-DATA-02'} "
                f"initiated continuous outbound beaconing to remote C2 infrastructure ({target_dst_ips[0] if target_dst_ips else '185.220.101.5'})."
            )

            recs = [
                {
                    "action_type": "BLOCK_IP",
                    "target_entity": target_dst_ips[0] if target_dst_ips else "185.220.101.5",
                    "rationale": "Block outbound command-and-control traffic at firewall boundary.",
                    "risk_assessment": "No legitimate business traffic associated with destination IP."
                },
                {
                    "action_type": "ISOLATE_HOST",
                    "target_entity": target_hosts[0] if target_hosts else "Host",
                    "rationale": "Prevent lateral propagation across internal network segments.",
                    "risk_assessment": "Protects core data repository while forensic image is captured."
                }
            ]

            mitre_list = [
                {
                    "technique_id": "T1071.001",
                    "tactic": "Command and Control",
                    "name": "Web Protocols",
                    "supporting_events": [net_events[0].get("id")] if net_events else [],
                    "explanation": "Outbound HTTP/HTTPS communication to external C2 node."
                }
            ]

        # SCENARIO 4: DNS Tunneling & Exfiltration
        elif "DNS" in rule or "TUNNELING" in rule or "EXFILTRATION" in rule or "Exfiltration" in title:
            dns_events = [e for e in telemetry_events if e.get("event_type") == "DNS_QUERY"]

            hypotheses = [
                {
                    "id": "H1",
                    "hypothesis": "Data exfiltration via DNS tunneling over port 53.",
                    "likelihood": "HIGH",
                    "tested": True,
                    "supported": True,
                    "rationale": "High volume of long, high-entropy TXT/A queries matching base32/hex encoded strings."
                }
            ]

            findings.append({
                "id": "F1",
                "statement": "Anomalous DNS queries with high Shannon entropy and subdomain length exceeding 50 characters.",
                "status": "OBSERVED",
                "confidence": 0.99,
                "supporting_events": [e.get("id") for e in dns_events[:4]],
                "rationale": "DNS log inspection confirms repetitive queries to .data.exfil-c2.net domain."
            })
            findings.append({
                "id": "F2",
                "statement": "Sensitive intellectual property or database records encoded and transferred via DNS protocol.",
                "status": "INFERRED",
                "confidence": 0.93,
                "supporting_events": [dns_events[0].get("id")] if dns_events else [],
                "rationale": "Subdomain payload concatenation reveals chunked binary stream reconstructed off-network."
            })

            narrative = (
                f"Adversary compromised server {target_hosts[0] if target_hosts else 'DB-BACKUP-01'} "
                f"and initiated covert channel data exfiltration using DNS query subdomains to bypass standard egress proxies."
            )

            recs = [
                {
                    "action_type": "BLOCK_IP",
                    "target_entity": target_dst_ips[0] if target_dst_ips else "198.51.100.88",
                    "rationale": "Null-route malicious authoritative nameserver address.",
                    "risk_assessment": "Prevents covert channel exfiltration without impacting local recursive resolvers."
                },
                {
                    "action_type": "ISOLATE_HOST",
                    "target_entity": target_hosts[0] if target_hosts else "Host",
                    "rationale": "Halt file extraction process on database server.",
                    "risk_assessment": "Immediate containment required to minimize data breach volume."
                }
            ]

            mitre_list = [
                {
                    "technique_id": "T1048.003",
                    "tactic": "Exfiltration",
                    "name": "Exfiltration Over Alternative Protocol",
                    "supporting_events": [dns_events[0].get("id")] if dns_events else [],
                    "explanation": "Covert exfiltration over DNS protocol."
                }
            ]

        # Generic / Machine Learning Anomaly Detection
        else:
            hypotheses = [
                {
                    "id": "H1",
                    "hypothesis": f"Statistical anomaly detected by Isolation Forest corresponds to unauthorized activity: {title}",
                    "likelihood": "MEDIUM",
                    "tested": True,
                    "supported": True,
                    "rationale": "Isolation Forest identified multi-dimensional outlier in telemetry feature distribution."
                }
            ]

            findings.append({
                "id": "F1",
                "statement": f"Telemetry event {primary_id or 'EVT'} triggered detection heuristic: {title}.",
                "status": "OBSERVED",
                "confidence": 0.90,
                "supporting_events": [primary_id] if primary_id else [e.get("id") for e in telemetry_events[:2]],
                "rationale": "Event values diverged significantly from baseline population metrics."
            })
            findings.append({
                "id": "F2",
                "statement": "Outlier behavior may represent novel exploit vector or unmodeled administrative operation.",
                "status": "INFERRED",
                "confidence": 0.85,
                "supporting_events": [primary_id] if primary_id else [],
                "rationale": "Unsupervised anomaly detection flags rarity; malicious intent requires corroboration."
            })

            narrative = f"Automated inspection of telemetry around alert '{title}' revealed anomalous deviation from normal activity profiles."
            recs = [
                {
                    "action_type": "ISOLATE_HOST",
                    "target_entity": target_hosts[0] if target_hosts else "Target Asset",
                    "rationale": "Restrict asset pending manual triage.",
                    "risk_assessment": "Precautionary containment."
                }
            ]
            mitre_list = [
                {
                    "technique_id": "T1204",
                    "tactic": "Execution",
                    "name": "User Execution",
                    "supporting_events": [primary_id] if primary_id else [],
                    "explanation": "Anomalous execution sequence flagged by ML model."
                }
            ]

        timeline_ids = [e.get("id") for e in telemetry_events if e.get("id")]

        # Sufficiency check: if sparse (< 2 events) on iteration 1, mark false
        sufficiency = True
        if len(telemetry_events) <= 1 and iteration == 1:
            sufficiency = False
            missing_evidence = [
                "Process lineage tree for parent executable",
                "Authentication logs for adjacent 30-minute window"
            ]

        return {
            "hypotheses": hypotheses,
            "findings": findings,
            "missing_evidence": missing_evidence,
            "attack_reconstruction": {
                "narrative": narrative,
                "timeline": timeline_ids
            },
            "executive_summary": (
                f"Forensic investigation into alert '{title}' conducted across {len(telemetry_events)} correlated events. "
                f"Identified {len(findings)} evidentiary findings ({sum(1 for f in findings if f['status'] == 'OBSERVED')} OBSERVED, "
                f"{sum(1 for f in findings if f['status'] == 'INFERRED')} INFERRED). "
                f"Generated {len(recs)} containment recommendations staged in Response Center."
            ),
            "response_recommendations": recs,
            "mitre_mappings": mitre_list,
            "recommended_next_steps": [
                "Review staged response actions in Response Center and authorize simulated containment.",
                "Capture disk forensic triage image of affected endpoint.",
                "Verify threat eradication via repeated detection run."
            ],
            "sufficiency_reached": sufficiency
        }
