import math
import uuid
from typing import List, Dict, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.telemetry import TelemetryEvent
from app.models.alert import Alert

class RuleDetectionEngine:
    @staticmethod
    def calculate_entropy(s: str) -> float:
        if not s:
            return 0.0
        prob = [float(s.count(c)) / len(s) for c in dict.fromkeys(list(s))]
        return - sum([p * math.log(p) / math.log(2.0) for p in prob])

    @staticmethod
    def run_detection(db: Session, is_demo: bool = False) -> List[Alert]:
        alerts_generated: List[Alert] = []
        
        # Query events filtered strictly by DEMO / LIVE partition
        events: List[TelemetryEvent] = db.query(TelemetryEvent).filter(
            TelemetryEvent.is_demo == is_demo
        ).order_by(TelemetryEvent.timestamp.asc()).all()

        if not events:
            return []

        # 1. Rule: Repeated Failed Logins & Suspicious Success After Failure
        user_failures = defaultdict(list)
        for ev in events:
            if ev.event_type == "AUTH_FAILURE" and ev.user:
                user_failures[ev.user].append(ev)
            elif ev.event_type == "AUTH_SUCCESS" and ev.user in user_failures and len(user_failures[ev.user]) >= 3:
                # Suspicious successful login after brute-force/multiple failures
                fail_count = len(user_failures[ev.user])
                alert_id = f"ALT-RULE-{uuid.uuid4().hex[:6].upper()}"
                alert = Alert(
                    id=alert_id,
                    title=f"Suspicious Successful Authentication After Brute Force ({ev.user})",
                    description=(
                        f"User '{ev.user}' authenticated successfully on host '{ev.host or 'Unknown'}' "
                        f"immediately following {fail_count} failed login attempts from source IP {ev.source_ip or 'Unknown'}."
                    ),
                    detection_method="RULE_BASED",
                    rule_name="AUTH_BRUTE_FORCE_SUCCESS",
                    severity="HIGH",
                    status="NEW",
                    primary_event_id=ev.id,
                    affected_entities=[
                        {"type": "user", "value": ev.user},
                        {"type": "host", "value": ev.host or "Unknown"},
                        {"type": "ip", "value": ev.source_ip or "Unknown"}
                    ],
                    explanation=(
                        f"Pattern indicates probable credential compromise or brute force exhaustion. "
                        f"First failed at {user_failures[ev.user][0].timestamp.isoformat()}, success at {ev.timestamp.isoformat()}."
                    ),
                    is_demo=is_demo
                )
                alerts_generated.append(alert)
                user_failures[ev.user] = [] # Reset to avoid duplicate alert

        for user, fails in user_failures.items():
            if len(fails) >= 3:
                first_ev = fails[0]
                last_ev = fails[-1]
                alert_id = f"ALT-RULE-{uuid.uuid4().hex[:6].upper()}"
                alert = Alert(
                    id=alert_id,
                    title=f"Repeated Failed Logins Detected ({user})",
                    description=f"{len(fails)} consecutive authentication failures recorded for account '{user}'.",
                    detection_method="RULE_BASED",
                    rule_name="REPEATED_AUTH_FAILURES",
                    severity="MEDIUM" if len(fails) < 5 else "HIGH",
                    status="NEW",
                    primary_event_id=last_ev.id,
                    affected_entities=[
                        {"type": "user", "value": user},
                        {"type": "host", "value": last_ev.host or "Unknown"},
                        {"type": "ip", "value": last_ev.source_ip or "Unknown"}
                    ],
                    explanation=f"Authentication anomaly: {len(fails)} failures between {first_ev.timestamp.isoformat()} and {last_ev.timestamp.isoformat()}.",
                    is_demo=is_demo
                )
                alerts_generated.append(alert)

        # 2. Rule: Suspicious PowerShell Execution
        for ev in events:
            cmd = (ev.command_line or "").lower()
            pname = (ev.process_name or "").lower()
            if "powershell" in pname or ev.event_type == "POWERSHELL_EXEC" or "powershell" in cmd:
                suspicious_tokens = ["-enc", "-encodedcommand", "downloadstring", "bypass", "hidden", "iex", "webclient"]
                matched_tokens = [tok for tok in suspicious_tokens if tok in cmd]
                if len(matched_tokens) >= 2 or "bypass" in cmd or "-enc" in cmd:
                    alert_id = f"ALT-RULE-{uuid.uuid4().hex[:6].upper()}"
                    alert = Alert(
                        id=alert_id,
                        title=f"Suspicious Obfuscated PowerShell Execution ({ev.host or 'Host'})",
                        description=f"PowerShell executed with evasive parameters: {', '.join(matched_tokens)} on host '{ev.host}'.",
                        detection_method="RULE_BASED",
                        rule_name="SUSPICIOUS_POWERSHELL_EXECUTION",
                        severity="CRITICAL",
                        status="NEW",
                        primary_event_id=ev.id,
                        affected_entities=[
                            {"type": "host", "value": ev.host or "Unknown"},
                            {"type": "user", "value": ev.user or "Unknown"},
                            {"type": "process", "value": ev.process_name or "powershell.exe"}
                        ],
                        explanation=f"Command line contained evasion flags: '{ev.command_line}'. Parent process: '{ev.parent_process}'.",
                        is_demo=is_demo
                    )
                    alerts_generated.append(alert)

        # 3. Rule: Unusual Process Creation & Reconnaissance Commands
        recon_commands = ["whoami /priv", "net group", "domain admins", "nltest", "vssadmin", "mimikatz"]
        office_parents = ["winword.exe", "excel.exe", "outlook.exe", "powerpnt.exe"]
        for ev in events:
            if ev.event_type in ["PROCESS_CREATE", "POWERSHELL_EXEC"]:
                cmd = (ev.command_line or "").lower()
                parent = (ev.parent_process or "").lower()
                pname = (ev.process_name or "").lower()
                
                # Office spawning shell
                if any(op in parent for op in office_parents) and any(sh in pname for sh in ["cmd.exe", "powershell.exe", "wscript.exe", "cscript.exe"]):
                    alert_id = f"ALT-RULE-{uuid.uuid4().hex[:6].upper()}"
                    alert = Alert(
                        id=alert_id,
                        title=f"Suspicious Process Spawned by Office Application ({parent} -> {pname})",
                        description=f"Office application '{ev.parent_process}' spawned execution interpreter '{ev.process_name}'.",
                        detection_method="RULE_BASED",
                        rule_name="OFFICE_SPAWNED_SHELL",
                        severity="CRITICAL",
                        status="NEW",
                        primary_event_id=ev.id,
                        affected_entities=[
                            {"type": "host", "value": ev.host or "Unknown"},
                            {"type": "user", "value": ev.user or "Unknown"},
                            {"type": "process", "value": ev.process_name}
                        ],
                        explanation=f"Parent process {ev.parent_process} launched child process {ev.process_name} with command: {ev.command_line}",
                        is_demo=is_demo
                    )
                    alerts_generated.append(alert)

                # Reconnaissance / privilege enumeration
                for rcmd in recon_commands:
                    if rcmd in cmd:
                        alert_id = f"ALT-RULE-{uuid.uuid4().hex[:6].upper()}"
                        alert = Alert(
                            id=alert_id,
                            title=f"Host Reconnaissance Command Executed ({rcmd})",
                            description=f"Administrative discovery command '{rcmd}' was executed on '{ev.host}'.",
                            detection_method="RULE_BASED",
                            rule_name="RECONNAISSANCE_COMMAND_EXECUTED",
                            severity="HIGH",
                            status="NEW",
                            primary_event_id=ev.id,
                            affected_entities=[
                                {"type": "host", "value": ev.host or "Unknown"},
                                {"type": "user", "value": ev.user or "Unknown"},
                                {"type": "process", "value": ev.process_name or "cmd.exe"}
                            ],
                            explanation=f"Potential post-exploitation discovery: '{ev.command_line}'",
                            is_demo=is_demo
                        )
                        alerts_generated.append(alert)
                        break

        # 4. Rule: Suspicious Outbound Connection & C2 Beaconing
        dest_ip_connections = defaultdict(list)
        for ev in events:
            if ev.event_type == "NETWORK_CONNECT" and ev.destination_ip:
                dest_ip_connections[(ev.host, ev.destination_ip)].append(ev)

        for (host, dst_ip), conns in dest_ip_connections.items():
            if len(conns) >= 4 and not dst_ip.startswith("10.") and not dst_ip.startswith("192.168."):
                last_conn = conns[-1]
                alert_id = f"ALT-RULE-{uuid.uuid4().hex[:6].upper()}"
                alert = Alert(
                    id=alert_id,
                    title=f"Potential Command & Control Beaconing ({dst_ip})",
                    description=f"{len(conns)} repeated periodic outbound connections observed from host '{host}' to external IP '{dst_ip}'.",
                    detection_method="RULE_BASED",
                    rule_name="C2_BEACONING_PATTERN",
                    severity="CRITICAL",
                    status="NEW",
                    primary_event_id=last_conn.id,
                    affected_entities=[
                        {"type": "host", "value": host or "Unknown"},
                        {"type": "ip", "value": dst_ip},
                        {"type": "process", "value": last_conn.process_name or "network"}
                    ],
                    explanation=(
                        f"Host '{host}' initiated {len(conns)} recurring network connections to destination IP {dst_ip} "
                        f"on port {last_conn.destination_port or 443}."
                    ),
                    is_demo=is_demo
                )
                alerts_generated.append(alert)

        # 5. Rule: Unusual DNS Tunneling / High-Entropy Subdomains
        dns_apex_queries = defaultdict(list)
        for ev in events:
            if ev.event_type == "DNS_QUERY" and ev.domain:
                dom = ev.domain.lower()
                entropy = RuleDetectionEngine.calculate_entropy(dom)
                # Split domain
                parts = dom.split(".")
                apex = ".".join(parts[-2:]) if len(parts) >= 2 else dom
                dns_apex_queries[apex].append((ev, entropy, len(dom)))

        for apex, queries in dns_apex_queries.items():
            high_entropy_count = sum(1 for q in queries if q[1] > 3.4 or q[2] > 35)
            if high_entropy_count >= 3:
                last_q_ev = queries[-1][0]
                alert_id = f"ALT-RULE-{uuid.uuid4().hex[:6].upper()}"
                alert = Alert(
                    id=alert_id,
                    title=f"DNS Tunneling / Data Exfiltration Anomaly ({apex})",
                    description=f"Multiple high-entropy, long-string DNS queries targeted to '{apex}' from host '{last_q_ev.host}'.",
                    detection_method="RULE_BASED",
                    rule_name="DNS_TUNNELING_EXFILTRATION",
                    severity="CRITICAL",
                    status="NEW",
                    primary_event_id=last_q_ev.id,
                    affected_entities=[
                        {"type": "host", "value": last_q_ev.host or "Unknown"},
                        {"type": "domain", "value": apex},
                        {"type": "ip", "value": last_q_ev.source_ip or "Unknown"}
                    ],
                    explanation=(
                        f"Detected {high_entropy_count} queries to {apex} with Shannon entropy > 3.4 or subdomain lengths > 35 characters. "
                        f"Sample domain: {last_q_ev.domain}"
                    ),
                    is_demo=is_demo
                )
                alerts_generated.append(alert)

        # Deduplicate and persist
        persisted_alerts = []
        for alt in alerts_generated:
            # Check if identical alert already exists to prevent duplication on re-run
            existing = db.query(Alert).filter(
                Alert.title == alt.title,
                Alert.is_demo == is_demo,
                Alert.primary_event_id == alt.primary_event_id
            ).first()
            if not existing:
                db.add(alt)
                persisted_alerts.append(alt)
            else:
                persisted_alerts.append(existing)

        db.commit()
        return persisted_alerts
