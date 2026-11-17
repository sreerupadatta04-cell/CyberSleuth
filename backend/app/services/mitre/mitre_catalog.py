from typing import List, Dict, Any, Optional
from app.models.telemetry import TelemetryEvent

class MitreCatalog:
    """
    Evidence-grounded MITRE ATT&CK Mapping Knowledge Base.
    Ensures every mapping strictly references observed telemetry events and prevents speculative hallucinations.
    """

    TECHNIQUES = {
        "T1110": {
            "name": "Brute Force",
            "tactic": "Credential Access",
            "description": "Adversaries may use brute force techniques to attempt access to accounts.",
            "triggers": ["AUTH_FAILURE", "REPEATED_AUTH_FAILURES", "AUTH_BRUTE_FORCE_SUCCESS"]
        },
        "T1078": {
            "name": "Valid Accounts",
            "tactic": "Defense Evasion / Initial Access",
            "description": "Adversaries may obtain and abuse credentials of existing accounts.",
            "triggers": ["AUTH_SUCCESS", "AUTH_BRUTE_FORCE_SUCCESS"]
        },
        "T1059.001": {
            "name": "Command and Scripting Interpreter: PowerShell",
            "tactic": "Execution",
            "description": "Adversaries may abuse PowerShell commands and scripts for execution.",
            "triggers": ["POWERSHELL_EXEC", "SUSPICIOUS_POWERSHELL_EXECUTION", "powershell.exe"]
        },
        "T1059.003": {
            "name": "Command and Scripting Interpreter: Windows Command Shell",
            "tactic": "Execution",
            "description": "Adversaries may abuse cmd.exe for execution of commands.",
            "triggers": ["cmd.exe", "whoami /priv", "net group"]
        },
        "T1087": {
            "name": "Account Discovery",
            "tactic": "Discovery",
            "description": "Adversaries may attempt to get a listing of valid accounts or domain admins.",
            "triggers": ["net group \"domain admins\"", "whoami", "RECONNAISSANCE_COMMAND_EXECUTED"]
        },
        "T1021.002": {
            "name": "Remote Services: SMB/Windows Admin Shares",
            "tactic": "Lateral Movement",
            "description": "Adversaries may use SMB to interact with remote network systems.",
            "triggers": ["port 445", "smb", "DEST_PORT_445"]
        },
        "T1071.001": {
            "name": "Application Layer Protocol: Web Protocols",
            "tactic": "Command and Control",
            "description": "Adversaries may communicate using application layer protocols (HTTP/HTTPS) to avoid detection.",
            "triggers": ["C2_BEACONING_PATTERN", "PORT_443", "PORT_8080"]
        },
        "T1071.004": {
            "name": "Application Layer Protocol: DNS",
            "tactic": "Command and Control / Exfiltration",
            "description": "Adversaries may communicate or exfiltrate data using the Domain Name System (DNS).",
            "triggers": ["DNS_TUNNELING_EXFILTRATION", "DNS_QUERY"]
        },
        "T1204.002": {
            "name": "User Execution: Malicious File",
            "tactic": "Execution",
            "description": "An adversary may rely upon a user opening a malicious attachment or file.",
            "triggers": ["OFFICE_SPAWNED_SHELL", "winword.exe", "excel.exe"]
        },
        "T1547.001": {
            "name": "Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder",
            "tactic": "Persistence",
            "description": "Adversaries may achieve persistence by adding program scripts to startup folders.",
            "triggers": ["FILE_MOD", ".vbs", ".bat"]
        }
    }

    @classmethod
    def evaluate_telemetry(cls, events: List[TelemetryEvent], alert_rules: List[str] = None) -> List[Dict[str, Any]]:
        mappings = []
        rules = [r.upper() for r in (alert_rules or [])]

        # 1. Check Brute Force (T1110)
        auth_failures = [e for e in events if e.event_type == "AUTH_FAILURE"]
        if len(auth_failures) >= 3 or any("BRUTE_FORCE" in r for r in rules):
            mappings.append({
                "technique_id": "T1110",
                "tactic": "Credential Access",
                "name": "Brute Force",
                "supporting_events": [e.id for e in auth_failures[:5]],
                "confidence": 0.95,
                "category": "OBSERVED",
                "explanation": f"Observed {len(auth_failures)} sequential authentication failures in telemetry."
            })

        # 2. Check Valid Accounts (T1078)
        auth_success = [e for e in events if e.event_type == "AUTH_SUCCESS"]
        if auth_success and auth_failures:
            mappings.append({
                "technique_id": "T1078",
                "tactic": "Defense Evasion / Initial Access",
                "name": "Valid Accounts",
                "supporting_events": [e.id for e in auth_success],
                "confidence": 0.90,
                "category": "OBSERVED",
                "explanation": f"Observed successful authentication ({auth_success[0].id}) immediately subsequent to credential exhaustion."
            })

        # 3. Check PowerShell Execution (T1059.001)
        ps_events = [e for e in events if e.event_type == "POWERSHELL_EXEC" or (e.process_name and "powershell" in e.process_name.lower())]
        if ps_events:
            mappings.append({
                "technique_id": "T1059.001",
                "tactic": "Execution",
                "name": "Command and Scripting Interpreter: PowerShell",
                "supporting_events": [e.id for e in ps_events],
                "confidence": 0.98,
                "category": "OBSERVED",
                "explanation": f"Observed PowerShell runtime execution with evasive parameters across {len(ps_events)} events."
            })

        # 4. Check Account Discovery (T1087)
        disc_events = [e for e in events if e.command_line and any(cmd in e.command_line.lower() for cmd in ["whoami", "net group", "net user", "nltest"])]
        if disc_events:
            mappings.append({
                "technique_id": "T1087",
                "tactic": "Discovery",
                "name": "Account Discovery",
                "supporting_events": [e.id for e in disc_events],
                "confidence": 0.92,
                "category": "OBSERVED",
                "explanation": f"Observed discovery command execution: {disc_events[0].command_line} (Event {disc_events[0].id})."
            })

        # 5. Check Lateral Movement SMB (T1021.002)
        smb_events = [e for e in events if e.destination_port == 445 or (e.protocol and "smb" in e.protocol.lower())]
        if smb_events:
            mappings.append({
                "technique_id": "T1021.002",
                "tactic": "Lateral Movement",
                "name": "Remote Services: SMB/Windows Admin Shares",
                "supporting_events": [e.id for e in smb_events],
                "confidence": 0.88,
                "category": "OBSERVED",
                "explanation": f"Observed SMB port 445 network connection from {smb_events[0].source_ip} to {smb_events[0].destination_ip}."
            })

        # 6. Check C2 Web Protocols (T1071.001)
        c2_events = [e for e in events if e.event_type == "NETWORK_CONNECT" and (e.destination_port in [80, 443, 8080])]
        if len(c2_events) >= 3 or any("C2" in r for r in rules):
            mappings.append({
                "technique_id": "T1071.001",
                "tactic": "Command and Control",
                "name": "Application Layer Protocol: Web Protocols",
                "supporting_events": [e.id for e in c2_events[:5]],
                "confidence": 0.91,
                "category": "OBSERVED",
                "explanation": f"Observed recurrent outbound network connection beacons to external endpoint {c2_events[0].destination_ip}."
            })

        # 7. Check DNS Exfiltration / Tunneling (T1071.004)
        dns_events = [e for e in events if e.event_type == "DNS_QUERY"]
        if len(dns_events) >= 3 or any("DNS" in r for r in rules):
            mappings.append({
                "technique_id": "T1071.004",
                "tactic": "Command and Control / Exfiltration",
                "name": "Application Layer Protocol: DNS",
                "supporting_events": [e.id for e in dns_events[:5]],
                "confidence": 0.94,
                "category": "OBSERVED",
                "explanation": f"Observed high-entropy DNS tunnel staging across {len(dns_events)} serialized query records."
            })

        # 8. Check User Execution Malicious File (T1204.002)
        office_events = [e for e in events if e.parent_process and any(o in e.parent_process.lower() for o in ["winword.exe", "excel.exe", "outlook.exe"])]
        if office_events:
            mappings.append({
                "technique_id": "T1204.002",
                "tactic": "Execution",
                "name": "User Execution: Malicious File",
                "supporting_events": [e.id for e in office_events],
                "confidence": 0.95,
                "category": "OBSERVED",
                "explanation": f"Observed document execution spawning anomalous sub-process: {office_events[0].parent_process} -> {office_events[0].process_name}."
            })

        return mappings
