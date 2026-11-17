from typing import Dict, Any, List, Set
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.alert import Alert
from app.models.telemetry import TelemetryEvent
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceGraphResponse, GraphNode, GraphEdge

class EvidenceGraphService:
    @staticmethod
    def get_investigation_graph(investigation_id: str, db: Session) -> EvidenceGraphResponse:
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            return EvidenceGraphResponse(investigation_id=investigation_id, nodes=[], edges=[], stats={})

        alert = db.query(Alert).filter(Alert.id == inv.alert_id).first()
        evidence_items = db.query(Evidence).filter(Evidence.investigation_id == investigation_id).all()
        
        # Query related telemetry events
        events: List[TelemetryEvent] = db.query(TelemetryEvent).filter(
            TelemetryEvent.is_demo == inv.is_demo
        ).all()

        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        node_ids: Set[str] = set()

        def add_node(n_id: str, label: str, n_type: str, cat: str = "OBSERVED", details: Dict[str, Any] = None):
            if n_id not in node_ids and n_id:
                nodes.append(GraphNode(
                    id=n_id,
                    label=label,
                    node_type=n_type,
                    category=cat,
                    details=details or {}
                ))
                node_ids.add(n_id)

        edge_keys: Set[str] = set()
        def add_edge(src: str, dst: str, rel_type: str, cat: str = "OBSERVED", conf: float = 1.0, evt_ref: str = None):
            key = f"{src}->{dst}:{rel_type}"
            if key not in edge_keys and src in node_ids and dst in node_ids:
                edges.append(GraphEdge(
                    id=f"EDGE-{len(edges)+1:03d}",
                    source=src,
                    target=dst,
                    relationship_type=rel_type,
                    relationship_category=cat,
                    confidence=conf,
                    supporting_event_id=evt_ref
                ))
                edge_keys.add(key)

        # 1. Add Investigation Node
        inv_node_id = f"node-{inv.id}"
        add_node(inv_node_id, inv.id, "investigation", "OBSERVED", {
            "status": inv.status,
            "progress": inv.progress,
            "stage": inv.current_stage
        })

        # 2. Add Alert Node
        if alert:
            alert_node_id = f"node-{alert.id}"
            add_node(alert_node_id, alert.title[:25] + "...", "alert", "OBSERVED", {
                "severity": alert.severity,
                "rule": alert.rule_name,
                "method": alert.detection_method,
                "score": alert.anomaly_score
            })
            add_edge(inv_node_id, alert_node_id, "INVESTIGATES", "OBSERVED", 1.0)

        # 3. Add Entity and Event Nodes
        for ev in events:
            # We filter events that match the affected entities or are cited in findings
            is_relevant = False
            if alert and alert.primary_event_id == ev.id:
                is_relevant = True
            
            # Check if event is cited in any finding
            for fnd in (inv.findings or []):
                if ev.id in fnd.get("supporting_events", []):
                    is_relevant = True
                    break

            # If not explicitly cited, check if user/host matches target
            if not is_relevant and alert and alert.affected_entities:
                for ent in alert.affected_entities:
                    if (ent.get("value") in [ev.user, ev.host, ev.source_ip, ev.destination_ip, ev.domain]):
                        is_relevant = True
                        break

            if not is_relevant:
                continue

            ev_node_id = f"evt-{ev.id}"
            add_node(ev_node_id, ev.id, "event", "OBSERVED", {
                "type": ev.event_type,
                "timestamp": ev.timestamp.isoformat(),
                "severity": ev.severity,
                "command": ev.command_line
            })

            if alert:
                add_edge(f"node-{alert.id}", ev_node_id, "TRIGGERED_BY", "OBSERVED", 1.0, ev.id)

            # Entity: User
            if ev.user:
                usr_id = f"user-{ev.user}"
                add_node(usr_id, ev.user, "user", "OBSERVED", {"account": ev.user})
                add_edge(ev_node_id, usr_id, "AUTHENTICATED_AS" if "AUTH" in ev.event_type else "EXECUTED_BY", "OBSERVED", 1.0, ev.id)

            # Entity: Host
            if ev.host:
                host_id = f"host-{ev.host}"
                add_node(host_id, ev.host, "host", "OBSERVED", {"hostname": ev.host})
                add_edge(ev_node_id, host_id, "OCCURRED_ON", "OBSERVED", 1.0, ev.id)

            # Entity: Source IP
            if ev.source_ip:
                ip_src_id = f"ip-{ev.source_ip}"
                add_node(ip_src_id, ev.source_ip, "ip", "OBSERVED", {"address": ev.source_ip})
                add_edge(ip_src_id, ev_node_id, "SOURCED_FROM", "OBSERVED", 1.0, ev.id)

            # Entity: Destination IP
            if ev.destination_ip:
                ip_dst_id = f"ip-{ev.destination_ip}"
                add_node(ip_dst_id, ev.destination_ip, "ip", "OBSERVED", {"address": ev.destination_ip})
                add_edge(ev_node_id, ip_dst_id, "CONNECTED_TO", "OBSERVED", 1.0, ev.id)

            # Entity: Process
            if ev.process_name:
                proc_id = f"proc-{ev.process_name}"
                add_node(proc_id, ev.process_name, "process", "OBSERVED", {
                    "path": ev.process_path,
                    "parent": ev.parent_process
                })
                add_edge(ev_node_id, proc_id, "SPAWNED", "OBSERVED", 1.0, ev.id)

            # Entity: Domain
            if ev.domain:
                dom_id = f"dom-{ev.domain[:20]}"
                add_node(dom_id, ev.domain[:25], "domain", "OBSERVED", {"domain": ev.domain})
                add_edge(ev_node_id, dom_id, "RESOLVED", "OBSERVED", 1.0, ev.id)

        # 4. Inferred Relationships from Findings
        for idx, fnd in enumerate(inv.findings or []):
            if fnd.get("status") == "INFERRED":
                # Link related entities with an INFERRED relationship
                supp_evts = fnd.get("supporting_events", [])
                if len(supp_evts) >= 2:
                    src_evt = f"evt-{supp_evts[0]}"
                    dst_evt = f"evt-{supp_evts[1]}"
                    add_edge(src_evt, dst_evt, "CORRELATED_WITH", "INFERRED", fnd.get("confidence", 0.85))

        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "observed_count": sum(1 for e in edges if e.relationship_category == "OBSERVED"),
            "inferred_count": sum(1 for e in edges if e.relationship_category == "INFERRED")
        }

        return EvidenceGraphResponse(
            investigation_id=investigation_id,
            nodes=nodes,
            edges=edges,
            stats=stats
        )
