import csv
import json
import io
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.telemetry import TelemetryEvent
from app.schemas.telemetry import IngestionResult

class TelemetryService:
    @staticmethod
    def parse_and_ingest(
        content: str,
        filename: str,
        db: Session,
        is_demo: bool = False,
        dataset_source: str = "upload"
    ) -> IngestionResult:
        records: List[Dict[str, Any]] = []
        errors: List[str] = []
        
        filename_lower = filename.lower()
        if filename_lower.endswith(".json"):
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    records = [data]
                else:
                    errors.append("JSON root must be an object or a list of objects.")
            except Exception as e:
                errors.append(f"Failed to parse JSON file: {str(e)}")
        elif filename_lower.endswith(".csv"):
            try:
                f = io.StringIO(content)
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(dict(row))
            except Exception as e:
                errors.append(f"Failed to parse CSV file: {str(e)}")
        else:
            errors.append("Unsupported file format. Please upload JSON or CSV.")

        if errors:
            return IngestionResult(
                total_received=len(records),
                valid_count=0,
                invalid_count=len(records),
                errors=errors,
                is_demo=is_demo
            )

        valid_events = []
        invalid_count = 0

        for idx, row in enumerate(records):
            norm_event, err = TelemetryService._normalize_record(row, idx, is_demo, dataset_source)
            if err:
                errors.append(f"Row {idx+1}: {err}")
                invalid_count += 1
            else:
                valid_events.append(norm_event)

        if valid_events:
            for event in valid_events:
                db.merge(event)
            db.commit()

        return IngestionResult(
            total_received=len(records),
            valid_count=len(valid_events),
            invalid_count=invalid_count,
            errors=errors[:10], # Truncate error display
            is_demo=is_demo
        )

    @staticmethod
    def _normalize_record(row: Dict[str, Any], idx: int, is_demo: bool, source: str) -> Tuple[TelemetryEvent, str]:
        event_type = row.get("event_type") or row.get("type") or row.get("EventType")
        if not event_type:
            return None, "Missing event_type"
        
        event_type = str(event_type).strip().upper()
        
        # Timestamp parsing
        raw_ts = row.get("timestamp") or row.get("time") or row.get("Timestamp")
        timestamp = datetime.utcnow()
        if raw_ts:
            if isinstance(raw_ts, str):
                try:
                    timestamp = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                except Exception:
                    try:
                        timestamp = datetime.strptime(raw_ts, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass
            elif isinstance(raw_ts, (int, float)):
                try:
                    timestamp = datetime.utcfromtimestamp(raw_ts)
                except Exception:
                    pass

        event_id = str(row.get("event_id") or row.get("id") or f"EVT-{uuid.uuid4().hex[:8].upper()}")
        
        # Severity normalization
        severity = str(row.get("severity") or "INFO").upper()
        if severity not in ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            severity = "INFO"

        # Safe port parsing
        src_port = None
        dst_port = None
        try:
            if row.get("source_port"):
                src_port = int(row.get("source_port"))
            if row.get("destination_port"):
                dst_port = int(row.get("destination_port"))
        except (ValueError, TypeError):
            pass

        # Demo flag precedence
        record_is_demo = is_demo or bool(row.get("is_demo", False))

        event = TelemetryEvent(
            id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            severity=severity,
            user=str(row.get("user")).strip() if row.get("user") else None,
            host=str(row.get("host")).strip() if row.get("host") else None,
            source_ip=str(row.get("source_ip")).strip() if row.get("source_ip") else None,
            destination_ip=str(row.get("destination_ip")).strip() if row.get("destination_ip") else None,
            source_port=src_port,
            destination_port=dst_port,
            protocol=str(row.get("protocol")).strip() if row.get("protocol") else None,
            process_name=str(row.get("process_name")).strip() if row.get("process_name") else None,
            process_path=str(row.get("process_path")).strip() if row.get("process_path") else None,
            parent_process=str(row.get("parent_process")).strip() if row.get("parent_process") else None,
            command_line=str(row.get("command_line")).strip() if row.get("command_line") else None,
            domain=str(row.get("domain")).strip() if row.get("domain") else None,
            hash=str(row.get("hash")).strip() if row.get("hash") else None,
            raw_payload=row,
            is_demo=record_is_demo,
            dataset_source=source
        )
        return event, None
