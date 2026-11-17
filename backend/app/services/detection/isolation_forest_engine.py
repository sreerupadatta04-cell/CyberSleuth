import math
import uuid
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from app.models.telemetry import TelemetryEvent
from app.models.alert import Alert

class IsolationForestEngine:
    """
    Unsupervised Anomaly Detection using Scikit-learn Isolation Forest.
    Extracts multi-dimensional behavioral features from event telemetry.
    Flags statistical outliers while maintaining the critical forensic distinction:
    'Anomalous behavior is statistically deviant, but not automatically malicious.'
    """

    @staticmethod
    def _extract_features(event: TelemetryEvent) -> List[float]:
        # Feature 1: Event type categorical mapping
        type_map = {
            "AUTH_FAILURE": 1.0,
            "AUTH_SUCCESS": 2.0,
            "PROCESS_CREATE": 3.0,
            "NETWORK_CONNECT": 4.0,
            "DNS_QUERY": 5.0,
            "POWERSHELL_EXEC": 6.0,
            "FILE_MOD": 7.0,
            "PRIVILEGE_ESCALATION": 8.0
        }
        f_type = type_map.get(event.event_type, 0.0)

        # Feature 2: Time of day (hour of day normalized 0-1)
        f_hour = (event.timestamp.hour + event.timestamp.minute / 60.0) / 24.0 if event.timestamp else 0.5

        # Feature 3: Destination port (normalized or 0)
        f_port = (float(event.destination_port) / 65535.0) if event.destination_port else 0.0

        # Feature 4: Command line length
        cmd_len = len(event.command_line or "")
        f_cmd_len = math.log1p(cmd_len)

        # Feature 5: Domain length & entropy (if DNS or network)
        domain = event.domain or ""
        f_dom_len = math.log1p(len(domain))
        if domain:
            prob = [float(domain.count(c)) / len(domain) for c in dict.fromkeys(list(domain))]
            f_entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
        else:
            f_entropy = 0.0

        # Feature 6: Severity weight
        sev_weights = {"INFO": 0.1, "LOW": 0.3, "MEDIUM": 0.6, "HIGH": 0.8, "CRITICAL": 1.0}
        f_sev = sev_weights.get(event.severity, 0.2)

        return [f_type, f_hour, f_port, f_cmd_len, f_dom_len, f_entropy, f_sev]

    @classmethod
    def run_detection(cls, db: Session, is_demo: bool = False, contamination: float = 0.15) -> List[Alert]:
        events: List[TelemetryEvent] = db.query(TelemetryEvent).filter(
            TelemetryEvent.is_demo == is_demo
        ).order_by(TelemetryEvent.timestamp.asc()).all()

        if len(events) < 4:
            return [] # Require minimum sample size for unsupervised forest

        feature_matrix = []
        valid_events = []
        for ev in events:
            features = cls._extract_features(ev)
            feature_matrix.append(features)
            valid_events.append(ev)

        X = np.array(feature_matrix)

        # Initialize Isolation Forest
        # random_state ensures reproducible anomaly scoring
        clf = IsolationForest(
            n_estimators=100,
            contamination=min(contamination, 0.3),
            random_state=42
        )
        clf.fit(X)

        # anomaly score: lower values indicate higher outlierness
        scores = clf.decision_function(X) # typical range [-0.5, 0.5]
        predictions = clf.predict(X) # -1 for anomaly, 1 for inlier

        alerts: List[Alert] = []
        for idx, (ev, score, pred) in enumerate(zip(valid_events, scores, predictions)):
            # When prediction is -1, it is identified as an anomaly
            if pred == -1:
                # Convert raw score to a normalized [0, 1] outlier severity score
                normalized_anomaly_score = float(round(max(0.0, min(1.0, 0.5 - score)), 3))
                
                # Determine severity based on anomaly score
                if normalized_anomaly_score > 0.75:
                    severity = "CRITICAL"
                elif normalized_anomaly_score > 0.6:
                    severity = "HIGH"
                else:
                    severity = "MEDIUM"

                alert_id = f"ALT-IF-{uuid.uuid4().hex[:6].upper()}"
                
                # Contextual description
                desc = (
                    f"Statistical outlier detected by Isolation Forest on event {ev.id} ({ev.event_type}). "
                    f"Anomaly score: {normalized_anomaly_score}."
                )
                
                entities = []
                if ev.user:
                    entities.append({"type": "user", "value": ev.user})
                if ev.host:
                    entities.append({"type": "host", "value": ev.host})
                if ev.source_ip:
                    entities.append({"type": "ip", "value": ev.source_ip})
                if ev.destination_ip:
                    entities.append({"type": "ip", "value": ev.destination_ip})
                if ev.process_name:
                    entities.append({"type": "process", "value": ev.process_name})
                if ev.domain:
                    entities.append({"type": "domain", "value": ev.domain})

                explanation = (
                    f"Scikit-learn Isolation Forest flagged this {ev.event_type} record as statistically deviant "
                    f"based on feature dimensions (port: {ev.destination_port or 'N/A'}, command length: {len(ev.command_line or '')}, "
                    f"entropy: {cls._extract_features(ev)[5]:.2f}). NOTE: Statistically anomalous behaviour is not automatically malicious, "
                    f"and requires multi-agent forensic verification."
                )

                alert = Alert(
                    id=alert_id,
                    title=f"Unsupervised Behavioral Anomaly: {ev.event_type} on {ev.host or ev.user or 'Asset'}",
                    description=desc,
                    detection_method="ISOLATION_FOREST",
                    rule_name=None,
                    anomaly_score=normalized_anomaly_score,
                    severity=severity,
                    status="NEW",
                    primary_event_id=ev.id,
                    affected_entities=entities,
                    explanation=explanation,
                    is_demo=is_demo
                )

                # Avoid duplicate alerts for the same event
                existing = db.query(Alert).filter(
                    Alert.detection_method == "ISOLATION_FOREST",
                    Alert.primary_event_id == ev.id,
                    Alert.is_demo == is_demo
                ).first()
                if not existing:
                    db.add(alert)
                    alerts.append(alert)
                else:
                    alerts.append(existing)

        db.commit()
        return alerts
